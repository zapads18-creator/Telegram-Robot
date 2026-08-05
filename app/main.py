import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.handlers.start import router


async def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        print("❌ BOT_TOKEN topilmadi")
        return

    bot = Bot(
        token=token,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML
        )
    )

    dp = Dispatcher()

    dp.include_router(router)

    print("🚀 TezDacha ishga tushdi")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
