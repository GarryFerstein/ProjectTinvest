# Конфигурационный файл

from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# Токен API Тинькофф Инвестиций
API_TOKEN = os.getenv("TINKOFF_TOKEN")
ACCOUNT_ID = os.getenv("ACCOUNT_ID")  # ID брокерского счета

# Токен API новостного агрегатора NewsAPI
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Основная информация
NAME = os.getenv("NAME", "Торговый бот с биржей через API Т-Инвестиции")

# Telegram-бот (для уведомлений)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Список FIGI и их тикеры
FIGI_TO_TICKER = {
    "BBG004S68614": "AFKS",   # АФК Система
    "BBG004S68B31": "ALRS",   # Европлан
    "BBG004S68507": "MAGN",   # Магнитогорский металлургический комбинат
    "BBG004S68598": "MTLR",   # Мечел
    "BBG004S682Z6": "RTKM",   # Ростелеком
    "BBG008F2T3T2": "RUAL",   # Русал
    "BBG004S681W1": "MTSS",   # МТС
    "BBG004730ZJ9": "VTBR",   # ВТБ
    "TCS00A109B25": "OZPH",   # Озон Фармацевтика
    "BBG0063FKTD9": "LENT"    # Лента
}

# Таймфрейм и лимиты данных
TIMEFRAME = "15m"  # Таймфрейм для анализа
LIMIT = int(os.getenv("LIMIT", 100))  # Количество свечей для анализа
TIMEOUT = int(os.getenv("TIMEOUT", 30))  # Задержка между циклами в секундах

# Параметры индикаторов
BOLLINGER_WINDOW = int(os.getenv("BOLLINGER_WINDOW", 14))
BOLLINGER_WINDOW_DEV = int(os.getenv("BOLLINGER_WINDOW_DEV", 2))
RSI_WINDOW = int(os.getenv("RSI_WINDOW", 9))
ADX_WINDOW = int(os.getenv("ADX_WINDOW", 14))
