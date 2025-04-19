# Получение рыночных данных

from tinkoff.invest import AsyncClient, CandleInterval
import pandas as pd
from datetime import datetime, timedelta
from config import API_TOKEN, FIGI_TO_TICKER, TIMEFRAME, LIMIT
import logging

logger = logging.getLogger(__name__)

INTERVAL_DURATION = {
    "1m": 1, "5m": 5, "15m": 15, "1h": 60, "1d": 1440,
}

INTERVAL_MAPPING = {
    "1m": CandleInterval.CANDLE_INTERVAL_1_MIN,
    "5m": CandleInterval.CANDLE_INTERVAL_5_MIN,
    "15m": CandleInterval.CANDLE_INTERVAL_15_MIN,
    "1h": CandleInterval.CANDLE_INTERVAL_HOUR,
    "1d": CandleInterval.CANDLE_INTERVAL_DAY,
}

CANDLE_INTERVAL = INTERVAL_MAPPING.get(TIMEFRAME, CandleInterval.CANDLE_INTERVAL_15_MIN)
INTERVAL_MINUTES = INTERVAL_DURATION.get(TIMEFRAME, 15)

async def fetch_market_data(figi, interval=CANDLE_INTERVAL, limit=LIMIT):
    try:
        async with AsyncClient(API_TOKEN) as client:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=limit * INTERVAL_MINUTES)
            ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
            logger.info(f"Запрос данных для {ticker} ({figi}): {start_time} - {end_time}")
            candles = (await client.market_data.get_candles(
                figi=figi,
                from_=start_time,
                to=end_time,
                interval=interval
            )).candles

            df = pd.DataFrame([{
                "timestamp": candle.time,
                "open": candle.open.units + candle.open.nano / 1e9,
                "high": candle.high.units + candle.high.nano / 1e9,
                "low": candle.low.units + candle.low.nano / 1e9,
                "close": candle.close.units + candle.close.nano / 1e9,
                "volume": candle.volume
            } for candle in candles])
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            logger.info(f"Получено {len(df)} свечей для {ticker}")
            print(f"Получено {len(df)} свечей для {ticker} ({figi})")  
            return df
    except Exception as e:
        logger.error(f"Ошибка для FIGI {figi}: {str(e)}")
        print(f"Ошибка для FIGI {figi}: {str(e)}")  
        return None

async def fetch_all_market_data():
    market_data = {}
    for figi, ticker in FIGI_TO_TICKER.items():
        logger.info(f"Обработка инструмента: {ticker} ({figi})")
        data = await fetch_market_data(figi)
        if data is not None and not data.empty:
            market_data[figi] = data
        else:
            logger.warning(f"Не удалось получить данные для {ticker}")
    return market_data
