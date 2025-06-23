import asyncio
from aiogram import Bot, Dispatcher
from core.config import settings
from bot.handlers import router

async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    print("Бот запущен. Ожидаю команду /start...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
