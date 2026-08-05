import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
import aiosqlite

# ============ SOZLAMALAR ============
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"   # @BotFather'dan olingan token
ADMIN_ID = 123456789                 # Sizning Telegram ID'ingiz (@userinfobot orqali bilib oling)
DB_PATH = "dachas.db"
# =====================================

logging.basicConfig(level=logging.INFO)
router = Router()


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dachas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                location TEXT,
                price_per_day INTEGER,
                description TEXT,
                contact TEXT,
                is_available INTEGER DEFAULT 1
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dacha_id INTEGER,
                user_id INTEGER,
                username TEXT,
                date_from TEXT,
                date_to TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT
            )
        """)
        await db.commit()


class BookingStates(StatesGroup):
    waiting_for_dates = State()
    waiting_for_phone = State()


class AddDachaStates(StatesGroup):
    name = State()
    location = State()
    price = State()
    description = State()
    contact = State()


# ============ FOYDALANUVCHI QISMI ============

@router.message(CommandStart())
async def cmd_start(message: Message):
    text = (
        "🏡 <b>Dacha Bron Bot</b>ga xush kelibsiz!\n\n"
        "Bu yerda siz O'zbekiston bo'ylab dachalarni ko'rishingiz "
        "va bron qilishingiz mumkin.\n\n"
        "/dachalar — mavjud dachalarni ko'rish\n"
    )
    if message.from_user.id == ADMIN_ID:
        text += (
            "\n<b>Admin buyruqlari:</b>\n"
            "/dacha_qoshish — yangi dacha qo'shish\n"
            "/bronlar — barcha bronlarni ko'rish"
        )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("dachalar"))
async def list_dachas(message: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, name, location, price_per_day FROM dachas WHERE is_available = 1"
        )
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("Hozircha mavjud dachalar yo'q.")
        return

    for dacha_id, name, location, price in rows:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔍 Batafsil", callback_data=f"view_{dacha_id}")
        ]])
        await message.answer(
            f"🏡 <b>{name}</b>\n📍 {location}\n💰 {price:,} so'm/kun",
            parse_mode="HTML",
            reply_markup=kb
        )


@router.callback_query(F.data.startswith("view_"))
async def view_dacha(callback: CallbackQuery):
    dacha_id = int(callback.data.split("_")[1])
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT name, location, price_per_day, description, contact FROM dachas WHERE id = ?",
            (dacha_id,)
        )
        row = await cursor.fetchone()

    if not row:
        await callback.answer("Topilmadi", show_alert=True)
        return

    name, location, price, description, contact = row
    text = (
        f"🏡 <b>{name}</b>\n"
        f"📍 Manzil: {location}\n"
        f"💰 Narx: {price:,} so'm/kun\n"
        f"📝 {description}\n"
        f"☎️ {contact}"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Bron qilish", callback_data=f"book_{dacha_id}")
    ]])
    await callback.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("book_"))
async def start_booking(callback: CallbackQuery, state: FSMContext):
    dacha_id = int(callback.data.split("_")[1])
    await state.update_data(dacha_id=dacha_id)
    await state.set_state(BookingStates.waiting_for_dates)
    await callback.message.answer(
        "📅 Qaysi sanalarga bron qilmoqchisiz?\n"
        "Masalan: 15.08.2026 - 17.08.2026"
    )
    await callback.answer()


@router.message(BookingStates.waiting_for_dates)
async def get_dates(message: Message, state: FSMContext):
    await state.update_data(dates=message.text)
    await state.set_state(BookingStates.waiting_for_phone)
    await message.answer("📞 Aloqa uchun telefon raqamingizni yuboring:")


@router.message(BookingStates.waiting_for_phone)
async def get_phone(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    dacha_id = data["dacha_id"]
    dates = data["dates"]
    phone = message.text

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO bookings (dacha_id, user_id, username, date_from, date_to, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (dacha_id, message.from_user.id, message.from_user.username or "noma'lum",
             dates, phone, datetime.now().isoformat())
        )
        await db.commit()

        cursor = await db.execute("SELECT name, contact FROM dachas WHERE id = ?", (dacha_id,))
        dacha_name, owner_contact = await cursor.fetchone()

    await message.answer(
        f"✅ So'rovingiz qabul qilindi!\n\n"
        f"🏡 {dacha_name}\n📅 {dates}\n\n"
        f"Tez orada egasi siz bilan bog'lanadi: {owner_contact}"
    )

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🔔 Yangi bron so'rovi!\n"
            f"🏡 Dacha: {dacha_name}\n"
            f"📅 Sana: {dates}\n"
            f"👤 Foydalanuvchi: @{message.from_user.username or message.from_user.id}\n"
            f"📞 Tel: {phone}"
        )
    except Exception as e:
        logging.error(f"Adminga xabar yuborishda xato: {e}")

    await state.clear()


# ============ ADMIN QISMI ============

@router.message(Command("dacha_qoshish"))
async def add_dacha_start(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("Bu buyruq faqat admin uchun.")
        return
    await state.set_state(AddDachaStates.name)
    await message.answer("Dacha nomini kiriting:")


@router.message(AddDachaStates.name)
async def add_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddDachaStates.location)
    await message.answer("Manzilini kiriting (masalan: Chirchiq tumani):")


@router.message(AddDachaStates.location)
async def add_location(message: Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(AddDachaStates.price)
    await message.answer("Bir kunlik narxini kiriting (faqat raqam, so'mda):")


@router.message(AddDachaStates.price)
async def add_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos faqat raqam kiriting:")
        return
    await state.update_data(price=int(message.text))
    await state.set_state(AddDachaStates.description)
    await message.answer("Qisqacha tavsif kiriting:")


@router.message(AddDachaStates.description)
async def add_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddDachaStates.contact)
    await message.answer("Aloqa uchun telefon raqam yoki Telegram username kiriting:")


@router.message(AddDachaStates.contact)
async def add_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO dachas (name, location, price_per_day, description, contact) "
            "VALUES (?, ?, ?, ?, ?)",
            (data["name"], data["location"], data["price"], data["description"], message.text)
        )
        await db.commit()
    await message.answer(f"✅ '{data['name']}' muvaffaqiyatli qo'shildi!")
    await state.clear()


@router.message(Command("bronlar"))
async def list_bookings(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT b.id, d.name, b.username, b.date_from, b.status
            FROM bookings b JOIN dachas d ON b.dacha_id = d.id
            ORDER BY b.id DESC LIMIT 20
        """)
        rows = await cursor.fetchall()

    if not rows:
        await message.answer("Hozircha bronlar yo'q.")
        return

    text = "📋 <b>Oxirgi bronlar:</b>\n\n"
    for bid, name, username, dfrom, status in rows:
        text += f"#{bid} | {name} | @{username} | {dfrom} | {status}\n"
    await message.answer(text, parse_mode="HTML")


async def main():
    await init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
