# Бэктестинг

import pandas as pd
from indicators import calculate_bollinger_bands, calculate_rsi
from signals import generate_signals

def load_historical_data(filename="historical_data.csv"):
    """Загружает исторические данные."""
    try:
        df = pd.read_csv(filename)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
        df.sort_index(inplace=True)
        return df
    except Exception as e:
        print(f"Ошибка при загрузке данных: {e}")
        return None

def add_indicators(df):
    """Добавляет индикаторы к данным."""
    df = calculate_bollinger_bands(df)
    df = calculate_rsi(df)
    return df

def backtest_strategy(df):
    """Генерирует сигналы."""
    df = generate_signals(df)
    return df

def evaluate_backtest(df):
    """Оценивает результаты бэктестинга."""
    buy_signals = df[df["buy_signal"]]
    sell_signals = df[df["sell_signal"]]

    profit = 0
    for buy_time, buy_row in buy_signals.iterrows():
        sell_row = sell_signals[sell_signals.index > buy_time].iloc[0] if not sell_signals.empty else None
        if sell_row is not None:
            profit += sell_row["close"] - buy_row["close"]

    metrics = {
        "total_trades": len(buy_signals),
        "profit": profit,
        "buy_signals": buy_signals.index.tolist(),
        "sell_signals": sell_signals.index.tolist(),
    }
    return metrics

if __name__ == "__main__":
    # Шаг 1: Загрузка данных
    df = load_historical_data()
    if df is None or df.empty:
        print("Нет данных для бэктестинга.")
        exit()

    # Шаг 2: Добавление индикаторов
    df = add_indicators(df)

    # Шаг 3: Генерация сигналов
    df = backtest_strategy(df)

    # Шаг 4: Оценка результатов
    metrics = evaluate_backtest(df)
    print("Результаты бэктестинга:")
    print(f"Общее количество сделок: {metrics['total_trades']}")
    print(f"Общая прибыль: {metrics['profit']:.2f}")
    print(f"Моменты покупки: {metrics['buy_signals']}")
    print(f"Моменты продажи: {metrics['sell_signals']}")