from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")

async def main():
    bot = Bot(token=TOKEN, default_parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    print("✅ BronlaDacha ishga tushdi.")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
