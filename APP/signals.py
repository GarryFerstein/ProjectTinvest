# Сигналы

import logging
import pandas as pd

logger = logging.getLogger(__name__)

def generate_signals(df):
    """
    Генерирует торговые сигналы на основе полос Боллинджера и RSI.

    Args:
        df: DataFrame с колонками 'close', 'bollinger_low', 'bollinger_high', 'rsi'.

    Returns:
        DataFrame с добавленными колонками 'buy_signal' и 'sell_signal'.
    """
    
        # Проверка на наличие nan
    if df["bollinger_low"].isnull().any() or df["bollinger_high"].isnull().any():
        print("Ошибка: Недостаточно данных для полос Боллинджера.")
        return df
    if df["rsi"].isnull().any():
        print("Ошибка: Недостаточно данных для RSI.")
        return df

    df["buy_signal"] = False
    df["sell_signal"] = False

    for i in range(3, len(df)):
        # Отладочная информация
        print(
            f"Timestamp: {df.index[i]}, "
            f"Close: {df['close'].iloc[i]:.2f}, "
            f"Bollinger Low: {df['bollinger_low'].iloc[i]:.2f}, "
            f"Bollinger High: {df['bollinger_high'].iloc[i]:.2f}, "
            f"RSI: {df['rsi'].iloc[i]:.2f}"
        )

        # Условие для покупки
        if (
            (df["close"].iloc[i] <= df["bollinger_low"].iloc[i]) and
            (df["close"].iloc[i-1] <= df["bollinger_low"].iloc[i-1]) and
            (df["close"].iloc[i-2] <= df["bollinger_low"].iloc[i-2]) and
            (df["rsi"].iloc[i] < 32)
        ):
            print(f"Сигнал на покупку обнаружен для {df.index[i]}")
            df.loc[df.index[i], "buy_signal"] = True

        # Условие для продажи
        if (
            (df["close"].iloc[i] >= df["bollinger_high"].iloc[i]) and
            (df["close"].iloc[i-1] >= df["bollinger_high"].iloc[i-1]) and
            (df["close"].iloc[i-2] >= df["bollinger_high"].iloc[i-2]) and
            (df["rsi"].iloc[i] > 70)
        ):
            print(f"Сигнал на продажу обнаружен для {df.index[i]}")
            df.loc[df.index[i], "sell_signal"] = True



    for i in range(3, len(df)):  # Начинаем с 3, чтобы был доступ к 3 предыдущим значениям
        # Логика для сигнала на покупку
        if (
            (df["close"].iloc[i] <= df["bollinger_low"].iloc[i]) and
            (df["close"].iloc[i-1] <= df["bollinger_low"].iloc[i-1]) and
            (df["close"].iloc[i-2] <= df["bollinger_low"].iloc[i-2]) and
            (df["rsi"].iloc[i] < 32)
        ):
            df.loc[df.index[i], "buy_signal"] = True

        # Логика для сигнала на продажу
        if (
            (df["close"].iloc[i] >= df["bollinger_high"].iloc[i]) and
            (df["close"].iloc[i-1] >= df["bollinger_high"].iloc[i-1]) and
            (df["close"].iloc[i-2] >= df["bollinger_high"].iloc[i-2]) and
            (df["rsi"].iloc[i] > 65)
        ):
            df.loc[df.index[i], "sell_signal"] = True

        # Логирование для анализа
        logger.debug(
            f"Timestamp: {df.index[i]}, Close: {df['close'][i]}, "
            f"Bollinger Low: {df['bollinger_low'][i]}, Bollinger High: {df['bollinger_high'][i]}, "
            f"RSI: {df['rsi'][i]}, "
            f"Buy Signal: {df['buy_signal'][i]}, Sell Signal: {df['sell_signal'][i]}"
        )

        print(f"Close: {df['close'].iloc[i]}, Bollinger Low: {df['bollinger_low'].iloc[i]}, Bollinger High: {df['bollinger_high'].iloc[i]}, RSI: {df['rsi'].iloc[i]}")
        
    return df

