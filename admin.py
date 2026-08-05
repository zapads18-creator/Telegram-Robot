from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from config import ADMIN_IDS, COMMISSION_PERCENT, ADMIN_CARD_NUMBER, ADMIN_CARD_OWNER
from handlers.owner import start_add_dacha_flow

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🔧 <b>Admin panel</b>\n\n"
        "/add_dacha — yangi dacha qo'shish (admin nomidan, komissiyasiz)\n"
        "/pending — tasdiqlanmagan bronlar ro'yxati\n"
        "/dachas — barcha faol dachalar"
    )


@router.message(Command("add_dacha"))
async def add_dacha_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    # Admin owner_id=None -> bu dacha uchun komissiya hisoblanmaydi
    await start_add_dacha_flow(message, state, owner_id=None)


@router.message(Command("pending"))
async def pending_bookings(message: Message):
    if not is_admin(message.from_user.id):
        return
    bookings = db.get_pending_bookings()
    if not bookings:
        await message.answer("Tasdiqlanmagan bronlar yo'q. ✅")
        return

    for b in bookings:
        text = (
            f"🆕 Bron #{b['id']}\n"
            f"🏡 {b['dacha_name']}\n"
            f"📅 {b['check_in']} - {b['check_out']}\n"
            f"💰 {b['total_price']:,} so'm\n"
            f"👤 {b['full_name']} (@{b['username'] or 'yo\u2018q'})\n"
            f"📞 {b['phone']}"
        )
        await message.answer(text, reply_markup=kb.admin_decision_kb(b["id"]))


@router.message(Command("dachas"))
async def list_all_dachas(message: Message):
    if not is_admin(message.from_user.id):
        return
    dachas = db.get_active_dachas()
    if not dachas:
        await message.answer("Hozircha dachalar qo'shilmagan.")
        return
    lines = [
        f"#{d['id']} — {d['name']} — {d['region']}, {d['district']} — {d['price_per_night']:,} so'm/kecha"
        for d in dachas
    ]
    await message.answer("\n".join(lines))


@router.callback_query(F.data.startswith("approve_"))
async def approve_booking(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    booking_id = int(callback.data.split("_")[1])
    booking = db.get_booking(booking_id)
    if not booking:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return

    db.update_booking_status(booking_id, "approved")
    await callback.message.edit_text(callback.message.text + "\n\n✅ TASDIQLANDI")
    await callback.answer("Tasdiqlandi")

    try:
        await bot.send_message(
            booking["user_id"],
            f"✅ Sizning bron so'rovingiz (#{booking_id}) tasdiqlandi! Tez orada siz bilan bog'lanishadi.",
        )
    except Exception:
        pass

    # Agar dachaning egasi bo'lsa, komissiya to'lash so'raladi
    dacha = db.get_dacha(booking["dacha_id"])
    if dacha and dacha.get("owner_id"):
        commission_text = (
            f"🎉 <b>Dachangiz bron qilindi!</b>\n\n"
            f"🏡 {dacha['name']}\n"
            f"📅 {booking['check_in']} - {booking['check_out']} ({booking['nights']} kecha)\n"
            f"💰 Umumiy summa: {booking['total_price']:,} so'm\n\n"
            f"📌 Botimizga to'lanishi kerak bo'lgan komissiya ({COMMISSION_PERCENT:g}%): "
            f"<b>{booking['commission_amount']:,} so'm</b>\n\n"
            f"💳 Karta: {ADMIN_CARD_NUMBER}\n"
            f"👤 Egasi: {ADMIN_CARD_OWNER}\n\n"
            "To'lovni amalga oshirgach, pastdagi tugmani bosing."
        )
        try:
            await bot.send_message(
                dacha["owner_id"], commission_text, reply_markup=kb.commission_paid_kb(booking_id)
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("reject_"))
async def reject_booking(callback: CallbackQuery, bot: Bot):
    if not is_admin(callback.from_user.id):
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    booking_id = int(callback.data.split("_")[1])
    booking = db.get_booking(booking_id)
    if not booking:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return

    db.update_booking_status(booking_id, "rejected")
    await callback.message.edit_text(callback.message.text + "\n\n❌ RAD ETILDI")
    await callback.answer("Rad etildi")

    try:
        await bot.send_message(
            booking["user_id"],
            f"❌ Afsuski, sizning bron so'rovingiz (#{booking_id}) rad etildi.",
        )
    except Exception:
        pass
