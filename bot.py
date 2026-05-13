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
    # Пытаемся найти текст сообщения
    text = None
    
    # Пробуем разные варианты получения текста
    if hasattr(update, 'message'):
        msg = update.message
        if hasattr(msg, 'text'):
            text = msg.text
        elif hasattr(msg, 'content'):
            text = msg.content
        elif hasattr(msg, 'data') and hasattr(msg.data, 'text'):
            text = msg.data.text
    
    if not text:
        # Если текст не найден, отвечаем заглушкой
        if hasattr(update, 'message'):
            await update.message.answer("Сообщение получено, но текст не распознан")
        return
    
    # Обработка команды /start
    if text == "/start":
        await update.message.answer(
            "📚 Я репетитор по математике 5-9 классов.\n"
            "Пришли любую задачу — объясню по шагам.\n\n"
            "🔹 Бесплатно: 5 задач в день\n"
            "🔹 Подписка: 399₽/мес, безлимит"
        )
        return
    
    # Ответ на любое другое сообщение
    await update.message.answer(f"Ты написал: {text}\n\nРешаю... (скоро добавлю решение)")

async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
