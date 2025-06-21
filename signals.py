# Сигналы

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def has_dmi_cross(df, i, window=5, cross_type="bullish"):
    start_idx = max(0, i - window)
    dmi_df = df.iloc[start_idx:i+1]

    if cross_type == "bullish":
        return ((dmi_df['plus_di'] > dmi_df['minus_di']) &
                (dmi_df['plus_di'].shift(1) <= dmi_df['minus_di'].shift(1))).any()
    elif cross_type == "bearish":
        return ((dmi_df['minus_di'] > dmi_df['plus_di']) &
                (dmi_df['minus_di'].shift(1) <= dmi_df['plus_di'].shift(1))).any()
    else:
        return False


def generate_signals(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = ["close", "bollinger_low", "bollinger_high", "rsi", "plus_di", "minus_di", "high", "low", "open"]
    if not all(col in df.columns for col in required_cols):
        logger.error("Отсутствуют необходимые колонки для генерации сигналов")
        return df
    # Колонки для сигналов
    df = df.copy()
    df["buy_signal"] = False
    df["sell_signal"] = False
    df["profit_take_long"] = False
    df["profit_take_short"] = False
    df["stop_loss"] = False  
    df["position"] = None
    df["entry_price"] = float('nan')  # Цена входа в позицию

    # === УСЛОВИЕ ДЛЯ ПОКУПКИ (long) ===
    for i in range(len(df)):
        if i < 2:
            continue

        current_close = df.loc[df.index[i], "close"]
        prev1_close = df.loc[df.index[i-1], "close"]
        prev2_close = df.loc[df.index[i-2], "close"]

        bollinger_low_condition = (
            current_close <= df.loc[df.index[i], "bollinger_low"] and
            prev1_close <= df.loc[df.index[i-1], "bollinger_low"] and
            prev2_close <= df.loc[df.index[i-2], "bollinger_low"]
        )

        rsi_condition = df.loc[df.index[i], "rsi"] < 32

        red_candles_condition = (
            current_close < df.loc[df.index[i], "open"] and
            prev1_close < df.loc[df.index[i-1], "open"] and
            prev2_close < df.loc[df.index[i-2], "open"]
        )

        dmi_bullish_cross = has_dmi_cross(df, i, window=5, cross_type="bullish")

        df.loc[df.index[i], "buy_signal"] = (
            bollinger_low_condition and
            rsi_condition and
            red_candles_condition and
            dmi_bullish_cross
        )

    # === УСЛОВИЕ ДЛЯ ПРОДАЖИ (short) ===
    for i in range(len(df)):
        if i < 2:
            continue

        current_close = df.loc[df.index[i], "close"]
        prev1_close = df.loc[df.index[i-1], "close"]
        prev2_close = df.loc[df.index[i-2], "close"]

        bollinger_high_condition = (
            current_close >= df.loc[df.index[i], "bollinger_high"] and
            prev1_close >= df.loc[df.index[i-1], "bollinger_high"] and
            prev2_close >= df.loc[df.index[i-2], "bollinger_high"]
        )

        rsi_condition = df.loc[df.index[i], "rsi"] > 65

        green_candles_condition = (
            current_close > df.loc[df.index[i], "open"] and
            prev1_close > df.loc[df.index[i-1], "open"] and
            prev2_close > df.loc[df.index[i-2], "open"]
        )

        dmi_bearish_cross = has_dmi_cross(df, i, window=5, cross_type="bearish")

        df.loc[df.index[i], "sell_signal"] = (
            bollinger_high_condition and
            rsi_condition and
            green_candles_condition and
            dmi_bearish_cross
        )

    # === ЛОГИКА УПРАВЛЕНИЯ ПОЗИЦИЕЙ И ФИКСАЦИИ ПРИБЫЛИ ===
    position = None
    entry_price = float('nan')

    for i in range(1, len(df)):
        current_index = df.index[i]
        prev_position = df["position"].iloc[i-1]

        if position is None:
            if df["buy_signal"].iloc[i]:
                position = "long"
                entry_price = df["close"].iloc[i]
            elif df["sell_signal"].iloc[i]:
                position = "short"
                entry_price = df["close"].iloc[i]
        else:
            position = prev_position

        df.loc[current_index, "position"] = position
        df.loc[current_index, "entry_price"] = entry_price

        # Фиксация прибыли для long позиции
        if position == "long" and not df["profit_take_long"].iloc[:i].any():
            green_candle_cross = (
                (df["close"].iloc[i] > df["open"].iloc[i]) &
                (df["high"].iloc[i] >= df["bollinger_high"].iloc[i])
            )
            df.loc[current_index, "profit_take_long"] = green_candle_cross

            if df["profit_take_long"].iloc[i]:
                position = None
                entry_price = float('nan')

        # Фиксация прибыли для short позиции
        elif position == "short" and not df["profit_take_short"].iloc[:i].any():
            red_candle_cross = (
                (df["close"].iloc[i] < df["open"].iloc[i]) &
                (df["low"].iloc[i] <= df["bollinger_low"].iloc[i])
            )
            df.loc[current_index, "profit_take_short"] = red_candle_cross

            if df["profit_take_short"].iloc[i]:
                position = None
                entry_price = float('nan')

        # Стоп-лосс для long позиции (падение больше 1% от точки входа)
        if position == "long" and not df["stop_loss"].iloc[:i].any() and not pd.isna(entry_price):
            price_drop_percent = (df["close"].iloc[i] - entry_price) / entry_price * 100
            if price_drop_percent <= -1.0:      # Здесь можно менять процент стоп-лосса
                df.loc[current_index, "stop_loss"] = True
                position = None
                entry_price = float('nan')
                logger.info(
                    f"Стоп-лосс (long): Timestamp: {current_index}, "
                    f"Entry Price: {entry_price:.2f}, Current Close: {df['close'].iloc[i]:.2f}"
                )

        # Стоп-лосс для short позиции (рост больше 1% от точки входа)
        elif position == "short" and not df["stop_loss"].iloc[:i].any() and not pd.isna(entry_price):
            price_rise_percent = (entry_price - df["close"].iloc[i]) / entry_price * 100
            if price_rise_percent >= 1.0:    # Здесь можно менять процент стоп-лосса
                df.loc[current_index, "stop_loss"] = True
                position = None
                entry_price = float('nan')
                logger.info(
                    f"Стоп-лосс (short): Timestamp: {current_index}, "
                    f"Entry Price: {entry_price:.2f}, Current Close: {df['close'].iloc[i]:.2f}"
                )

        df.loc[current_index, "position"] = position

    # === ЛОГИРОВАНИЕ СИГНАЛОВ ===
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
        elif row["stop_loss"]:
            logger.info(
                f"Сработал стоп-лосс: Timestamp: {index}, Close: {row['close']:.2f}, "
                f"Position: {row['position']}, Entry Price: {row['entry_price']:.2f}"
            )
            signals_detected = True

    if not signals_detected:
        logger.info("Сигналы не обнаружены в текущем наборе данных")

    return df