# tests/test_signals.py.  Запуск теста в виртуальной среде: pytest -v tests/test_signals.py

import pytest
import pandas as pd
from signals import generate_signals

def test_full_buy_signal_and_profit_take_long():
    data = {
        "timestamp": pd.date_range(start="2023-10-01", periods=10, freq="15min"),
        "open":  [100, 100, 100, 100, 100, 100, 100, 100, 100, 100],
        "high":  [101, 101, 101, 101, 101, 105, 105, 105, 105, 105],
        "low":   [99,  99,  99,  99,  99,  99,  99,  99,  99,  99],
        "close": [98,  98,  98,  100, 102, 106, 106, 106, 106, 106],  # 3 подряд ниже bollinger_low
        "bollinger_low": [99] * 10,
        "bollinger_high": [110] * 10,
        "rsi": [30, 30, 30, 35, 40, 45, 50, 55, 60, 60],
        "plus_di": [10, 10, 10, 10, 10, 20, 30, 40, 40, 40],
        "minus_di": [40, 40, 40, 30, 25, 20, 15, 10, 10, 10]
    }
    df = pd.DataFrame(data)
    result = generate_signals(df.copy())

    # Сигнал на покупку должен быть на 3-й свече
    assert result["buy_signal"].iloc[2]
    assert not result["sell_signal"].any()

    # Должна быть фиксация прибыли после входа (DMI cross или пробитие верхней полосы)
    assert result["profit_take_long"].any()

def test_full_sell_signal_and_profit_take_short():
    data = {
        "timestamp": pd.date_range(start="2023-10-02", periods=10, freq="15min"),
        "open":  [110, 110, 110, 110, 110, 110, 110, 110, 110, 110],
        "high":  [111, 111, 111, 111, 111, 111, 111, 111, 111, 111],
        "low":   [109, 109, 109, 109, 109, 105, 104, 103, 102, 102],
        "close": [112, 112, 112, 110, 108, 104, 103, 102, 101, 100],  # 3 подряд выше bollinger_high
        "bollinger_low": [90] * 10,
        "bollinger_high": [111] * 10,
        "rsi": [70, 70, 70, 68, 65, 60, 55, 50, 45, 40],
        "plus_di": [40, 40, 40, 40, 40, 30, 20, 10, 10, 10],
        "minus_di": [10, 10, 10, 10, 10, 20, 30, 40, 40, 40]
    }
    df = pd.DataFrame(data)
    result = generate_signals(df.copy())

    # Сигнал на продажу должен быть на 2-й свече (0,1,2 выше верхней полосы + RSI > 65)
    assert result["sell_signal"].iloc[2]
    assert not result["buy_signal"].any()

    # Должна быть фиксация прибыли после входа в short (пересечение DMI или пробитие нижней полосы)
    assert result["profit_take_short"].any()
