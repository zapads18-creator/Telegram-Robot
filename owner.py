from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import OwnerContractStates, AddDachaStates
from regions import REGIONS
from config import COMMISSION_PERCENT

router = Router()

CONTRACT_TEXT = (
    "📜 <b>Shartnoma</b>\n\n"
    "Hurmatli dacha egasi!\n\n"
    "Botimiz orqali dachangizni bepul joylashtirishingiz mumkin. Shu bilan birga siz "
    "quyidagi shartlarga rozilik bildirasiz:\n\n"
    f"• Botimiz orqali amalga oshirilgan har bir muvaffaqiyatli (admin tomonidan tasdiqlangan) "
    f"bron uchun umumiy bron summasidan <b>{COMMISSION_PERCENT:g}%</b> miqdorida komissiya "
    f"botimiz administratsiyasiga to'lanadi.\n"
    "• Komissiya bron tasdiqlangandan so'ng hisoblanadi va sizga to'lov ma'lumotlari yuboriladi.\n"
    "• Siz taqdim etgan ma'lumotlar (narx, manzil, aloqa raqami) haqiqiy va to'g'ri bo'lishi kerak.\n"
    "• Shartlarga rozi bo'lmasangiz, dacha joylashtira olmaysiz.\n\n"
    "Ushbu shartlarga roziligingizni bildiring:"
)


# ---------- Contract ----------

@router.callback_query(F.data == "owner_start")
async def owner_start(callback: CallbackQuery, state: FSMContext):
    if db.owner_has_agreed(callback.from_user.id):
        await callback.message.edit_text(
            "🏘 <b>Dacha egasi bo'limi</b>\n\nQuyidagilardan birini tanlang:",
            reply_markup=kb.owner_menu_kb(),
        )
        await callback.answer()
        return

    await callback.message.edit_text(CONTRACT_TEXT, reply_markup=kb.contract_kb())
    await callback.answer()


@router.callback_query(F.data == "owner_disagree")
async def owner_disagree(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "Tushunarli. Shartnomaga rozi bo'lmaguningizcha dacha joylashtira olmaysiz.\n\n"
        "Fikringiz o'zgarsa, \"🏘 Dachamni joylashtirish\" tugmasini istalgan vaqt qayta bosishingiz mumkin.",
        reply_markup=kb.main_menu_kb(),
    )
    await callback.answer()


@router.callback_query(F.data == "owner_agree")
async def owner_agree(callback: CallbackQuery, state: FSMContext):
    await state.set_state(OwnerContractStates.entering_full_name)
    await callback.message.edit_text("✅ Rozilik qabul qilindi.\n\nIsm familiyangizni kiriting:")
    await callback.answer()


@router.message(OwnerContractStates.entering_full_name)
async def owner_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await state.set_state(OwnerContractStates.entering_phone)
    await message.answer("📞 Aloqa uchun telefon raqamingizni kiriting (masalan: +998901234567):")


@router.message(OwnerContractStates.entering_phone)
async def owner_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 9:
        await message.answer("Telefon raqami noto'g'ri ko'rinishda. Qaytadan kiriting:")
        return

    data = await state.get_data()
    db.upsert_owner(message.from_user.id, data["full_name"], phone, agreed=1)
    await state.clear()
    await message.answer(
        "✅ Ro'yxatdan o'tdingiz! Endi dachangizni joylashtirishingiz mumkin.",
        reply_markup=kb.owner_menu_kb(),
    )


# ---------- Owner menu ----------

@router.callback_query(F.data == "owner_my_dachas")
async def owner_my_dachas(callback: CallbackQuery):
    dachas = db.get_dachas_by_owner(callback.from_user.id)
    if not dachas:
        await callback.message.edit_text(
            "Sizda hali joylashtirilgan dachalar yo'q.", reply_markup=kb.owner_menu_kb()
        )
        await callback.answer()
        return

    lines = ["🏠 <b>Sizning dachalaringiz:</b>\n"]
    for d in dachas:
        status = "✅ faol" if d["is_active"] else "⛔️ o'chirilgan"
        lines.append(f"#{d['id']} {d['name']} — {d['region']}, {d['district']} — {status}")
    await callback.message.edit_text("\n".join(lines), reply_markup=kb.owner_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "owner_commissions")
async def owner_commissions(callback: CallbackQuery):
    items = db.get_unpaid_commissions_for_owner(callback.from_user.id)
    if not items:
        await callback.message.edit_text(
            "To'lanmagan komissiyalaringiz yo'q. ✅", reply_markup=kb.owner_menu_kb()
        )
        await callback.answer()
        return

    for b in items:
        text = (
            f"💳 <b>Komissiya to'lovi kerak</b>\n\n"
            f"🏡 Dacha: {b['dacha_name']}\n"
            f"📅 {b['check_in']} - {b['check_out']} ({b['nights']} kecha)\n"
            f"💰 Umumiy bron summasi: {b['total_price']:,} so'm\n"
            f"📌 Komissiya ({COMMISSION_PERCENT:g}%): <b>{b['commission_amount']:,} so'm</b>\n\n"
            "To'lovni admin kartasiga o'tkazing va \"✅ To'ladim\" tugmasini bosing."
        )
        await callback.message.answer(text, reply_markup=kb.commission_paid_kb(b["id"]))
    await callback.answer()


# ---------- Add dacha (shared: owner self-service + admin) ----------

async def start_add_dacha_flow(target, state: FSMContext, owner_id):
    """target can be Message or CallbackQuery"""
    await state.update_data(owner_id=owner_id)
    await state.set_state(AddDachaStates.entering_name)
    text = "🏡 Dacha nomini kiriting:"
    if isinstance(target, CallbackQuery):
        await target.message.answer(text, reply_markup=kb.cancel_kb())
    else:
        await target.answer(text, reply_markup=kb.cancel_kb())


@router.callback_query(F.data == "owner_add_dacha")
async def owner_add_dacha(callback: CallbackQuery, state: FSMContext):
    if not db.owner_has_agreed(callback.from_user.id):
        await callback.message.edit_text(CONTRACT_TEXT, reply_markup=kb.contract_kb())
        await callback.answer()
        return
    await start_add_dacha_flow(callback, state, owner_id=callback.from_user.id)
    await callback.answer()


@router.message(AddDachaStates.entering_name)
async def add_dacha_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AddDachaStates.entering_description)
    await message.answer("📝 Tavsifini kiriting (xonalar soni, qulayliklar va h.k.):")


@router.message(AddDachaStates.entering_description)
async def add_dacha_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AddDachaStates.choosing_region)
    await message.answer("📍 Dacha joylashgan viloyatni tanlang:", reply_markup=kb.regions_kb("adregion_"))


@router.callback_query(AddDachaStates.choosing_region, F.data.startswith("adregion_"))
async def add_dacha_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.removeprefix("adregion_")
    if region not in REGIONS:
        await callback.answer("Noto'g'ri viloyat.", show_alert=True)
        return
    await state.update_data(region=region)
    await state.set_state(AddDachaStates.choosing_district)
    await callback.message.edit_text(
        f"📍 {region} — tumanni tanlang:",
        reply_markup=kb.districts_kb(region, "addistrict_", back_callback="owner_add_dacha"),
    )
    await callback.answer()


@router.callback_query(AddDachaStates.choosing_district, F.data.startswith("addistrict_"))
async def add_dacha_district(callback: CallbackQuery, state: FSMContext):
    district = callback.data.removeprefix("addistrict_")
    await state.update_data(district=district)
    await state.set_state(AddDachaStates.entering_address)
    await callback.message.answer("🏠 Aniq manzilni kiriting (ko'cha, mo'ljal va h.k.):")
    await callback.answer()


@router.message(AddDachaStates.entering_address)
async def add_dacha_address(message: Message, state: FSMContext):
    await state.update_data(address=message.text.strip())
    await state.set_state(AddDachaStates.entering_price)
    await message.answer("💰 Bir kechalik narxini so'mda kiriting (faqat raqam, masalan 500000):")


@router.message(AddDachaStates.entering_price)
async def add_dacha_price(message: Message, state: FSMContext):
    price_text = message.text.strip().replace(" ", "").replace(",", "")
    if not price_text.isdigit():
        await message.answer("Narx faqat raqamlardan iborat bo'lishi kerak. Qaytadan kiriting:")
        return
    await state.update_data(price=int(price_text))
    await state.set_state(AddDachaStates.entering_contact_phone)
    await message.answer("📞 Mehmonlar bog'lanishi uchun telefon raqamini kiriting:")


@router.message(AddDachaStates.entering_contact_phone)
async def add_dacha_contact_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 9:
        await message.answer("Telefon raqami noto'g'ri ko'rinishda. Qaytadan kiriting:")
        return
    await state.update_data(contact_phone=phone)
    await state.set_state(AddDachaStates.entering_photo)
    await message.answer(
        "🖼 Dacha rasmini yuboring (yoki rasmsiz qoldirish uchun tugmani bosing):",
        reply_markup=kb.skip_photo_kb(),
    )


@router.message(AddDachaStates.entering_photo, F.photo)
async def add_dacha_photo(message: Message, state: FSMContext):
    photo_file_id = message.photo[-1].file_id
    await finish_add_dacha(message, state, photo_file_id)


@router.callback_query(AddDachaStates.entering_photo, F.data == "skip_photo")
async def add_dacha_skip_photo(callback: CallbackQuery, state: FSMContext):
    await finish_add_dacha(callback.message, state, None)
    await callback.answer()


async def finish_add_dacha(message: Message, state: FSMContext, photo_file_id):
    data = await state.get_data()
    dacha_id = db.add_dacha(
        owner_id=data.get("owner_id"),
        name=data["name"],
        description=data["description"],
        region=data["region"],
        district=data["district"],
        location=data["address"],
        price_per_night=data["price"],
        contact_phone=data["contact_phone"],
        photo_file_id=photo_file_id,
    )
    await state.clear()
    await message.answer(
        f"✅ \"{data['name']}\" dachasi qo'shildi! (ID: {dacha_id})\n\n"
        f"📍 {data['region']}, {data['district']}",
        reply_markup=kb.owner_menu_kb(),
    )


# ---------- Commission payment confirmation by owner ----------

@router.callback_query(F.data.startswith("owner_paid_"))
async def owner_marks_paid(callback: CallbackQuery, bot):
    from config import ADMIN_IDS

    booking_id = int(callback.data.removeprefix("owner_paid_"))
    booking = db.get_booking(booking_id)
    if not booking:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return

    db.update_commission_status(booking_id, "pending_confirmation")
    await callback.message.edit_text(
        callback.message.text + "\n\n⏳ To'lov admin tomonidan tekshirilmoqda...",
    )
    await callback.answer("Admin tasdiqlashini kuting")

    dacha = db.get_dacha(booking["dacha_id"])
    text = (
        f"💳 <b>Egadan komissiya to'lovi keldi</b>\n\n"
        f"🏡 Dacha: {dacha['name'] if dacha else booking['dacha_id']}\n"
        f"📌 Bron #{booking_id}\n"
        f"💰 Komissiya: {booking['commission_amount']:,} so'm\n"
        f"👤 Egasi: {callback.from_user.full_name} (@{callback.from_user.username or 'yo\u2018q'})\n\n"
        "Tushumni tekshirib, tasdiqlang:"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=kb.admin_commission_confirm_kb(booking_id))
        except Exception:
            pass


@router.callback_query(F.data.startswith("confirm_commission_"))
async def admin_confirm_commission(callback: CallbackQuery, bot):
    from config import ADMIN_IDS

    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    booking_id = int(callback.data.removeprefix("confirm_commission_"))
    booking = db.get_booking(booking_id)
    if not booking:
        await callback.answer("Bron topilmadi.", show_alert=True)
        return

    db.update_commission_status(booking_id, "paid")
    await callback.message.edit_text(callback.message.text + "\n\n✅ TUSHUM TASDIQLANDI")
    await callback.answer("Tasdiqlandi")

    dacha = db.get_dacha(booking["dacha_id"])
    if dacha and dacha.get("owner_id"):
        try:
            await bot.send_message(
                dacha["owner_id"],
                f"✅ Bron #{booking_id} uchun komissiya to'lovingiz tasdiqlandi. Rahmat!",
            )
        except Exception:
            pass
