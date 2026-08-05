
import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message


async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))

    dp = Dispatcher()

    @dp.message(CommandStart())
    async def start(message: Message):
        await message.answer("🏡 TezDacha ishlayapti!")

    print("🚀 Bot ishga tushdi")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
