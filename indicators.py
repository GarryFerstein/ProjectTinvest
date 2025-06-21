# Индикаторы

import pandas as pd
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator
from ta.trend import ADXIndicator
from config import BOLLINGER_WINDOW, BOLLINGER_WINDOW_DEV, RSI_WINDOW, ADX_WINDOW  
import logging

logger = logging.getLogger(__name__)

def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Ожидался объект DataFrame, но получен другой тип данных.")
   
    if not isinstance(df.index, pd.DatetimeIndex):
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

    # Проверка минимального количества данных
    min_required = max(BOLLINGER_WINDOW, RSI_WINDOW, 2 * ADX_WINDOW + 1)  
    if len(df) < min_required:
        logger.warning(f"Недостаточно данных для расчета индикаторов: {len(df)} свечей, требуется минимум {min_required}")
        return df

    # Полосы Боллинджера
    bb_indicator = BollingerBands(close=df["close"], window=BOLLINGER_WINDOW, window_dev=BOLLINGER_WINDOW_DEV)
    df["bollinger_high"] = bb_indicator.bollinger_hband()
    df["bollinger_low"] = bb_indicator.bollinger_lband()
    df["bollinger_mid"] = bb_indicator.bollinger_mavg()

    # RSI
    rsi_indicator = RSIIndicator(close=df["close"], window=RSI_WINDOW)
    df["rsi"] = rsi_indicator.rsi()

    # ADX, +DMI, -DMI
    adx_indicator = ADXIndicator(high=df["high"], low=df["low"], close=df["close"], window=ADX_WINDOW)
    df["adx"] = adx_indicator.adx()
    df["plus_di"] = adx_indicator.adx_pos()  # +DMI
    df["minus_di"] = adx_indicator.adx_neg()  # -DMI

    # Удаление строк с NaN после расчета индикаторов
    initial_len = len(df)
    df.dropna(subset=["bollinger_high", "bollinger_low", "bollinger_mid", "rsi", "adx", "plus_di", "minus_di"], inplace=True)
    if len(df) < initial_len:
        logger.info(f"Удалено {initial_len - len(df)} строк с пропущенными значениями индикаторов")

    return df
