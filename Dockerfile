# Базовый образ с Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы из репозитория
COPY . /app

# Устанавливаем зависимости из requirements.txt и FastAPI
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

# Открываем порт 8000 для Timeweb
EXPOSE 8000

# Команда для запуска веб-сервера FastAPI
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]