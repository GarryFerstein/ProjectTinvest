# Основной файл запуска торгового бота

import asyncio
import logging
import sys
from datetime import datetime
from tinkoff.invest import AsyncClient
from telegram_notifier import TelegramNotifier
from data_fetcher import fetch_market_data
from indicators import calculate_indicators
from signals import generate_signals
from config import API_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, FIGI_TO_TICKER, TIMEOUT

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Инициализация Telegram-уведомлений
telegram_notifier = TelegramNotifier(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

# Хранилище для запомненных сигналов (ключ: (figi, timestamp, тип_сигнала))
sent_signals = set()

async def check_market_status(figi, market_data_service):
    try:
        trading_status_response = await market_data_service.get_trading_status(figi=figi)
        ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
        if trading_status_response.trading_status == 5:  # INSTRUMENT_STATUS_NORMAL_TRADING
            print(f"Рынок открыт для {ticker} ({figi})")
            return True
        else:
            await telegram_notifier.send_message(
                f"⚠️ Рынок закрыт для инструмента {ticker} ({figi}). Торговля невозможна."
            )
            return False
    except Exception as e:
        ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
        await telegram_notifier.send_message(
            f"❌ Ошибка при проверке статуса рынка для {ticker} ({figi}): {e}"
        )
        return False

async def process_instrument(figi, ticker, market_data_service):
    print(f"Обработка инструмента: {ticker} ({figi})")
    is_market_open = await check_market_status(figi, market_data_service)
    if not is_market_open:
        return

    df = await fetch_market_data(figi)
    if df is None or df.empty:
        await telegram_notifier.send_message(
            f"⚠️ Нет данных для инструмента {ticker} ({figi})."
        )
        return

    try:
        df = calculate_indicators(df)
    except ValueError as e:
        await telegram_notifier.send_message(
            f"❌ Ошибка при расчете индикаторов для {ticker} ({figi}): {e}"
        )
        return

    signals_df = generate_signals(df)
    if "buy_signal" in signals_df.columns and signals_df["buy_signal"].any():
        buy_signals = signals_df[signals_df["buy_signal"]]
        for timestamp, row in buy_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "buy")
            if signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                await telegram_notifier.send_message(
                    f"🟢 Сигнал на покупку: {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}"
                )
                sent_signals.add(signal_key)

    if "sell_signal" in signals_df.columns and signals_df["sell_signal"].any():
        sell_signals = signals_df[signals_df["sell_signal"]]
        for timestamp, row in sell_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "sell")
            if signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                await telegram_notifier.send_message(
                    f"🔴 Сигнал на продажу: {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}"
                )
                sent_signals.add(signal_key)

async def main():
    # Уведомление о старте бота
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await telegram_notifier.send_message(f"🚀 Бот запущен в {start_time}")
    print(f"Бот запущен в {start_time}")

    async with AsyncClient(API_TOKEN) as client:
        market_data_service = client.market_data
        try:
            while True:
                tasks = [
                    process_instrument(figi, ticker, market_data_service)
                    for figi, ticker in FIGI_TO_TICKER.items()
                ]
                await asyncio.gather(*tasks)
                print(f"Цикл завершен. Ожидание {TIMEOUT} секунд перед следующим запуском...")
                await asyncio.sleep(TIMEOUT)
        except asyncio.CancelledError:
            stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await telegram_notifier.send_message(f"🛑 Бот остановлен пользователем в {stop_time}")
            print(f"Бот остановлен в {stop_time}")
        except Exception as e:
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await telegram_notifier.send_message(f"❌ Бот завершил работу с ошибкой в {error_time}: {str(e)}")
            print(f"Ошибка: {str(e)}")
            raise

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        loop.run_until_complete(
            telegram_notifier.send_message(f"🛑 Бот остановлен пользователем в {stop_time}")
        )
        print(f"Бот остановлен в {stop_time}")
        loop.close()
    except Exception as e:
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        loop.run_until_complete(
            telegram_notifier.send_message(f"❌ Критическая ошибка при запуске бота в {stop_time}: {str(e)}")
        )
        print(f"Критическая ошибка: {str(e)}")
        loop.close()
        sys.exit(1)