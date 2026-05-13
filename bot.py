import asyncio
import os
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен не найден!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.bot_started()
async def handle_start(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я репетитор по математике.",
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
    # Пытаемся получить текст из разных возможных мест
    user_text = None
    
    # Способ 1: напрямую как атрибут
    if hasattr(event.message, 'text'):
        user_text = event.message.text
    # Способ 2: в словаре data
    elif hasattr(event.message, 'data') and isinstance(event.message.data, dict):
        user_text = event.message.data.get('text')
    # Способ 3: в атрибуте content
    elif hasattr(event.message, 'content'):
        user_text = event.message.content
    
    # Если текст не найден — выводим всю структуру в лог
    if not user_text:
        print(f"Структура message: {dir(event.message)}")
        if hasattr(event.message, 'data'):
            print(f"data: {event.message.data}")
        await event.message.answer("Получил сообщение, но не могу прочитать текст")
        return
    
    await event.message.answer(f"Ты написал: {user_text}\n\nРешаю... (скоро добавлю решение)")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
