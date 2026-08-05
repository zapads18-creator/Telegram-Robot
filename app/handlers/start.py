from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🏡 TezDacha botiga xush kelibsiz!\n\n"
        "Tez orada dachalarni bron qilish tizimi ishga tushadi."
    )
