"""
Бот-репетитор по математике для платформы MAX с использованием YandexGPT.
Версия: 2.2 (исправлены отступы и ошибка FOLDER_ID)
"""

import asyncio
import os
from aiohttp import ClientSession, ClientTimeout
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

# ======================== 1. НАСТРОЙКИ ========================

# Получаем переменные окружения
FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("YANDEXGPT_API_KEY")
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

# Проверяем, что все переменные заданы
if not BOT_TOKEN:
    raise ValueError("Токен MAX не найден! Укажите MAX_BOT_TOKEN в настройках Bothost")
if not FOLDER_ID:
    raise ValueError("FOLDER_ID не найден! Укажите FOLDER_ID в настройках Bothost")
if not API_KEY:
    raise ValueError("API_KEY не найден! Укажите YANDEXGPT_API_KEY в настройках Bothost")

# Формируем URI для модели YandexGPT 5.1 Pro
MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt/rc"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================== 2. ФУНКЦИЯ ЗАПРОСА К YANDEXGPT ========================

async def ask_yandexgpt(question) -> str:
    """
    Отправляет вопрос в YandexGPT и возвращает ответ.
    """
    # Извлекаем чистый текст
    if hasattr(question, 'text'):
        clean_text = question.text
    elif isinstance(question, str):
        clean_text = question
    else:
        clean_text = str(question)

    clean_text = clean_text.strip()

    if not clean_text:
        return "Сообщение пустое. Напишите, пожалуйста, задачу или вопрос."

    # Диагностика в логах
    print(f"🔍 Вопрос: {clean_text[:50]}...")

    system_prompt = (
        "Ты — репетитор по математике для учеников 5-9 классов. "
        "Объясняй решение задач шаг за шагом, простыми словами. "
        "Не давай сразу готовый ответ — сначала объясни ход мыслей. "
        "Если ученик ошибся, мягко укажи на ошибку и помоги исправить."
    )

    request_body = {
        "modelUri": MODEL_URI,
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": 2000
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": clean_text}
        ]
    }

    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json",
        "x-folder-id": FOLDER_ID
    }

    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    try:
        async with ClientSession() as session:
            timeout = ClientTimeout(total=30)
            async with session.post(url, headers=headers, json=request_body, timeout=timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"❌ Ошибка {response.status}: {error_text}")
                    return f"Ошибка YandexGPT (статус {response.status}). Проверьте настройки."

                result = await response.json()
                answer = result["result"]["alternatives"][0]["message"]["text"]
                print(f"✅ Ответ получен, длина: {len(answer)}")
                return answer

    except asyncio.TimeoutError:
        print("❌ Таймаут запроса")
        return "Превышено время ожидания. Попробуйте позже."
    except Exception as e:
        print(f"❌ Исключение: {type(e).__name__}: {e}")
        return f"Техническая ошибка: {type(e).__name__}"

# ======================== 3. ОБРАБОТЧИКИ СООБЩЕНИЙ ========================

@dp.bot_started()
async def handle_start(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я репетитор по математике. Напиши /start для продолжения."
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
    # Получаем текст из правильного поля
    user_text = event.message.body if hasattr(event.message, 'body') else None

    if not user_text:
        await event.message.answer("Не могу прочитать сообщение. Попробуйте написать текстом.")
        return

    await event.message.answer("🤔 Думаю над решением...")
    answer = await ask_yandexgpt(user_text)
    await event.message.answer(answer)

# ======================== 4. ЗАПУСК ========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
