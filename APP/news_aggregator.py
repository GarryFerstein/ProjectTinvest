# Новостной агрегатор: NewsAPI

import aiohttp
import asyncio
from textblob import TextBlob
import logging
from datetime import datetime, timedelta
from config import FIGI_TO_TICKER, NEWSAPI_KEY

logger = logging.getLogger(__name__)

news_cache = {
    "general": {"sentiment": 0.0, "text": "Новости не найдены", "last_updated": None},
    "tickers": {figi: {"sentiment": 0.0, "text": "Новости не найдены", "last_updated": None} for figi in FIGI_TO_TICKER.keys()}
}

NEWSAPI_DAILY_LIMIT = 100
NEWSAPI_INTERVAL = timedelta(minutes=15)
newsapi_request_count = 0
newsapi_reset_time = datetime.now() + timedelta(days=1)

async def fetch_newsapi_general_news():
    """Парсинг общих новостей по российскому фондовому рынку с NewsAPI."""
    global newsapi_request_count, newsapi_reset_time
    current_time = datetime.now()
    
    if current_time > newsapi_reset_time:
        newsapi_request_count = 0
        newsapi_reset_time = current_time + timedelta(days=1)
        logger.info("NewsAPI: лимит запросов сброшен")
    
    last_updated = news_cache["general"]["last_updated"]
    if last_updated and (current_time - last_updated) < NEWSAPI_INTERVAL:
        logger.debug("NewsAPI: используем кэш для общих новостей")
        return news_cache["general"]
    
    if newsapi_request_count >= NEWSAPI_DAILY_LIMIT:
        logger.warning(f"NewsAPI: дневной лимит ({NEWSAPI_DAILY_LIMIT} запросов) исчерпан")
        return news_cache["general"]
    
    query = "российский фондовый рынок"
    url = f"https://newsapi.org/v2/everything?q={query}&language=ru&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    
    try:
        await asyncio.sleep(1)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:  # Отключение проверки SSL
                if response.status == 200:
                    newsapi_request_count += 1
                    data = await response.json()
                    articles = data.get("articles", [])
                    if articles:
                        latest_article = articles[0]
                        title = latest_article["title"]
                        description = latest_article["description"] or ""
                        full_text = f"{title} {description}"
                        sentiment = TextBlob(full_text).sentiment.polarity
                        result = {"sentiment": sentiment, "text": title, "last_updated": current_time}
                        news_cache["general"] = result
                        logger.info(f"NewsAPI общая новость: {title} (тональность: {sentiment})")
                        return result
                    result = {"sentiment": 0.0, "text": "Новости не найдены", "last_updated": current_time}
                    news_cache["general"] = result
                    logger.debug("NewsAPI: общие новости не найдены")
                    return result
                elif response.status == 429:
                    logger.error("NewsAPI: ошибка HTTP 429 для общих новостей - слишком много запросов")
                    return {"sentiment": 0.0, "text": "Ошибка HTTP 429 - слишком много запросов", "last_updated": current_time}
                else:
                    logger.error(f"NewsAPI: ошибка HTTP {response.status} для общих новостей")
                    return {"sentiment": 0.0, "text": f"Ошибка HTTP {response.status}", "last_updated": current_time}
    except Exception as e:
        logger.error(f"NewsAPI: ошибка для общих новостей: {str(e)}")
        return {"sentiment": 0.0, "text": "Ошибка получения новостей", "last_updated": current_time}

async def fetch_newsapi_ticker_news(figi, ticker):
    """Получение новостей для конкретного тикера через NewsAPI на русском языке."""
    global newsapi_request_count, newsapi_reset_time
    current_time = datetime.now()
    
    if current_time > newsapi_reset_time:
        newsapi_request_count = 0
        newsapi_reset_time = current_time + timedelta(days=1)
        logger.info("NewsAPI: лимит запросов сброшен")
    
    last_updated = news_cache["tickers"][figi]["last_updated"]
    if last_updated and (current_time - last_updated) < NEWSAPI_INTERVAL:
        logger.debug(f"NewsAPI: используем кэш для {ticker} ({figi})")
        return news_cache["tickers"][figi]
    
    if newsapi_request_count >= NEWSAPI_DAILY_LIMIT:
        logger.warning(f"NewsAPI: дневной лимит ({NEWSAPI_DAILY_LIMIT} запросов) исчерпан")
        return news_cache["tickers"][figi]
    
    url = f"https://newsapi.org/v2/everything?q={ticker}&language=ru&sortBy=publishedAt&apiKey={NEWSAPI_KEY}"
    try:
        await asyncio.sleep(1)
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=False) as response:  # Отключение проверки SSL
                if response.status == 200:
                    newsapi_request_count += 1
                    data = await response.json()
                    articles = data.get("articles", [])
                    if articles:
                        latest_article = articles[0]
                        title = latest_article["title"]
                        description = latest_article["description"] or ""
                        full_text = f"{title} {description}"
                        sentiment = TextBlob(full_text).sentiment.polarity
                        result = {"sentiment": sentiment, "text": title, "last_updated": current_time}
                        news_cache["tickers"][figi] = result
                        logger.info(f"NewsAPI новость для {ticker} ({figi}): {title} (тональность: {sentiment})")
                        return result
                    result = {"sentiment": 0.0, "text": "Новости не найдены", "last_updated": current_time}
                    news_cache["tickers"][figi] = result
                    logger.debug(f"NewsAPI: новости для {ticker} ({figi}) не найдены")
                    return result
                elif response.status == 429:
                    logger.error(f"NewsAPI: ошибка HTTP 429 для {ticker} ({figi}) - слишком много запросов")
                    return {"sentiment": 0.0, "text": "Ошибка HTTP 429 - слишком много запросов", "last_updated": current_time}
                else:
                    logger.error(f"NewsAPI: ошибка HTTP {response.status} для {ticker} ({figi})")
                    return {"sentiment": 0.0, "text": f"Ошибка HTTP {response.status}", "last_updated": current_time}
    except Exception as e:
        logger.error(f"NewsAPI: ошибка для {ticker} ({figi}): {str(e)}")
        return {"sentiment": 0.0, "text": "Ошибка получения новостей", "last_updated": current_time}

async def analyze_news(figi, ticker):
    """Анализ новостей с NewsAPI для общего рынка и конкретного тикера."""
    general_task = fetch_newsapi_general_news()
    ticker_task = fetch_newsapi_ticker_news(figi, ticker)
    general_result, ticker_result = await asyncio.gather(general_task, ticker_task)
    
    general_sentiment = general_result["sentiment"]
    ticker_sentiment = ticker_result["sentiment"]
    avg_sentiment = (general_sentiment + ticker_sentiment) / 2
    
    news_summary = (
        f"Общий рынок: {general_result['text']} (тональность: {general_sentiment:.2f}), "
        f"{ticker}: {ticker_result['text']} (тональность: {ticker_sentiment:.2f})"
    )
    
    logger.info(f"Новости для {ticker} ({figi}): {news_summary}")
    return {"avg_sentiment": avg_sentiment, "summary": news_summary}