from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
import keyboards as kb
from states import BookingStates
from regions import REGIONS
from config import ADMIN_IDS, SUPPORT_PHONE, SUPPORT_USERNAME, COMMISSION_PERCENT

router = Router()

DATE_FORMAT = "%d.%m.%Y"


def format_date(date_str: str) -> str:
    return datetime.strptime(date_str, "%Y-%m-%d").strftime(DATE_FORMAT)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! 🏡 <b>Dachalarni bron qilish botiga xush kelibsiz!</b>\n\n"
        "Bu yerda mavjud dachalarni ko'rishingiz, viloyat va tuman bo'yicha qidirishingiz "
        "va istalgan sanaga bron qilishingiz mumkin.",
        reply_markup=kb.main_menu_kb(),
    )


@router.message(Command("help"))
@router.callback_query(F.data == "help")
async def show_help(event, state: FSMContext = None):
    text = (
        "ℹ️ <b>Bot qanday ishlaydi:</b>\n\n"
        "1. \"Dachalar ro'yxati\" bo'limidan viloyat va tumanni tanlang\n"
        "2. Yoqqan dachani tanlab \"Bron qilish\" tugmasini bosing\n"
        "3. Kirish va chiqish sanalarini, telefon raqamingizni kiriting\n"
        "4. So'rovingiz administratorga yuboriladi\n"
        "5. Admin tasdiqlagach, sizga xabar keladi\n\n"
        "Savollar bo'lsa, \"🆘 Qo'llab-quvvatlash\" bo'limiga murojaat qiling."
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb.main_menu_kb())
        await event.answer()
    else:
        await event.answer(text)


@router.callback_query(F.data == "support")
async def show_support(callback: CallbackQuery):
    text = (
        "🆘 <b>Qo'llab-quvvatlash</b>\n\n"
        f"📞 Telefon: {SUPPORT_PHONE}\n"
        f"💬 Telegram: {SUPPORT_USERNAME}\n\n"
        "Savol yoki muammo bo'lsa, biz bilan bemalol bog'laning."
    )
    await callback.message.edit_text(text, reply_markup=kb.main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🏡 <b>Bosh menyu</b>\n\nQuyidagilardan birini tanlang:",
        reply_markup=kb.main_menu_kb(),
    )
    await callback.answer()


# ---------- Browse: region -> district -> dachas ----------

@router.callback_query(F.data == "list_dachas")
async def list_dachas(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📍 <b>Qaysi viloyatdan dacha qidiryapsiz?</b>",
        reply_markup=kb.regions_kb("region_"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("region_"))
async def choose_region(callback: CallbackQuery, state: FSMContext):
    region = callback.data.removeprefix("region_")
    if region not in REGIONS:
        await callback.answer("Noto'g'ri viloyat.", show_alert=True)
        return
    await callback.message.edit_text(
        f"📍 {region} — <b>tumanni tanlang:</b>",
        reply_markup=kb.districts_kb(region, "district_"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("district_"))
async def choose_district(callback: CallbackQuery, state: FSMContext):
    district = callback.data.removeprefix("district_")
    # find which region this district belongs to
    region = None
    for r, districts in REGIONS.items():
        if district in districts:
            region = r
            break
    if not region:
        await callback.answer("Noto'g'ri tuman.", show_alert=True)
        return

    dachas = db.get_dachas_by_district(region, district)
    if not dachas:
        await callback.message.edit_text(
            f"😔 {district} tumanida hozircha dachalar yo'q.\n\nBoshqa tumanni tanlang:",
            reply_markup=kb.districts_kb(region, "district_"),
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        f"🏡 <b>{district} — mavjud dachalar:</b>",
        reply_markup=kb.dachas_list_kb(dachas),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dacha_"))
async def show_dacha(callback: CallbackQuery, state: FSMContext):
    dacha_id = int(callback.data.split("_")[1])
    dacha = db.get_dacha(dacha_id)
    if not dacha:
        await callback.answer("Bu dacha topilmadi.", show_alert=True)
        return

    text = (
        f"🏡 <b>{dacha['name']}</b>\n\n"
        f"📍 {dacha['region']}, {dacha['district']}\n"
        f"🏠 Manzil: {dacha['location'] or 'Ko\'rsatilmagan'}\n"
        f"💰 Narxi: {dacha['price_per_night']:,} so'm / kecha\n"
        f"📞 Aloqa: {dacha['contact_phone'] or 'Ko\'rsatilmagan'}\n\n"
        f"{dacha['description'] or ''}"
    )

    await callback.message.delete()
    if dacha["photo_file_id"]:
        await callback.message.answer_photo(
            photo=dacha["photo_file_id"],
            caption=text,
            reply_markup=kb.dacha_detail_kb(dacha_id),
        )
    else:
        await callback.message.answer(text, reply_markup=kb.dacha_detail_kb(dacha_id))
    await callback.answer()


# ---------- Booking flow ----------

@router.callback_query(F.data.startswith("book_"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    dacha_id = int(callback.data.split("_")[1])
    dacha = db.get_dacha(dacha_id)
    if not dacha:
        await callback.answer("Bu dacha topilmadi.", show_alert=True)
        return

    await state.update_data(dacha_id=dacha_id, dacha_name=dacha["name"], price_per_night=dacha["price_per_night"])
    await state.set_state(BookingStates.entering_check_in)
    await callback.message.answer(
        "📅 Kirish sanasini kiriting (masalan: 15.08.2026):",
        reply_markup=kb.cancel_kb(),
    )
    await callback.answer()


@router.message(BookingStates.entering_check_in)
async def process_check_in(message: Message, state: FSMContext):
    try:
        date = datetime.strptime(message.text.strip(), DATE_FORMAT)
        if date.date() < datetime.now().date():
            await message.answer("O'tmishdagi sana kiritib bo'lmaydi. Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Sana formati noto'g'ri. Namuna: 15.08.2026. Qaytadan kiriting:")
        return

    await state.update_data(check_in=date.strftime("%Y-%m-%d"))
    await state.set_state(BookingStates.entering_check_out)
    await message.answer("📅 Chiqish sanasini kiriting (masalan: 18.08.2026):", reply_markup=kb.cancel_kb())


@router.message(BookingStates.entering_check_out)
async def process_check_out(message: Message, state: FSMContext):
    data = await state.get_data()
    try:
        check_out = datetime.strptime(message.text.strip(), DATE_FORMAT)
        check_in = datetime.strptime(data["check_in"], "%Y-%m-%d")
        if check_out.date() <= check_in.date():
            await message.answer("Chiqish sanasi kirish sanasidan keyin bo'lishi kerak. Qaytadan kiriting:")
            return
    except ValueError:
        await message.answer("Sana formati noto'g'ri. Namuna: 18.08.2026. Qaytadan kiriting:")
        return

    nights = (check_out.date() - check_in.date()).days
    await state.update_data(check_out=check_out.strftime("%Y-%m-%d"), nights=nights)
    await state.set_state(BookingStates.entering_phone)
    await message.answer(
        "📞 Telefon raqamingizni kiriting (masalan: +998901234567):",
        reply_markup=kb.cancel_kb(),
    )


@router.message(BookingStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) < 9:
        await message.answer("Telefon raqami noto'g'ri ko'rinishda. Qaytadan kiriting:")
        return

    await state.update_data(phone=phone)
    data = await state.get_data()
    total_price = data["price_per_night"] * data["nights"]

    summary = (
        "📝 <b>Bron ma'lumotlarini tekshiring:</b>\n\n"
        f"🏡 Dacha: {data['dacha_name']}\n"
        f"📅 Kirish: {format_date(data['check_in'])}\n"
        f"📅 Chiqish: {format_date(data['check_out'])}\n"
        f"🌙 Necha kecha: {data['nights']}\n"
        f"💰 Umumiy narx: {total_price:,} so'm\n"
        f"📞 Telefon: {phone}\n\n"
        "Ma'lumotlar to'g'rimi?"
    )
    await state.set_state(BookingStates.confirming)
    await message.answer(summary, reply_markup=kb.confirm_booking_kb())


@router.callback_query(BookingStates.confirming, F.data == "confirm_booking")
async def confirm_booking(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    user = callback.from_user

    total_price = data["price_per_night"] * data["nights"]
    commission_amount = round(total_price * COMMISSION_PERCENT / 100)

    booking_id = db.create_booking(
        dacha_id=data["dacha_id"],
        user_id=user.id,
        username=user.username or "",
        full_name=user.full_name,
        phone=data["phone"],
        check_in=data["check_in"],
        check_out=data["check_out"],
        nights=data["nights"],
        total_price=total_price,
        commission_amount=commission_amount,
    )

    await callback.message.edit_text(
        "✅ So'rovingiz qabul qilindi! Administrator tasdiqlashi bilan sizga xabar beriladi.",
    )
    await state.clear()
    await callback.answer()

    admin_text = (
        "🆕 <b>Yangi bron so'rovi!</b>\n\n"
        f"🏡 Dacha: {data['dacha_name']}\n"
        f"📅 Kirish: {format_date(data['check_in'])}\n"
        f"📅 Chiqish: {format_date(data['check_out'])}\n"
        f"🌙 Necha kecha: {data['nights']}\n"
        f"💰 Umumiy narx: {total_price:,} so'm\n"
        f"📞 Telefon: {data['phone']}\n"
        f"👤 Mijoz: {user.full_name} (@{user.username or 'username yo\u2018q'})\n"
        f"🆔 ID: {user.id}"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=kb.admin_decision_kb(booking_id))
        except Exception:
            pass


@router.callback_query(F.data == "cancel_booking")
async def cancel_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Bron bekor qilindi.", reply_markup=kb.main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "cancel_flow")
async def cancel_flow(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer("❌ Amal bekor qilindi.", reply_markup=kb.main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "my_bookings")
async def my_bookings(callback: CallbackQuery, state: FSMContext):
    bookings = db.get_user_bookings(callback.from_user.id)
    if not bookings:
        await callback.message.edit_text(
            "Sizda hali bronlar mavjud emas.", reply_markup=kb.main_menu_kb()
        )
        await callback.answer()
        return

    status_map = {"pending": "⏳ Kutilmoqda", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}

    lines = ["📋 <b>Sizning bronlaringiz:</b>\n"]
    for b in bookings:
        lines.append(
            f"🏡 {b['dacha_name']} | {format_date(b['check_in'])} - {format_date(b['check_out'])} | "
            f"{b['total_price']:,} so'm | {status_map.get(b['status'], b['status'])}"
        )

    await callback.message.edit_text("\n".join(lines), reply_markup=kb.main_menu_kb())
    await callback.answer()
