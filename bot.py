import asyncio
import os
from aiohttp import ClientSession

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
API_BASE = "https://platform-api.max.ru/bot/v1"
HEADERS = {"Authorization": f"Bearer {BOT_TOKEN}", "Content-Type": "application/json"}

async def send_message(chat_id, text):
    async with ClientSession() as session:
        async with session.post(f"{API_BASE}/messages/send", headers=HEADERS, json={"chat_id": chat_id, "text": text}) as resp:
            if resp.status != 200:
                print(await resp.text())

async def get_updates(offset=0):
    async with ClientSession() as session:
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
        async with session.get(f"{API_BASE}/updates/get", headers=HEADERS, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("updates", [])
            print(f"Ошибка {resp.status}: {await resp.text()}")
            return []

async def main():
    print("Бот запущен")
    offset = 0
    while True:
        updates = await get_updates(offset)
        for upd in updates:
            msg = upd.get("message")
            if msg:
                chat_id = msg["chat"]["id"]
                text = msg.get("text", "")
                if text == "/start":
                    await send_message(chat_id, "Привет! Я репетитор.")
                elif text:
                    await send_message(chat_id, f"Ты написал: {text}")
            offset = upd.get("update_id", offset) + 1
        await asyncio.sleep(0.5)

if __name__ == "__main__":
    asyncio.run(main())
