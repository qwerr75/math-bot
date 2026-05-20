"""
NeuroClass Bot — репетитор по математике в MAX
Версия: 2.0 (с поддержкой формул через CodeCogs)
"""

import asyncio
import os
import re
import hashlib
import aiohttp
from urllib.parse import quote
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

# ======================== 1. НАСТРОЙКИ ========================

BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("YANDEXGPT_API_KEY")

if not BOT_TOKEN:
    raise ValueError("MAX_BOT_TOKEN не найден!")
if not FOLDER_ID:
    raise ValueError("FOLDER_ID не найден!")
if not API_KEY:
    raise ValueError("YANDEXGPT_API_KEY не найден!")

MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt-5.1-pro/latest"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Папка для кэша формул
CACHE_DIR = "cache/math"
os.makedirs(CACHE_DIR, exist_ok=True)

# Регулярное выражение для поиска формул в тексте
# Ищет \( ... \) и $$ ... $$
LATEX_PATTERN = r'(\$\$.*?\$\$|\\\(.*?\\\))'

# ======================== 2. ФУНКЦИЯ ДЛЯ ФОРМУЛ ========================

async def render_latex_to_image(latex_code: str) -> bytes:
    """Превращает LaTeX-код в PNG-картинку через CodeCogs"""
    encoded = quote(latex_code)
    url = f"https://latex.codecogs.com/png.image?\\large {encoded}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            raise Exception(f"CodeCogs error: {resp.status}")

async def send_math(chat_id: int, latex_code: str, caption: str = ""):
    """Отправляет формулу картинкой (с кэшированием)"""
    # Убираем ограничители \( \) или $$ $$
    clean_latex = latex_code.strip()
    if clean_latex.startswith("\\(") and clean_latex.endswith("\\)"):
        clean_latex = clean_latex[2:-2]
    elif clean_latex.startswith("$$") and clean_latex.endswith("$$"):
        clean_latex = clean_latex[2:-2]
    
    # Кэширование
    hash_name = hashlib.md5(clean_latex.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{hash_name}.png")
    
    if os.path.exists(cache_path):
        with open(cache_path, "rb") as f:
            img = f.read()
        await bot.send_photo(chat_id, photo=img, caption=caption)
        return
    
    # Генерация через CodeCogs
    try:
        img = await render_latex_to_image(clean_latex)
        with open(cache_path, "wb") as f:
            f.write(img)
        await bot.send_photo(chat_id, photo=img, caption=caption)
    except Exception as e:
        # Запасной вариант — отправить текст
        await bot.send_message(chat_id, f"⚠️ Формула: {clean_latex}\n{caption}")

async def send_text_with_formulas(chat_id: int, text: str):
    """
    Отправляет текст, автоматически заменяя формулы \( ... \) и $$ ... $$ на картинки
    """
    parts = re.split(LATEX_PATTERN, text, flags=re.DOTALL)
    
    for part in parts:
        if not part:
            continue
        # Если часть — это формула (начинается с \( или $$)
        if part.startswith("\\(") or part.startswith("$$"):
            await send_math(chat_id, part)
        else:
            # Обычный текст
            await bot.send_message(chat_id, part)

# ======================== 3. ФУНКЦИЯ ЗАПРОСА К YANDEXGPT ========================

async def ask_yandexgpt(question: str) -> str:
    """Отправляет вопрос в YandexGPT и возвращает ответ"""
    
    system_prompt = (
        "Ты — репетитор по математике для учеников 5-9 классов. "
        "Объясняй решение задач шаг за шагом, простыми словами. "
        "Не давай сразу готовый ответ — сначала объясни ход мыслей. "
        "Если ученик ошибся, мягко укажи на ошибку и помоги исправить.\n\n"
        "Формулы оформляй в LaTeX внутри \\( ... \\) (для коротких формул) или $$ ... $$ (для вынесенных)."
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
            {"role": "user", "text": question}
        ]
    }
    
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json",
        "x-folder-id": FOLDER_ID
    }
    
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"YandexGPT error {response.status}: {error_text}")
                return "Извините, у меня сейчас технические трудности. Попробуйте позже."
            
            result = await response.json()
            return result["result"]["alternatives"][0]["message"]["text"]

# ======================== 4. ОБРАБОТЧИКИ СООБЩЕНИЙ ========================

@dp.bot_started()
async def handle_start(event: BotStarted):
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я репетитор NeuroClass. Напиши /start для продолжения."
    )

@dp.message_created(Command("start"))
async def cmd_start(event: MessageCreated):
    await bot.send_message(
        event.message.chat.id,
        "📚 Я репетитор по математике 5-9 классов.\n"
        "Пришли любую задачу — объясню по шагам.\n\n"
        "🔹 Бесплатно: 5 задач в день\n"
        "🔹 Подписка: 399₽/мес, безлимит"
    )

@dp.message_created()
async def handle_message(event: MessageCreated):
    # Получаем текст сообщения
    user_text = None
    if hasattr(event.message, 'body'):
        user_text = event.message.body
    elif hasattr(event, 'data') and hasattr(event.data, 'text'):
        user_text = event.data.text
    
    if not user_text:
        await bot.send_message(event.message.chat.id, "Не могу прочитать сообщение.")
        return
    
    # Отправляем уведомление о начале обработки
    await bot.send_message(event.message.chat.id, "🤔 Думаю над решением...")
    
    # Получаем ответ от YandexGPT
    answer = await ask_yandexgpt(user_text)
    
    # Отправляем ответ с автоматической заменой формул на картинки
    await send_text_with_formulas(event.message.chat.id, answer)

# ======================== 5. ЗАПУСК ========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
