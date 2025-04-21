# tests/test_indicators.py.   Запуск теста в виртуальной среде: pytest -v tests/test_indicators.py

import pytest
import pandas as pd
from indicators import calculate_indicators

def test_calculate_indicators():
    # Создаем тестовый DataFrame
    data = {
        "timestamp": pd.date_range(start="2023-10-01", periods=30, freq="15min"),  # Увеличено до 30
        "open": [100 + i for i in range(30)],
        "high": [101 + i for i in range(30)],
        "low": [99 + i for i in range(30)],
        "close": [100 + i for i in range(30)],
        "volume": [1000] * 30
    }
    df = pd.DataFrame(data)

    # Вызываем функцию
    result = calculate_indicators(df.copy())

    # Проверки
    assert "bollinger_high" in result.columns
    assert "rsi" in result.columns
    assert "adx" in result.columns
    assert len(result) <= len(df)  # Проверяем удаление NaN
    assert not result[["bollinger_high", "rsi", "adx"]].isna().any().any()

def test_insufficient_data():
    # DataFrame с недостаточным количеством строк
    data = {
        "timestamp": pd.date_range(start="2023-10-01", periods=5, freq="15min"),
        "open": [100] * 5,
        "high": [101] * 5,
        "low": [99] * 5,
        "close": [100] * 5,
        "volume": [1000] * 5
    }
    df = pd.DataFrame(data)

    result = calculate_indicators(df.copy())
    assert len(result) == 5
    assert "bollinger_high" not in result.columns  