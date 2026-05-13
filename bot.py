import asyncio
import os
import json
from aiohttp import ClientSession, ClientTimeout

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен не найден! Укажите MAX_BOT_TOKEN в настройках бота")

API_BASE = "https://api.max.ru/bot/v1"
HEADERS = {
    "Authorization": f"Bearer {BOT_TOKEN}",
    "Content-Type": "application/json"
}

async def send_message(chat_id, text):
    """Отправка сообщения пользователю"""
    async with ClientSession() as session:
        url = f"{API_BASE}/messages/send"
        payload = {
            "chat_id": chat_id,
            "text": text
        }
        try:
            async with session.post(url, headers=HEADERS, json=payload) as resp:
                if resp.status != 200:
                    text_err = await resp.text()
                    print(f"Ошибка отправки {resp.status}: {text_err}")
        except Exception as e:
            print(f"Ошибка при отправке: {e}")

async def get_updates(offset=0):
    """Получение новых сообщений (Long Polling)"""
    async with ClientSession() as session:
        url = f"{API_BASE}/updates/get"
        params = {
            "offset": offset,
            "timeout": 30
        }
        try:
            async with session.get(url, headers=HEADERS, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("updates", [])
                else:
                    text_err = await resp.text()
                    print(f"Ошибка получения обновлений {resp.status}: {text_err}")
                    return []
        except Exception as e:
            print(f"Ошибка при получении: {e}")
            return []

async def handle_update(update):
    """Обработка одного обновления"""
    # Получаем сообщение из обновления
    message = update.get("message")
    if not message:
        return
    
    # Получаем chat_id (может быть в разных местах)
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        chat_id = message.get("chat_id")
    if not chat_id:
        print(f"Не удалось получить chat_id из сообщения: {message}")
        return
    
    # Получаем текст сообщения
    text = message.get("text", "")
    if not text:
        # Возможно, текст в другом поле
        text = message.get("content", {}).get("text", "")
    
    print(f"Получено сообщение от {chat_id}: {text}")
    
    # Обработка команды /start
    if text == "/start":
        await send_message(chat_id, 
            "📚 Я репетитор по математике 5-9 классов.\n"
            "Пришли любую задачу — объясню по шагам.\n\n"
            "🔹 Бесплатно: 5 задач в день\n"
            "🔹 Подписка: 399₽/мес, безлимит"
        )
        return
    
    # Ответ на любое другое сообщение
    if text:
        await send_message(chat_id, f"Ты написал: {text}\n\nРешаю... (скоро добавлю решение)")
    else:
        await send_message(chat_id, "Получил сообщение, но текст не распознан")

async def main():
    print("Бот запущен, жду сообщений...")
    offset = 0
    while True:
        updates = await get_updates(offset)
        for update in updates:
            await handle_update(update)
            # Обновляем offset, чтобы не получать одни и те же сообщения
            update_id = update.get("update_id")
            if update_id:
                offset = update_id + 1
        await asyncio.sleep(0.5)  # Небольшая пауза для снижения нагрузки

if __name__ == "__main__":
    asyncio.run(main())
