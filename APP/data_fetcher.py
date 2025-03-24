# Получение рыночных данных

from tinkoff.invest import Client, CandleInterval
import pandas as pd
from datetime import datetime, timedelta
from config import API_TOKEN, FIGI_TO_TICKER, TIMEFRAME, LIMIT

# Определение длительности интервалов в минутах
INTERVAL_DURATION = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "1d": 1440,
}

# Маппинг интервалов свечей
INTERVAL_MAPPING = {
    "1m": CandleInterval.CANDLE_INTERVAL_1_MIN,
    "5m": CandleInterval.CANDLE_INTERVAL_5_MIN,
    "15m": CandleInterval.CANDLE_INTERVAL_15_MIN,
    "1h": CandleInterval.CANDLE_INTERVAL_HOUR,
    "1d": CandleInterval.CANDLE_INTERVAL_DAY,
}

# Получаем прототип интервала и его длительность
CANDLE_INTERVAL = INTERVAL_MAPPING.get(TIMEFRAME, CandleInterval.CANDLE_INTERVAL_15_MIN)
INTERVAL_MINUTES = INTERVAL_DURATION.get(TIMEFRAME, 15)

def fetch_market_data(figi, interval=CANDLE_INTERVAL, limit=LIMIT):
    """Получение рыночных данных с выводом в терминал."""
    try:
        with Client(API_TOKEN) as client:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=limit * INTERVAL_MINUTES)
            ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
            print(f"Запрос данных для {ticker} ({figi}):")
            print(f"Период: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}")
            print(f"Интервал: {TIMEFRAME}, Количество свечей: {limit}")
            candles = client.market_data.get_candles(
                figi=figi,
                from_=start_time,
                to=end_time,
                interval=interval
            ).candles

            # Преобразование данных в DataFrame
            df = pd.DataFrame([{
                "timestamp": candle.time,
                "open": candle.open.units + candle.open.nano / 1e9,
                "high": candle.high.units + candle.high.nano / 1e9,
                "low": candle.low.units + candle.low.nano / 1e9,
                "close": candle.close.units + candle.close.nano / 1e9,
                "volume": candle.volume
            } for candle in candles])
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Вывод первых 5 строк в терминал
            print("Полученные данные:")
            print(df.head().to_string(index=False))
            print("-" * 50)
            return df
    except Exception as e:
        print(f"Ошибка для FIGI {figi}: {str(e)}")
        return None

def fetch_all_market_data():
    """Получение данных для всех инструментов с выводом статуса."""
    market_data = {}
    for figi, ticker in FIGI_TO_TICKER.items():
        print(f"\n{'=' * 30}")
        print(f"Обработка инструмента: {ticker} ({figi})")
        data = fetch_market_data(figi)
        if data is not None and not data.empty:
            market_data[figi] = data
            print(f"Успешно получено {len(data)} свечей")
        else:
            print(f"Не удалось получить данные для {ticker}")
    return market_data