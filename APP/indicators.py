# Индикаторы

import pandas as pd
from ta.volatility import BollingerBands  # Индикатор Полос Боллинджера
from ta.momentum import RSIIndicator  # Индикатор RSI
from config import BOLLINGER_WINDOW, BOLLINGER_WINDOW_DEV, RSI_WINDOW

def calculate_bollinger_bands(df):
    """
    Рассчитывает Полосы Боллинджера.
    """
    bb_indicator = BollingerBands(
        close=df["close"], 
        window=BOLLINGER_WINDOW, 
        window_dev=BOLLINGER_WINDOW_DEV
    )
    df["bollinger_high"] = bb_indicator.bollinger_hband()
    df["bollinger_low"] = bb_indicator.bollinger_lband()
    df["bollinger_mid"] = bb_indicator.bollinger_mavg()

    # Проверка на наличие nan
    if df["bollinger_high"].isnull().any() or df["bollinger_low"].isnull().any():
        print("Обнаружены пропущенные значения в полосах Боллинджера.")
    return df

def calculate_rsi(df):
    """
    Рассчитывает RSI.
    """
    rsi_indicator = RSIIndicator(
        close=df["close"], 
        window=RSI_WINDOW
    )
    df["rsi"] = rsi_indicator.rsi()

    # Проверка на наличие nan
    if df["rsi"].isnull().any():
        print("Обнаружены пропущенные значения в RSI.")
    return df

def calculate_indicators(df):
    """
    Полный расчет индикаторов (Боллинджер + RSI) для DataFrame.
    Args:
        df: DataFrame с колонками 'open', 'high', 'low', 'close', 'volume'.
    Returns:
        DataFrame с добавленными колонками для индикаторов.
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("Ожидался объект DataFrame, но получен другой тип данных.")

    # Убедимся, что индекс установлен как временной ряд
    if not isinstance(df.index, pd.DatetimeIndex):
        df.set_index("timestamp", inplace=True)
        df.sort_index(inplace=True)

    # Расчет индикаторов
    df = calculate_bollinger_bands(df)
    df = calculate_rsi(df)

    return df