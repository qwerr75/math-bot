import asyncio
import os
from maxapi import Bot

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

async def main():
    me = await bot.get_me()
    print(f"Бот {me.username} запущен")
    
    # Long Polling цикл
    offset = 0
    while True:
        updates = await bot.get_updates(offset=offset, timeout=30)
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
            offset = update["update_id"] + 1

if __name__ == "__main__":
    asyncio.run(main())
