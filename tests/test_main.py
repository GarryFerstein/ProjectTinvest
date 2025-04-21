# tests/test_main.py.  Запуск теста в виртуальной среде: pytest -v tests/test_main.py

import pytest
import pandas as pd
from main import check_market_status, process_instrument
from unittest.mock import AsyncMock, patch
from tinkoff.invest import GetTradingStatusResponse
from datetime import datetime

@pytest.mark.asyncio
async def test_check_market_status(mocker):
    # Мокаем datetime.now()
    mock_datetime = mocker.patch("main.datetime")
    mock_datetime.now.return_value = datetime(2025, 4, 17, 10, 0, 0)
    mock_datetime.strftime = datetime.strftime

    mock_service = AsyncMock()
    # Создаем мок для GetTradingStatusResponse с числовым значением trading_status
    mock_response = GetTradingStatusResponse(trading_status=5)  # Соответствует NORMAL_TRADING
    mock_service.get_trading_status.return_value = mock_response
    mock_notifier = AsyncMock()
    mocker.patch("main.telegram_notifier", mock_notifier)

    result = await check_market_status("BBG004S681B4", mock_service)
    assert result is True
    mock_notifier.send_message.assert_called_with(
        "✅ Рынок открылся для NLMK (BBG004S681B4) в 2025-04-17 10:00:00"
    )

@pytest.mark.asyncio
async def test_process_instrument(mocker):
    mock_service = AsyncMock()
    mock_notifier = AsyncMock()
    mocker.patch("main.check_market_status", return_value=True)
    mocker.patch("main.analyze_news", return_value={"summary": "General: Test, Ticker: Test"})
    mocker.patch("main.fetch_market_data", return_value=pd.DataFrame({
        "timestamp": [pd.Timestamp("2023-10-01")],
        "open": [100],
        "high": [101],
        "low": [99],
        "close": [100],
        "volume": [1000]
    }))
    mocker.patch("main.calculate_indicators", return_value=pd.DataFrame({
        "timestamp": [pd.Timestamp("2023-10-01")],
        "close": [100],
        "bollinger_low": [99],
        "rsi": [30],
        "buy_signal": [True]
    }))
    mocker.patch("main.generate_signals", return_value=pd.DataFrame({
        "timestamp": [pd.Timestamp("2023-10-01")],
        "close": [100],
        "buy_signal": [True]
    }).set_index("timestamp"))
    mocker.patch("main.telegram_notifier", mock_notifier)

    await process_instrument("BBG004S681B4", "NLMK", mock_service)
    mock_notifier.send_message.assert_called_with(
        "🟢 Сигнал на покупку: NLMK (BBG004S681B4) по цене 100.00 RUB в 2023-10-01 00:00:00\n"
        "Новости:\n"
        "Общий рынок: General: Test\n"
        "NLMK: Ticker: Test"
    )
