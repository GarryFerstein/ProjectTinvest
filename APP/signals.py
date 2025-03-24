# Сигналы

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    # Проверка наличия необходимых колонок
    required_cols = ["close", "bollinger_low", "bollinger_high", "rsi"]
    if not all(col in df.columns for col in required_cols):
        logger.error("Отсутствуют необходимые колонки для генерации сигналов")
        return df

    # Инициализация колонок сигналов
    df["buy_signal"] = (
        (df["close"] <= df["bollinger_low"]) &
        (df["close"].shift(1) <= df["bollinger_low"].shift(1)) &
        (df["close"].shift(2) <= df["bollinger_low"].shift(2)) &
        (df["rsi"] < 32)
    )
    df["sell_signal"] = (
        (df["close"] >= df["bollinger_high"]) &
        (df["close"].shift(1) >= df["bollinger_high"].shift(1)) &
        (df["close"].shift(2) >= df["bollinger_high"].shift(2)) &
        (df["rsi"] > 65)
    )

    # Логирование сигналов
    signals_detected = False
    for index, row in df.iterrows():
        if row["buy_signal"]:
            logger.info(
                f"Сигнал на покупку: Timestamp: {index}, Close: {row['close']:.2f}, "
                f"Bollinger Low: {row['bollinger_low']:.2f}, RSI: {row['rsi']:.2f}"
            )
            signals_detected = True
        elif row["sell_signal"]:
            logger.info(
                f"Сигнал на продажу: Timestamp: {index}, Close: {row['close']:.2f}, "
                f"Bollinger High: {row['bollinger_high']:.2f}, RSI: {row['rsi']:.2f}"
            )
            signals_detected = True

    if not signals_detected:
        logger.info("Сигналы не обнаружены в текущем наборе данных")

    return df