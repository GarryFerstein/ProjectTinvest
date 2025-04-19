# Получение исторических данных

import logging
import time
import csv
from datetime import datetime, timedelta, timezone
from tinkoff.invest import Client, CandleInterval, RequestError
from config import API_TOKEN

# === Конфигурация ===
FIGI = "BBG004S68507"  # Идентификатор инструмента
CANDLE_INTERVAL = CandleInterval.CANDLE_INTERVAL_15_MIN
END_DATE = datetime.utcnow().replace(tzinfo=timezone.utc)  # Текущая дата в UTC
START_DATE = END_DATE - timedelta(days=10)  # 10 дней назад
CSV_FILENAME = "historical_data.csv"
SLEEP_TIME = 2  # Задержка между запросами (сек)
MAX_RETRIES = 3  # Максимальное количество повторных попыток
LIMIT = 200  # Лимит свечей за один запрос (из config.py)

# Словарь для преобразования интервала в timedelta
INTERVAL_TO_DELTA = {
    CandleInterval.CANDLE_INTERVAL_1_MIN: timedelta(minutes=1),
    CandleInterval.CANDLE_INTERVAL_5_MIN: timedelta(minutes=5),
    CandleInterval.CANDLE_INTERVAL_15_MIN: timedelta(minutes=15),
    CandleInterval.CANDLE_INTERVAL_HOUR: timedelta(hours=1),
    CandleInterval.CANDLE_INTERVAL_DAY: timedelta(days=1),
    CandleInterval.CANDLE_INTERVAL_WEEK: timedelta(weeks=1),
    CandleInterval.CANDLE_INTERVAL_MONTH: timedelta(days=30)
}

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def save_to_csv(data, filename):
    """Сохранение данных в CSV с сортировкой по времени."""
    if not data:
        logger.warning(f"Нет данных для сохранения в {filename}")
        return

    data.sort(key=lambda x: x.time)

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "open", "high", "low", "close", "volume"])

        for candle in data:
            writer.writerow([
                candle.time.strftime("%Y-%m-%d %H:%M:%S"),
                candle.open.units + candle.open.nano / 1e9,
                candle.high.units + candle.high.nano / 1e9,
                candle.low.units + candle.low.nano / 1e9,
                candle.close.units + candle.close.nano / 1e9,
                candle.volume
            ])

    logger.info(f"✅ Данные сохранены в {filename}, записано {len(data)} свечей")

def fetch_candles(figi, start_date, end_date, interval, limit=LIMIT):
    """
    Получение исторических свечей с обработкой ошибок.
    """
    with Client(API_TOKEN) as client:
        candles = []
        current_start = start_date
        delta = INTERVAL_TO_DELTA[interval]

        while current_start < end_date:
            try:
                current_end = min(current_start + delta * limit, end_date)
                logger.info(f"🔄 Запрос данных ({figi}) с {current_start} до {current_end}")

                response = client.market_data.get_candles(
                    figi=figi,
                    from_=current_start,
                    to=current_end,
                    interval=interval,
                )
                batch = response.candles

                if not batch:
                    logger.warning(f"⚠️ Нет данных за {current_start} — {current_end}")
                    current_start = current_end  # Сдвигаем на конец окна
                else:
                    candles.extend(batch)
                    current_start = batch[-1].time.replace(tzinfo=timezone.utc) + delta
                    logger.info(f"✅ Получено {len(batch)} свечей")

                time.sleep(SLEEP_TIME)  # Задержка для соблюдения лимитов API

            except RequestError as e:
                logger.error(f"❌ Ошибка API: {e}")
                if "50002" in str(e):
                    logger.error(f"🚫 FIGI {figi} не найден!")
                    return candles
                time.sleep(SLEEP_TIME)
                current_start = current_end  # Пропускаем интервал при ошибке
            except Exception as e:
                logger.error(f"❌ Неизвестная ошибка: {str(e)}")
                time.sleep(SLEEP_TIME)
                current_start = current_end

        return candles

if __name__ == "__main__":
    logger.info(f"🚀 Начало выгрузки данных ({FIGI})")
    candles_data = fetch_candles(FIGI, START_DATE, END_DATE, CANDLE_INTERVAL)
    if candles_data:
        save_to_csv(candles_data, CSV_FILENAME)
        logger.info(f"✅ Завершена выгрузка ({FIGI})")
    else:
        logger.warning(f"⚠️ Данные ({FIGI}) нет.")