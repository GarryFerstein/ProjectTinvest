# Основной файл запуска торгового бота

import asyncio
from fastapi import FastAPI
from APP.main import run_bot  # Импортируем функцию run_bot из main.py

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Trading bot is running"}

async def start_bot():
    await asyncio.to_thread(run_bot)  # Запускаем бот в отдельном потоке

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_bot())  # Запускаем бот при старте сервера