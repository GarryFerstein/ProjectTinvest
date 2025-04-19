# Сигналы

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    # Проверка наличия необходимых колонок
    required_cols = ["close", "bollinger_low", "bollinger_high", "rsi", "plus_di", "minus_di", "high", "low", "open"]
    if not all(col in df.columns for col in required_cols):
        logger.error("Отсутствуют необходимые колонки для генерации сигналов")
        return df

    # Инициализация колонок сигналов
    df["buy_signal"] = False
    df["sell_signal"] = False
    df["profit_take_long"] = False
    df["profit_take_short"] = False
    df["position"] = None

    # Условия для покупки (три свечи подряд)
    df["buy_signal"] = (
        (df["close"] <= df["bollinger_low"]) &
        (df["close"].shift(1) <= df["bollinger_low"].shift(1)) &
        (df["close"].shift(2) <= df["bollinger_low"].shift(2)) &
        (df["rsi"] < 32)
    )

    # Условия для продажи (три свечи подряд)
    df["sell_signal"] = (
        (df["close"] >= df["bollinger_high"]) &
        (df["close"].shift(1) >= df["bollinger_high"].shift(1)) &
        (df["close"].shift(2) >= df["bollinger_high"].shift(2)) &
        (df["rsi"] > 65)
    )

    # Определение позиции и фиксации прибыли
    position = None
    for i in range(1, len(df)):
        current_index = df.index[i]
        prev_position = df["position"].iloc[i-1]

        # Открытие позиции, если нет текущей позиции
        if position is None:
            if df["buy_signal"].iloc[i] and prev_position != "long":
                position = "long"
            elif df["sell_signal"].iloc[i] and prev_position != "short":
                position = "short"
        else:
            position = prev_position

        df.loc[current_index, "position"] = position

        # Фиксация прибыли для long позиции
        if position == "long" and not df["profit_take_long"].iloc[:i].any():
            # Условие 1: Пересечение +DMI и -DMI
            dmi_cross = (
                (df["plus_di"].iloc[i] > df["minus_di"].iloc[i]) &
                (df["plus_di"].iloc[i-1] <= df["minus_di"].iloc[i-1])
            )
            # Условие 2: Зеленая свеча пересекает верхнюю полосу Боллинджера
            green_candle_cross = (
                (df["close"].iloc[i] > df["open"].iloc[i]) &  # Зеленая свеча
                (df["high"].iloc[i] >= df["bollinger_high"].iloc[i])
            )
            df.loc[current_index, "profit_take_long"] = dmi_cross | green_candle_cross
            if df["profit_take_long"].iloc[i]:
                position = None  # Сбрасываем позицию после фиксации

        # Фиксация прибыли для short позиции
        elif position == "short" and not df["profit_take_short"].iloc[:i].any():
            # Условие 1: Пересечение +DMI и -DMI
            dmi_cross = (
                (df["minus_di"].iloc[i] > df["plus_di"].iloc[i]) &
                (df["minus_di"].iloc[i-1] <= df["plus_di"].iloc[i-1])
            )
            # Условие 2: Красная свеча пересекает нижнюю полосу Боллинджера
            red_candle_cross = (
                (df["close"].iloc[i] < df["open"].iloc[i]) &  # Красная свеча
                (df["low"].iloc[i] <= df["bollinger_low"].iloc[i])
            )
            df.loc[current_index, "profit_take_short"] = dmi_cross | red_candle_cross
            if df["profit_take_short"].iloc[i]:
                position = None  # Сбрасываем позицию после фиксации

        # Обновляем позицию после проверки фиксации
        df.loc[current_index, "position"] = position

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
        elif row["profit_take_long"]:
            logger.info(
                f"Фиксация прибыли (long): Timestamp: {index}, Close: {row['close']:.2f}, "
                f"+DMI: {row['plus_di']:.2f}, -DMI: {row['minus_di']:.2f}, "
                f"High: {row['high']:.2f}, Bollinger High: {row['bollinger_high']:.2f}"
            )
            signals_detected = True
        elif row["profit_take_short"]:
            logger.info(
                f"Фиксация прибыли (short): Timestamp: {index}, Close: {row['close']:.2f}, "
                f"+DMI: {row['plus_di']:.2f}, -DMI: {row['minus_di']:.2f}, "
                f"Low: {row['low']:.2f}, Bollinger Low: {row['bollinger_low']:.2f}"
            )
            signals_detected = True

    if not signals_detected:
        logger.info("Сигналы не обнаружены в текущем наборе данных")

    return df
