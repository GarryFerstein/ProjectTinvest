# tests/test_config.py.   Запуск теста в виртуальной среде: pytest -v tests/test_config.py

import os
import pytest
from unittest.mock import patch
from config import API_TOKEN, ACCOUNT_ID, NEWSAPI_KEY, NAME, FIGI_TO_TICKER, LIMIT, TIMEFRAME

def test_config_env_loading(monkeypatch):
    # Устанавливаем временные переменные окружения
    monkeypatch.setenv("TINKOFF_TOKEN", "Твой API-токен")
    monkeypatch.setenv("ACCOUNT_ID", "Твой ID")
    monkeypatch.setenv("NEWSAPI_KEY", "Твой API-ключ")
    
    # Перезагружаем модуль config для применения новых переменных
    import importlib
    import config
    importlib.reload(config)
    
    assert config.API_TOKEN == "Твой API-токен"
    assert config.ACCOUNT_ID == "Твой ID"
    assert config.NEWSAPI_KEY == "Твой API-ключ"

def test_config_defaults():
    assert NAME == "Торговый бот с биржей через API Т-Инвестиции"
    assert LIMIT == 100
    assert TIMEFRAME == "15m"

def test_figi_to_ticker():
    assert "BBG004S681B4" in FIGI_TO_TICKER
    assert FIGI_TO_TICKER["BBG004S681B4"] == "NLMK"
    assert len(FIGI_TO_TICKER) == 10
