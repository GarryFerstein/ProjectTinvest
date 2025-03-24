# Получение исторических данных

import logging
import time
import csv
from datetime import datetime, timedelta, timezone
from tinkoff.invest import Client, CandleInterval, RequestError
import os

# === Конфигурация ===
API_TOKEN = os.getenv("TINKOFF_TOKEN")
FIGI = "BBG004730N88" # На примере Сбербанка
INTERVAL = CandleInterval.CANDLE_INTERVAL_15_MIN
START_DATE = "2025-01-01 00:00:00"
END_DATE = "2025-01-30 23:59:59"
LIMIT = 1000
CSV_FILENAME = "historical_data.csv"
SLEEP_TIME = 2  # Увеличенная задержка в секундах
MAX_RETRIES = 3  # Максимальное количество повторных попыток

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

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def save_to_csv(data, filename):
    """Сохранение данных в CSV с сортировкой по времени."""
    data.sort(key=lambda x: x.time)

    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["datetime", "open", "high", "low", "close", "volume"])

        for candle in data:
            writer.writerow([
                candle.time.strftime("%Y-%m-%d %H:%M:%S"),
                candle.open.units + candle.open.nano / 1e9,
                candle.high.units + candle.high.nano / 1e9,
                candle.low.units + candle.low.nano / 1e9,
                candle.close.units + candle.close.nano / 1e9,
                candle.volume
            ])

    logging.info(f"✅ Данные сохранены в {filename}")

def fetch_candles(figi, start_date, end_date, interval):
    """
    Получение исторических свечей с обработкой зависания.
    """
    with Client(API_TOKEN) as client:
        candles = []
        current_start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        end_date = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        retries = 0

        while current_start < end_date:
            try:
                current_end = min(current_start + timedelta(minutes=LIMIT * 15), end_date)
                logging.info(f"🔄 Запрос данных для {figi} с {current_start} до {current_end}")

                response = client.market_data.get_candles(
                    figi=figi,
                    from_=current_start,
                    to=current_end,
                    interval=interval,
                )
                batch = response.candles

                if not batch:
                    retries += 1
                    logging.warning(f"⚠️ Нет данных за {current_start} — {current_end}. Попытка {retries}/{MAX_RETRIES}")

                    if retries >= MAX_RETRIES:
                        logging.error(f"🚫 Пропускаем интервал {current_start} — {current_end} после {MAX_RETRIES} неудачных попыток.")
                        current_start = current_end
                        retries = 0
                    else:
                        logging.info(f"⏳ Ожидание {SLEEP_TIME} сек перед повторной попыткой...")
                        time.sleep(SLEEP_TIME)
                    continue

                candles.extend(batch)
                # Обновляем current_start на время последней свечи + интервал
                current_start = batch[-1].time.replace(tzinfo=timezone.utc) + INTERVAL_TO_DELTA[interval]
                retries = 0

                logging.info(f"⏳ Ожидание {SLEEP_TIME} сек перед следующим запросом...")
                time.sleep(SLEEP_TIME)

            except RequestError as e:
                logging.error(f"❌ Ошибка API: {e}")

                if "50002" in str(e):
                    logging.error(f"🚫 FIGI {figi} не найден! Завершаем работу.")
                    break

                logging.info(f"🔄 Повторный запрос через {SLEEP_TIME} секунд...")
                time.sleep(SLEEP_TIME)

        return candles

if __name__ == "__main__":
    candles_data = fetch_candles(FIGI, START_DATE, END_DATE, INTERVAL)

    if candles_data:
        save_to_csv(candles_data, CSV_FILENAME)
        logging.info(f"✅ Загружено {len(candles_data)} свечей для FIGI: {FIGI}.")
    else:
        logging.warning(f"⚠️ Данных для FIGI {FIGI} нет.")