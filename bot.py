import asyncio
import os
from aiohttp import ClientSession

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
# Правильный базовый URL из документации MAX [citation:4][citation:8]
API_BASE = "https://platform-api.max.ru"
HEADERS = {"Authorization": BOT_TOKEN, "Content-Type": "application/json"}

async def send_message(chat_id: int, text: str):
    """Отправка сообщения по правильному пути и с правильным токеном [citation:4][citation:9]."""
    async with ClientSession() as session:
        # Путь из документации: POST /messages/send?chat_id=... [citation:4]
        url = f"{API_BASE}/messages/send"
        params = {"chat_id": chat_id}
        payload = {"text": text}
        
        async with session.post(url, headers=HEADERS, params=params, json=payload) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                print(f"Ошибка отправки {resp.status}: {error_text}")

async def get_updates(marker: int = 0):
    """Получение обновлений через Long Polling [citation:8]."""
    async with ClientSession() as session:
        # Правильный путь: GET /updates [citation:8]
        url = f"{API_BASE}/updates"
        # Передаем параметр marker для управления полученными обновлениями [citation:8]
        params = {"marker": marker, "timeout": 30} if marker > 0 else {"timeout": 30}
        
        async with session.get(url, headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("updates", [])
            else:
                error_text = await resp.text()
                print(f"Ошибка получения обновлений {resp.status}: {error_text}")
                return []

async def main():
    print("Бот запущен, жду сообщений...")
    marker = 0
    while True:
        updates = await get_updates(marker)
        for upd in updates:
            # Извлекаем тип обновления (поле 'type') и его содержимое (поле 'body')
            if upd.get("type") == "message_created":
                # Тело сообщения находится в поле 'body'
                body = upd.get("body", {})
                # Пользователь, отправивший сообщение
                sender = body.get("sender", {})
                user_id = sender.get("user_id")
                
                # Текст сообщения внутри поля 'body'
                text = body.get("text", "")
                
                print(f"Получено сообщение от {user_id}: {text}")
                
                # Обработка команды /start
                if text == "/start":
                    await send_message(user_id,
                        "📚 Я репетитор по математике 5-9 классов.\n"
                        "Пришли любую задачу — объясню по шагам.\n\n"
                        "🔹 Бесплатно: 5 задач в день\n"
                        "🔹 Подписка: 399₽/мес, безлимит"
                    )
                # Ответ на любое другое сообщение
                elif text:
                    await send_message(user_id, f"Ты написал: {text}\n\nРешаю... (скоро добавлю решение)")
            
            # Обновляем marker, как того требует API, для получения следующих обновлений [citation:8]
            marker = upd.get("marker", marker)
        
        # Небольшая пауза, чтобы не нагружать процессор
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
