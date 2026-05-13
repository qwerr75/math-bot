import asyncio
import os

from maxapi import Bot, Dispatcher
from maxapi.filters import MessageCreated, Command
from maxapi.types import BotStarted, Message

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен не найден! Укажите MAX_BOT_TOKEN в настройках бота")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.update(BotStarted)
async def on_bot_started(update: BotStarted):
    print(f"Бот запущен для чата {update.chat_id}")

@dp.update(Message, Command("start"))
async def on_start_command(message: Message):
    await message.answer(
        "📚 Я репетитор по математике 5-9 классов.\n"
        "Пришли любую задачу — объясню по шагам.\n\n"
        "🔹 Бесплатно: 5 задач в день\n"
        "🔹 Подписка: 399₽/мес, безлимит"
    )

@dp.update(Message)
async def on_any_message(message: Message):
    user_text = message.text
    await message.answer(f"Ты написал: {user_text}\n\nРешаю... (скоро добавлю решение)")

async def main():
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
