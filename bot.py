# ======================== 122
import asyncio
import os
import re
import hashlib
import aiohttp
from urllib.parse import quote
from aiohttp import ClientSession, ClientTimeout
from maxapi import Bot, Dispatcher
from maxapi.types import BotStarted, Command, MessageCreated

# ======================== 1. НАСТРОЙКИ ========================

FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("YANDEXGPT_API_KEY")
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Токен MAX не найден!")
if not FOLDER_ID:
    raise ValueError("FOLDER_ID не найден!")
if not API_KEY:
    raise ValueError("API_KEY не найден!")

MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt/rc"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

CACHE_DIR = "cache/math"
os.makedirs(CACHE_DIR, exist_ok=True)

LATEX_PATTERN = r'(\$\$.*?\$\$|\\\(.*?\\\))'

# ======================== 2. ФУНКЦИИ ДЛЯ ФОРМУЛ ========================

async def render_latex_to_image(latex_code: str) -> bytes:
    encoded = quote(latex_code)
    url = f"https://latex.codecogs.com/png.image?\\large {encoded}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            raise Exception(f"CodeCogs error: {resp.status}")

async def send_math(chat_id: int, latex_code: str, caption: str = ""):
    clean_latex = latex_code.strip()
    if clean_latex.startswith("\\(") and clean_latex.endswith("\\)"):
        clean_latex = clean_latex[2:-2]
    elif clean_latex.startswith("$$") and clean_latex.endswith("$$"):
        clean_latex = clean_latex[2:-2]
    
    hash_name = hashlib.md5(clean_latex.encode()).hexdigest()
    cache_path = os.path.join(CACHE_DIR, f"{hash_name}.png")
    
    if not os.path.exists(cache_path):
        try:
            img = await render_latex_to_image(clean_latex)
            with open(cache_path, "wb") as f:
                f.write(img)
        except Exception as e:
            await bot.send_message(chat_id, f"⚠️ Ошибка генерации: {e}")
            return
    
    try:
        with open(cache_path, "rb") as f:
            await bot.send_photo(chat_id, photo=f.read(), caption=caption)
    except Exception as e:
        await bot.send_message(chat_id, f"⚠️ Ошибка отправки: {e}")

async def send_text_with_formulas(chat_id: int, text: str):
    parts = re.split(LATEX_PATTERN, text, flags=re.DOTALL)
    for part in parts:
        if not part:
            continue
        if part.startswith("\\(") or part.startswith("$$"):
            await send_math(chat_id, part)
        else:
            await bot.send_message(chat_id, part)

# ======================== 3. YANDEXGPT ========================

async def ask_yandexgpt(question) -> str:
    if hasattr(question, 'text'):
        clean_text = question.text
    elif isinstance(question, str):
        clean_text = question
    else:
        clean_text = str(question)
    clean_text = clean_text.strip()
    
    if not clean_text:
        return "Сообщение пустое. Напишите, пожалуйста, задачу или вопрос."
    
    print(f"🔍 Вопрос: {clean_text[:50]}...")
    
    system_prompt = (
        "Ты — репетитор по математике для учеников 5-9 классов. "
        "Объясняй решение задач шаг за шагом, простыми словами. "
        "Не давай сразу готовый ответ — сначала объясни ход мыслей. "
        "Если ученик ошибся, мягко укажи на ошибку и помоги исправить.\n\n"
        "ВАЖНО: Все формулы выводи ТОЛЬКО в LaTeX, обёрнутые в \\( ... \\). "
        "Например: \\(x^2 = 4\\), \\(\\sqrt{4}\\). НЕ пиши x^2 = 4 без обёртки."
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
                    print(f"❌ Ошибка YandexGPT {response.status}: {error_text}")
                    return f"Ошибка YandexGPT (статус {response.status}). Проверьте настройки."
                result = await response.json()
                answer = result["result"]["alternatives"][0]["message"]["text"]
                print(f"✅ Ответ получен, длина: {len(answer)}")
                return answer
    except asyncio.TimeoutError:
        print("❌ Таймаут")
        return "Превышено время ожидания. Попробуйте позже."
    except Exception as e:
        print(f"❌ Исключение: {type(e).__name__}: {e}")
        return f"Техническая ошибка: {type(e).__name__}"

# ======================== 4. ОБРАБОТЧИКИ ========================

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
    if hasattr(event.message, 'body') and hasattr(event.message.body, 'text'):
        user_text = event.message.body.text
    else:
        user_text = None
    
    if not user_text:
        await event.message.answer("Не могу прочитать сообщение.")
        return
    
    chat_id = event.message.recipient.chat_id
    
    await event.message.answer("🤔 Думаю над решением...")
    answer = await ask_yandexgpt(user_text)
    
    # Принудительно оборачиваем формулу, если нет LaTeX
    if '\\(' not in answer and ('^' in answer or '=' in answer or '/' in answer):
        answer = f"\\({answer}\\)"
    
    await send_text_with_formulas(chat_id, answer)

# ======================== 5. ЗАПУСК ========================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
