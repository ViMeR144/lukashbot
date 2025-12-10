"""
Веб-сервер для работы с webhook на Render (бот для билетов)
"""
import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

# Импортируем диспетчер из bot_tickets.py
from bot_tickets import dp

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "")  # URL вашего приложения на Render
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

bot = Bot(token=BOT_TOKEN)


async def on_startup(bot: Bot) -> None:
    """Установка webhook при запуске"""
    if WEBHOOK_HOST:
        await bot.set_webhook(WEBHOOK_URL)
        logger.info(f"Webhook установлен: {WEBHOOK_URL}")
    else:
        logger.warning("WEBHOOK_HOST не установлен, webhook не будет настроен")


async def on_shutdown(bot: Bot) -> None:
    """Удаление webhook при остановке"""
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Webhook удален, сессия закрыта")


def create_app() -> web.Application:
    """Создание приложения aiohttp"""
    app = web.Application()
    
    # Настраиваем webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    # Настраиваем приложение
    setup_application(app, dp, bot=bot)
    
    # Обработчики для startup/shutdown
    app.on_startup.append(lambda _: asyncio.create_task(on_startup(bot)))
    app.on_shutdown.append(lambda _: asyncio.create_task(on_shutdown(bot)))
    
    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 8000))
    web.run_app(app, host="0.0.0.0", port=port)

