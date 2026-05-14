import asyncio
import os
import json
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated
from aiohttp import ClientSession

# --- 1. НАСТРОЙКИ YANDEXGPT ---
# Сюда вы вставите свои данные из Yandex Cloud
#FOLDER_ID = ""      # Идентификатор каталога
#API_KEY = ""           # API-ключ сервисного аккаунта

FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("YANDEXGPT_API_KEY")

# Адрес модели YandexGPT 5.1 Pro
MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt-5.1-pro/latest"

# --- 2. НАСТРОЙКИ БОТА ---
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен не найден!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- 3. ФУНКЦИЯ ЗАПРОСА К YANDEXGPT ---
async def ask_yandexgpt(question: str) -> str:
    """Отправляет вопрос в YandexGPT и возвращает ответ"""
    
    # Промпт, который настраивает модель быть хорошим репетитором
    system_prompt = (
        "Ты — репетитор по математике для учеников 5-9 классов. "
        "Объясняй решение задач шаг за шагом, простыми словами. "
        "Не давай сразу готовый ответ — сначала объясни ход мыслей. "
        "Если ученик ошибся, мягко укажи на ошибку и помоги исправить."
    )
    
    # Формируем тело запроса для API Яндекса
    body = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,     # Температура: чем выше, тем креативнее (0.5-0.9)
            "maxTokens": 2000       # Максимальная длина ответа
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": question}
        ]
    }
    
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    
    async with ClientSession() as session:
        async with session.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers=headers,
            json=body
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Ошибка YandexGPT: {response.status} - {error_text}")
                return "Извините, у меня сейчас технические трудности. Попробуйте позже."
            
            result = await response.json()
            # Извлекаем текст ответа из результата
            return result["result"]["alternatives"][0]["message"]["text"]

# --- 4. ОБРАБОТЧИКИ КОМАНД БОТА ---

@dp.bot_started()
async def handle_start(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я новый умный репетитор по математике. Напиши /start, чтобы начать!"
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
    # Получаем текст сообщения пользователя
    user_text = None
    if hasattr(event, 'data') and hasattr(event.data, 'text'):
        user_text = event.data.text
    elif hasattr(event.message, 'data') and hasattr(event.message.data, 'text'):
        user_text = event.message.data.text
    elif hasattr(event.message, 'text'):
        user_text = event.message.text
    
    if not user_text:
        await event.message.answer("Не могу прочитать сообщение. Попробуйте написать текстом.")
        return
    
    # Отправляем уведомление, что бот думает (чтобы пользователь не ждал в тишине)
    await event.message.answer("🤔 Думаю над решением...")
    
    # Получаем ответ от YandexGPT
    answer = await ask_yandexgpt(user_text)
    
    # Отправляем ответ пользователю
    await event.message.answer(answer)

# --- 5. ЗАПУСК БОТА ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
