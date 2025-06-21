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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

telegram_notifier = TelegramNotifier(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
sent_signals = set()
market_status_history = {figi: None for figi in FIGI_TO_TICKER.keys()}
active_positions = {}

async def check_market_status(figi, market_data_service):
    try:
        trading_status_response = await market_data_service.get_trading_status(figi=figi)
        ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        is_open = trading_status_response.trading_status == 5

        previous_status = market_status_history[figi]
        if previous_status != is_open:
            if is_open:
                await telegram_notifier.send_message(f"✅ Рынок открылся для {ticker} ({figi}) в {current_time}")
            else:
                await telegram_notifier.send_message(f"⚠️ Рынок приостановил торги для {ticker} ({figi}) в {current_time}")
            market_status_history[figi] = is_open

        return is_open
    except Exception as e:
        ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
        await telegram_notifier.send_message(f"❌ Ошибка статуса для {ticker} ({figi}): {str(e)}")
        return False


async def process_instrument(figi, ticker, market_data_service):
    print(f"Обработка инструмента: {ticker} ({figi})")
    is_market_open = await check_market_status(figi, market_data_service)
    if not is_market_open:
        return

    df = await fetch_market_data(figi)
    if df is None or df.empty:
        await telegram_notifier.send_message(f"⚠️ Нет данных для {ticker} ({figi}).")
        return

    try:
        df = calculate_indicators(df)
    except ValueError as e:
        await telegram_notifier.send_message(f"❌ Ошибка индикаторов для {ticker} ({figi}): {str(e)}")
        return

    signals_df = generate_signals(df)

    # Сигнал на покупку
    if "buy_signal" in signals_df.columns and signals_df["buy_signal"].any():
        buy_signals = signals_df[signals_df["buy_signal"]].iloc[-1:]
        for timestamp, row in buy_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "buy")
            if signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"🟢 Сигнал на покупку: {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}"
                )
                await telegram_notifier.send_message(message)
                print(message)
                sent_signals.add(signal_key)
                active_positions[figi] = {"type": "long", "entry_time": timestamp.isoformat()}

    # Сигнал на продажу
    if "sell_signal" in signals_df.columns and signals_df["sell_signal"].any():
        sell_signals = signals_df[signals_df["sell_signal"]].iloc[-1:]
        for timestamp, row in sell_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "sell")
            if signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"🔴 Сигнал на продажу: {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}"
                )
                await telegram_notifier.send_message(message)
                print(message)
                sent_signals.add(signal_key)
                active_positions[figi] = {"type": "short", "entry_time": timestamp.isoformat()}

    # Фиксация прибыли (long)
    if "profit_take_long" in signals_df.columns and signals_df["profit_take_long"].any():
        profit_signals = signals_df[signals_df["profit_take_long"]].iloc[-1:]
        for timestamp, row in profit_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "profit_take_long")
            if figi in active_positions and active_positions[figi]["type"] == "long" and signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"🟡 Фиксация прибыли (long): {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}"
                )
                await telegram_notifier.send_message(message)
                print(message)
                sent_signals.add(signal_key)
                del active_positions[figi]

    # Фиксация прибыли (short)
    if "profit_take_short" in signals_df.columns and signals_df["profit_take_short"].any():
        profit_signals = signals_df[signals_df["profit_take_short"]].iloc[-1:]
        for timestamp, row in profit_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "profit_take_short")
            if figi in active_positions and active_positions[figi]["type"] == "short" and signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                message = (
                    f"🟡 Фиксация прибыли (short): {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}"
                )
                await telegram_notifier.send_message(message)
                print(message)
                sent_signals.add(signal_key)
                del active_positions[figi]

    # === СТОП-ЛОСС ===
    if "stop_loss" in signals_df.columns and signals_df["stop_loss"].any():
        stop_loss_signals = signals_df[signals_df["stop_loss"]].iloc[-1:]
        for timestamp, row in stop_loss_signals.iterrows():
            signal_key = (figi, timestamp.isoformat(), "stop_loss")
            if signal_key not in sent_signals:
                signal_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                position_type = active_positions.get(figi, {}).get("type", "unknown")

                if position_type == "long":
                    message = (
                        f"🛑 Стоп-лосс (long): {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}. "
                        f"Цена входа: {row['entry_price']:.2f} RUB"
                    )
                elif position_type == "short":
                    message = (
                        f"🛑 Стоп-лосс (short): {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}. "
                        f"Цена входа: {row['entry_price']:.2f} RUB"
                    )
                else:
                    message = (
                        f"🛑 Стоп-лосс: {ticker} ({figi}) по цене {row['close']:.2f} RUB в {signal_time}. "
                        f"Неизвестная позиция."
                    )

                await telegram_notifier.send_message(message)
                print(message)
                sent_signals.add(signal_key)

                # Удаляем из активных позиций
                if figi in active_positions:
                    del active_positions[figi]


async def main():
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await telegram_notifier.send_message(f"🚀 Бот запущен в {start_time}")
    print(f"Бот запущен в {start_time}")

    async with AsyncClient(API_TOKEN) as client:
        market_data_service = client.market_data
        try:
            while True:
                tasks = [
                    process_instrument(figi, FIGI_TO_TICKER.get(figi, "Unknown"), market_data_service)
                    for figi in FIGI_TO_TICKER.keys()
                ]
                await asyncio.gather(*tasks)
                print(f"Цикл завершен. Ожидание {TIMEOUT} секунд...")
                await asyncio.sleep(TIMEOUT)
        except asyncio.CancelledError:
            stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await telegram_notifier.send_message(f"🛑 Бот остановлен в {stop_time}")
        except Exception as e:
            error_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await telegram_notifier.send_message(f"❌ Ошибка бота в {error_time}: {str(e)}")
            raise


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        loop.run_until_complete(telegram_notifier.send_message(f"🛑 Бот остановлен в {stop_time}"))
        print(f"Бот остановлен в {stop_time}")
        loop.close()
    except Exception as e:
        stop_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        loop.run_until_complete(telegram_notifier.send_message(f"❌ Критическая ошибка в {stop_time}: {str(e)}"))
        print(f"Критическая ошибка: {str(e)}")
        loop.close()
        sys.exit(1)
