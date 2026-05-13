import asyncio
import os

from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен не найден! Укажите MAX_BOT_TOKEN в настройках бота на Bothost")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.bot_started()
async def handle_start(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я пока не умею отвечать на вопросы, но уже работаю.",
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
    user_text = event.message.text
    await event.message.answer(f"Ты написал: {user_text}\n\nРешаю... (скоро добавлю решение)")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())