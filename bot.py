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
    # ВЫВОДИМ В ЛОГИ ВСЮ СТРУКТУРУ
    print("=== Диагностика: начало ===")
    print(f"Тип event: {type(event)}")
    print(f"Атрибуты event: {dir(event)}")
    
    if hasattr(event, 'message'):
        print(f"Тип event.message: {type(event.message)}")
        print(f"Атрибуты event.message: {dir(event.message)}")
        if hasattr(event.message, 'data'):
            print(f"event.message.data: {event.message.data}")
    
    if hasattr(event, 'data'):
        print(f"Тип event.data: {type(event.data)}")
        print(f"event.data: {event.data}")
    
    print("=== Диагностика: конец ===")
    
    # Пытаемся найти текст (пока заглушка)
    await event.message.answer("Диагностика завершена, смотрите логи Bothost")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
