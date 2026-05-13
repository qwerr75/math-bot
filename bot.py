import asyncio
import os
from maxapi import Bot, Dispatcher

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен не найден! Укажите MAX_BOT_TOKEN в настройках бота")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.update()
async def handle_update(update):
    # Пытаемся извлечь сообщение из любого места
    message = None
    if hasattr(update, "message"):
        message = update.message
    elif hasattr(update, "data") and hasattr(update.data, "message"):
        message = update.data.message
    
    if not message:
        return
    
    # Пытаемся получить текст сообщения
    text = None
    if hasattr(message, "text"):
        text = message.text
    elif hasattr(message, "content"):
        text = message.content
    elif isinstance(message, dict):
        text = message.get("text") or message.get("content")
    
    # Если текст не найден — отвечаем заглушкой
    if not text:
        await message.answer("Получил сообщение, но текст не найден")
        return
    
    # Обработка команды /start
    if text == "/start":
        await message.answer(
            "📚 Я репетитор по математике 5-9 классов.\n"
            "Пришли любую задачу — объясню по шагам.\n\n"
            "🔹 Бесплатно: 5 задач в день\n"
            "🔹 Подписка: 399₽/мес, безлимит"
        )
        return
    
    # Ответ на любое другое сообщение
    await message.answer(f"Ты написал: {text}\n\nРешаю... (скоро добавлю решение)")

async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
