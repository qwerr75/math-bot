"""
Бот-репетитор по математике для платформы MAX с использованием YandexGPT.
Версия: 2.1 (исправлена ошибка JSON-сериализации)
"""

import asyncio
import os
from aiohttp import ClientSession, ClientTimeout
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

# ======================== 1. НАСТРОЙКИ ========================

FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("YANDEXGPT_API_KEY")
MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt-5.1-pro/latest"

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен MAX не найден!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================== 2. ФУНКЦИЯ ЗАПРОСА К YANDEXGPT ========================

async def ask_yandexgpt(question: str) -> str:
    """ВРЕМЕННАЯ ФУНКЦИЯ ДЛЯ ДИАГНОСТИКИ"""
    # Просто возвращаем текст, который получили
    return f"Я получил твой вопрос: «{question}». Сейчас YandexGPT временно отключён для диагностики."

# ======================== 3. ОБРАБОТЧИКИ СООБЩЕНИЙ ========================

@dp.bot_started()
async def handle_start(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я репетитор по математике. Напиши /start для продолжения."
    )

@dp.message_created(Command("start"))
async def cmd_start(event: MessageCreated):
    await event.message.answer(
        "📚 Я репетитор по математике 5-9 классов.\n"
        "Пришли любую задачу — объясню по шагам.\n\n"
        "🔹 Бесплатно: 5 задач в день\n"
        "🔹 Подписка: 399₽/мес, безлимит"
    )

@dp.message_created()
async def handle_message(event: MessageCreated):
    # Получаем текст из правильного поля (body)
    user_text = event.message.body if hasattr(event.message, 'body') else None
    
    if not user_text:
        await event.message.answer("Не могу прочитать сообщение. Попробуйте написать текстом.")
        return
    
    await event.message.answer("🤔 Думаю над решением...")
    answer = await ask_yandexgpt(user_text)
    await event.message.answer(answer)

# ======================== 4. ЗАПУСК ========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
