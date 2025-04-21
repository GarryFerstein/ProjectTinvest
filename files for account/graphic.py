# Визуализация японских свечей с сигналами покупки/продажи и фиксации прибыли

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from indicators import calculate_indicators
from signals import generate_signals
import logging

# Настройка логирования
logger = logging.getLogger(__name__)

def plot_candlestick_chart(csv_file: str, ticker: str = "Unknown"):
    """
    Построение графика японских свечей с индикаторами, сигналами и ползунком.
    Args:
        csv_file (str): Путь к CSV-файлу с историческими данными (timestamp, open, high, low, close, volume).
        ticker (str): Название тикера для отображения на графике.
    """
    try:
        # Чтение данных из CSV
        df = pd.read_csv(csv_file)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        logger.info(f"Загружено {len(df)} строк данных из {csv_file} для {ticker}")

        # Проверка наличия необходимых колонок
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            logger.error("Отсутствуют необходимые колонки в CSV-файле")
            raise ValueError("Отсутствуют необходимые колонки в CSV-файле")

        # Расчет индикаторов
        df = calculate_indicators(df)
        if df.empty:
            logger.error("После расчета индикаторов данные пусты")
            raise ValueError("После расчета индикаторов данные пусты")

        # Генерация сигналов
        df = generate_signals(df)
        if df.empty:
            logger.error("После генерации сигналов данные пусты")
            raise ValueError("После генерации сигналов данные пусты")

        # Подготовка данных для графика
        df_mpf = df[['open', 'high', 'low', 'close', 'volume']].copy()
        df_mpf.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

        # Создание стилей для графика
        mc = mpf.make_marketcolors(
            up='green', down='red',
            edge='black',
            wick='black',
            volume='blue'
        )
        s = mpf.make_mpf_style(marketcolors=mc)

        # Начальные параметры (1 час ≈ 4 свечи при 15-минутном таймфрейме)
        window_size = 100
        start_idx = max(0, len(df_mpf) - window_size)

        # Подготовка данных для сигналов
        buy_signals = pd.Series(index=df_mpf.index, dtype=float)
        sell_signals = pd.Series(index=df_mpf.index, dtype=float)
        profit_take_long = pd.Series(index=df_mpf.index, dtype=float)
        profit_take_short = pd.Series(index=df_mpf.index, dtype=float)
        buy_signals[df['buy_signal']] = df['close'][df['buy_signal']]
        sell_signals[df['sell_signal']] = df['close'][df['sell_signal']]
        profit_take_long[df['profit_take_long']] = df['close'][df['profit_take_long']]
        profit_take_short[df['profit_take_short']] = df['close'][df['profit_take_short']]

        # Определение доступных индикаторов
        possible_indicators = [
            'bollinger_high', 'bollinger_low', 'bollinger_mid',
            'bb_upper', 'bb_lower', 'rsi', 'adx', 'plus_di', 'minus_di',
            'upper_band', 'lower_band', 'sma', 'ema'
        ]
        available_indicators = [col for col in possible_indicators if col in df.columns]
        logger.info(f"Доступные индикаторы: {available_indicators}")

        # Создание фигуры и осей
        fig = plt.figure(figsize=(12, 10))
        ax_main = fig.add_axes([0.1, 0.5, 0.8, 0.4])  # Свечи
        ax_volume = fig.add_axes([0.1, 0.35, 0.8, 0.15], sharex=ax_main)  # Объемы
        ax_indicators = fig.add_axes([0.1, 0.2, 0.8, 0.15], sharex=ax_main)  # RSI и другие
        ax_slider = fig.add_axes([0.1, 0.05, 0.8, 0.05])  # Ползунок

        # Создание ползунка (один раз)
        slider = Slider(
            ax_slider,
            'Start Index',
            0,
            len(df_mpf) - window_size,
            valinit=start_idx,
            valstep=1
        )

        # Функция для обновления графика
        def update_plot(val):
            start_idx = int(val)
            end_idx = start_idx + window_size
            if end_idx > len(df_mpf):
                end_idx = len(df_mpf)
                start_idx = max(0, end_idx - window_size)

            # Выборка данных
            df_window = df_mpf.iloc[start_idx:end_idx]
            df_indicators = df.iloc[start_idx:end_idx]

            # Логирование данных
            logger.debug(f"Данные для построения графика: {df_window}")
            logger.debug(f"Доступные индикаторы: {available_indicators}")

            # Проверка данных
            if df_window.empty:
                logger.error("Данные для построения графика пусты")
                return

            # Подготовка дополнительных графиков
            apds = []

            # Сигналы
            if buy_signals.iloc[start_idx:end_idx].notna().any():
                apds.append(
                    mpf.make_addplot(
                        buy_signals.iloc[start_idx:end_idx],
                        type='scatter',
                        markersize=100,
                        marker='^',
                        color='green',
                        label='Buy Signal',
                        ax=ax_main  # Явно указываем ось
                    )
                )
            if sell_signals.iloc[start_idx:end_idx].notna().any():
                apds.append(
                    mpf.make_addplot(
                        sell_signals.iloc[start_idx:end_idx],
                        type='scatter',
                        markersize=100,
                        marker='v',
                        color='red',
                        label='Sell Signal',
                        ax=ax_main  # Явно указываем ось
                    )
                )

            # Индикаторы на основном графике
            for ind in available_indicators:
                if ind in ['bollinger_high', 'bollinger_low', 'bollinger_mid', 'bb_upper', 'bb_lower', 'upper_band', 'lower_band', 'sma', 'ema']:
                    color = 'blue' if 'high' in ind or 'upper' in ind else 'red' if 'low' in ind or 'lower' in ind else 'purple'
                    apds.append(
                        mpf.make_addplot(
                            df_indicators[ind],
                            type='line',
                            color=color,
                            linestyle='--',
                            label=ind.replace('_', ' ').title(),
                            ax=ax_main  # Явно указываем ось
                        )
                    )

            # Построение графика свечей
            try:
                fig, axes = mpf.plot(
                    df_window,
                    type='candle',
                    style=s,
                    ax=ax_main,
                    volume=ax_volume,
                    addplot=apds,
                    title=f"{ticker} Candlestick Chart with Signals and Indicators",
                    ylabel='Price (RUB)',
                    ylabel_lower='Volume',
                    show_nontrading=False,
                    returnfig=True  # Возвращаем объекты fig и axes
                )
                # Индикаторы на отдельной оси
                for ind in available_indicators:
                    if ind in ['rsi', 'adx', 'plus_di', 'minus_di']:
                        color = 'purple' if ind == 'rsi' else 'black' if ind == 'adx' else 'green' if ind == 'plus_di' else 'red'
                        linestyle = '-' if ind in ['rsi', 'adx'] else ':'
                        ax_indicators.plot(df_indicators.index, df_indicators[ind], color=color, linestyle=linestyle, label=ind.replace('_', ' ').title())

                # Дополнительные линии для RSI
                if 'rsi' in available_indicators:
                    ax_indicators.axhline(70, color='red', linestyle='--', alpha=0.5)
                    ax_indicators.axhline(30, color='green', linestyle='--', alpha=0.5)
                    ax_indicators.set_ylim(0, 100)

                ax_indicators.set_ylabel('Indicators')
                ax_indicators.legend()
                ax_indicators.grid(True, alpha=0.3)

                # Обновление меток и стиля
                ax_main.tick_params(axis='x', rotation=45)
                ax_main.grid(True, alpha=0.3)
                ax_volume.grid(True, alpha=0.3)
                ax_main.legend()

                plt.draw()
            except Exception as e:
                logger.error(f"Ошибка при построении графика: {str(e)}")

        # Привязка ползунка к функции обновления
        slider.on_changed(update_plot)

        # Первоначальный рендеринг
        update_plot(start_idx)
        logger.info(f"График для {ticker} успешно построен")
        plt.show()

    except Exception as e:
        logger.error(f"Ошибка при построении графика для {ticker}: {str(e)}")
        print(f"Ошибка при построении графика: {str(e)}")


if __name__ == "__main__":
    # Пример использования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    # Укажите путь к вашему CSV-файлу и тикер
    csv_file = "historical_data.csv"
    ticker = "Example Ticker"
    plot_candlestick_chart(csv_file, ticker)
