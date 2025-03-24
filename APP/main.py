# Основной файл запуска торгового бота

import asyncio
from datetime import datetime
from tinkoff.invest import AsyncClient, InstrumentStatus
from telegram_notifier import TelegramNotifier
from data_fetcher import fetch_all_market_data
from indicators import calculate_indicators
from signals import generate_signals
from config import API_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, FIGI_TO_TICKER

# Инициализация Telegram-уведомлений
telegram_notifier = TelegramNotifier(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

async def check_market_status(figi, instruments_service):
    """
    Проверяет статус рынка для указанного инструмента.
    """
    try:
        trading_status = await instruments_service.get_trading_status(figi=figi)
        ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
        print(f"Проверка статуса рынка для {ticker} ({figi}): {trading_status.trading_status}")

        if trading_status.trading_status == InstrumentStatus.INSTRUMENT_STATUS_CLOSE:
            await telegram_notifier.send_message(
                f"⚠️ Рынок закрыт для инструмента {ticker} ({figi}). Торговля невозможна."
            )
            return False
        return True
    except Exception as e:
        ticker = FIGI_TO_TICKER.get(figi, "Unknown Ticker")
        print(f"❌ Ошибка при проверке статуса рынка для {ticker} ({figi}): {e}")
        await telegram_notifier.send_message(
            f"❌ Ошибка при проверке статуса рынка для {ticker} ({figi}): {e}"
        )
        return False

async def process_instrument(figi, ticker, market_data_service, instruments_service):
    """
    Обрабатывает один инструмент: проверяет статус, получает данные,
    рассчитывает индикаторы и генерирует сигналы.
    """
    print(f"Обработка инструмента: {ticker} ({figi})")

    # Проверка статуса рынка
    is_market_open = await check_market_status(figi, instruments_service)
    if not is_market_open:
        print(f"Рынок закрыт для {ticker} ({figi}). Пропускаем обработку.")
        return

    # Получение рыночных данных
    df = fetch_all_market_data(figi)
    if df is None or df.empty:
        print(f"⚠️ Нет данных для инструмента {ticker} ({figi}).")
        await telegram_notifier.send_message(
            f"⚠️ Нет данных для инструмента {ticker} ({figi})."
        )
        return

    print(f"Успешно получено {len(df)} записей для {ticker} ({figi}).")

    # Расчет индикаторов
    try:
        df = calculate_indicators(df)
        print(f"Индикаторы рассчитаны для {ticker} ({figi}).")
    except ValueError as e:
        print(f"❌ Ошибка при расчете индикаторов для {ticker} ({figi}): {e}")
        await telegram_notifier.send_message(
            f"❌ Ошибка при расчете индикаторов для {ticker} ({figi}): {e}"
        )
        return

    # Генерация сигналов
    signals_df = generate_signals(df)
    if "buy_signal" in signals_df.columns and signals_df["buy_signal"].any():
        buy_signals = signals_df[signals_df["buy_signal"]]
        for _, row in buy_signals.iterrows():
            print(f"Сигнал на покупку: {ticker} ({figi}) по цене {row['close']:.2f} RUB")
            await telegram_notifier.send_message(
                f"🟢 Сигнал на покупку: {ticker} ({figi}) по цене {row['close']:.2f} RUB"
            )

    if "sell_signal" in signals_df.columns and signals_df["sell_signal"].any():
        sell_signals = signals_df[signals_df["sell_signal"]]
        for _, row in sell_signals.iterrows():
            print(f"Сигнал на продажу: {ticker} ({figi}) по цене {row['close']:.2f} RUB")
            await telegram_notifier.send_message(
                f"🔴 Сигнал на продажу: {ticker} ({figi}) по цене {row['close']:.2f} RUB"
            )

async def main():
    # Отправляем уведомление о запуске бота
    await telegram_notifier.send_message("🚀 Бот запущен.")
    
    # Автоматически запускаем бота
    telegram_notifier.is_running = True
    print("Бот запущен автоматически.")

    # Запуск Telegram-бота в основном цикле событий
    asyncio.create_task(telegram_notifier.run())

    try:
        while True:
            # Проверяем состояние бота
            if not telegram_notifier.is_running:
                print("Бот остановлен. Ждем 5 секунд перед следующей проверкой...")
                await asyncio.sleep(5)
                continue

            # Инициализация клиента Tinkoff
            async with AsyncClient(API_TOKEN) as client:
                instruments_service = client.instruments
                market_data_service = client.market_data

                # Обработка каждого инструмента
                tasks = [
                    process_instrument(figi, ticker, market_data_service, instruments_service)
                    for figi, ticker in FIGI_TO_TICKER.items()
                ]
                await asyncio.gather(*tasks)

            # Ждем перед следующим циклом
            await asyncio.sleep(60)  # Пауза между циклами обработки

    except KeyboardInterrupt:
        print("\nПрограмма остановлена пользователем (CTRL-C).")
        await telegram_notifier.send_message("⏹️ Бот остановлен пользователем.")
    finally:
        # Корректное завершение работы бота
        try:
            await asyncio.sleep(1)  # Даем боту время завершить текущие задачи
            await telegram_notifier.application.updater.stop_polling()
            await telegram_notifier.application.stop()
            await telegram_notifier.application.shutdown()
            print("Telegram-бот успешно остановлен.")
        except Exception as e:
            print(f"Ошибка при завершении работы Telegram-бота: {e}")

# Запуск программы
if __name__ == "__main__":
    asyncio.run(main())