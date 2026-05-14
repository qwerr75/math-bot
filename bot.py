"""
Бот-репетитор по математике для платформы MAX с использованием YandexGPT.
Автор: qwerr75
Версия: 2.0 (с поддержкой актуальной версии maxapi)
"""

# Подключаем библиотеки
import asyncio          # Для асинхронного выполнения
import os               # Для работы с переменными окружения (токены, ключи)
from maxapi import Bot, Dispatcher              # Основные классы для бота
from maxapi.types import BotStarted, Command, MessageCreated  # Типы событий
from aiohttp import ClientSession               # Для HTTP-запросов к YandexGPT

# ======================== 1. НАСТРОЙКИ И ПЕРЕМЕННЫЕ ========================

# --- Данные для подключения к YandexGPT (берите из переменных окружения!) ---
# ВНИМАНИЕ: Никогда не вписывайте ключи и ID напрямую в код!
# В панели Bothost создайте переменные окружения: FOLDER_ID и YANDEXGPT_API_KEY
FOLDER_ID = os.getenv("FOLDER_ID")                 # ID каталога в Yandex Cloud
API_KEY = os.getenv("YANDEXGPT_API_KEY")           # API-ключ сервисного аккаунта

# Адрес (URI) модели YandexGPT 5.1 Pro
MODEL_URI = f"gpt://{FOLDER_ID}/yandexgpt-5.1-pro/latest"

# --- Данные для подключения к MAX (токен бота) ---
# Токен передаётся платформой Bothost автоматически
BOT_TOKEN = os.getenv("MAX_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Токен MAX не найден! Проверьте настройки бота в Bothost.")

# Создаём объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======================== 2. ФУНКЦИЯ ЗАПРОСА К YANDEXGPT ========================

async def ask_yandexgpt(question: str) -> str:
    """
    Отправляет вопрос пользователя в YandexGPT и возвращает ответ репетитора.
    
    Параметры:
        question (str): Текст вопроса от пользователя
    
    Возвращает:
        str: Ответ от нейросети или сообщение об ошибке
    """
    
    # Системный промпт — настройка поведения модели
    # Модель будет объяснять математику для 5-9 классов, по шагам, дружелюбно
    system_prompt = (
        "Ты — репетитор по математике для учеников 5-9 классов. "
        "Объясняй решение задач шаг за шагом, простыми словами. "
        "Не давай сразу готовый ответ — сначала объясни ход мыслей. "
        "Если ученик ошибся, мягко укажи на ошибку и помоги исправить."
    )
    
    # Формируем тело запроса к API YandexGPT
    # Подробнее о параметрах: https://cloud.yandex.ru/docs/yandexgpt/api-ref/TextGeneration/completion
    request_body = {
        "modelUri": MODEL_URI,                      # Какая модель используется
        "completionOptions": {
            "stream": False,                       # Получаем ответ целиком, а не по частям
            "temperature": 0.7,                    # Креативность (0.0 — строго, 1.0 — вольно)
            "maxTokens": 2000                      # Максимальная длина ответа (символов)
        },
        "messages": [
            {"role": "system", "text": system_prompt},   # Инструкция для модели
            {"role": "user", "text": question}           # Вопрос пользователя
        ]
    }
    
    # Заголовки запроса: авторизация по API-ключу
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # URL эндпоинта YandexGPT (foundationModels версии 1)
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    
    # Отправляем запрос
    async with ClientSession() as session:
        async with session.post(url, headers=headers, json=request_body) as response:
            if response.status != 200:
                # Если произошла ошибка, выводим её в логи и возвращаем дружелюбное сообщение
                error_text = await response.text()
                print(f"Ошибка YandexGPT (статус {response.status}): {error_text}")
                return "Извините, у меня сейчас технические трудности. Попробуйте позже."
            
            # Парсим JSON-ответ от Яндекса
            result = await response.json()
            # Извлекаем текст ответа из структуры результата
            # Типичная структура: result["result"]["alternatives"][0]["message"]["text"]
            answer = result["result"]["alternatives"][0]["message"]["text"]
            return answer

# ======================== 3. ОБРАБОТЧИКИ СОБЫТИЙ ОТ MAX ========================

@dp.bot_started()
async def handle_start(event: BotStarted):
    """
    Обработчик события 'bot_started' — когда пользователь первый раз нажал "Начать".
    Просто шлём короткое приветствие.
    """
    await bot.send_message(
        chat_id=event.chat_id,
        text="Привет! Я репетитор по математике. Напиши /start для продолжения."
    )

@dp.message_created(Command("start"))
async def cmd_start(event: MessageCreated):
    """
    Обработчик команды /start.
    Отправляем подробное описание и тарифы.
    """
    await event.message.answer(
        "📚 Я репетитор по математике 5-9 классов.\n"
        "Пришли любую задачу — объясню по шагам.\n\n"
        "🔹 Бесплатно: 5 задач в день\n"
        "🔹 Подписка: 399₽/мес, безлимит"
    )

@dp.message_created()
async def handle_message(event: MessageCreated):
    """
    Обработчик всех остальных текстовых сообщений.
    Получает текст от пользователя, отправляет в YandexGPT и возвращает ответ.
    """
    # --- 1. Получаем текст сообщения ---
    # ВАЖНО: В версии maxapi с Pydantic текст лежит в event.message.body
    # (это выяснили с помощью диагностики)
    user_text = None
    
    # Основной способ (для вашей версии библиотеки)
    if hasattr(event.message, 'body'):
        user_text = event.message.body
    # Резервные способы (на случай обновлений библиотеки)
    elif hasattr(event, 'data') and hasattr(event.data, 'text'):
        user_text = event.data.text
    elif hasattr(event.message, 'text'):
        user_text = event.message.text
    
    # Если текст не найден — сообщаем об ошибке и выходим
    if not user_text:
        await event.message.answer("Не могу прочитать сообщение. Попробуйте написать текстом.")
        return
    
    # --- 2. Уведомляем, что бот начал обработку ---
    # (Чтобы пользователь не ждал в тишине и не думал, что бот завис)
    await event.message.answer("🤔 Думаю над решением...")
    
    # --- 3. Получаем ответ от YandexGPT ---
    answer = await ask_yandexgpt(user_text)
    
    # --- 4. Отправляем ответ пользователю ---
    await event.message.answer(answer)

# ======================== 4. ЗАПУСК БОТА ========================

async def main():
    """Главная асинхронная функция — запускает бесконечный цикл опроса (Long Polling)."""
    await dp.start_polling(bot)

# Точка входа в программу
if __name__ == "__main__":
    asyncio.run(main())
