import asyncio
import os
from maxapi import Bot

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен не найден!")

bot = Bot(token=BOT_TOKEN)

async def main():
    me = await bot.get_me()
    print(f"Бот {me.username} запущен")
    
    offset = 0
    while True:
        # Пытаемся получить обновления. Если offset не поддерживается, убираем его.
        try:
            updates = await bot.get_updates(timeout=30)
        except TypeError:
            # Если ошибка повторяется, пробуем без аргументов
            updates = await bot.get_updates()
        
        for update in updates:
            if "message" in update:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message.get("text", "")
                
                if text == "/start":
                    await bot.send_message(
                        chat_id,
                        "📚 Я репетитор по математике 5-9 классов.\n"
                        "Пришли любую задачу — объясню по шагам.\n\n"
                        "🔹 Бесплатно: 5 задач в день\n"
                        "🔹 Подписка: 399₽/мес, безлимит"
                    )
                elif text:
                    await bot.send_message(
                        chat_id,
                        f"Ты написал: {text}\n\nРешаю... (скоро добавлю решение)"
                    )
            # Обновляем offset, если есть update_id
            if "update_id" in update:
                offset = update["update_id"] + 1
        
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
