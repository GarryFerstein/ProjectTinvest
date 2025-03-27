# Базовый образ с Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем все файлы из репозитория
COPY . /app

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Добавляем порт 
EXPOSE 8000  

# Команда для запуска бота
ENTRYPOINT ["python"]
CMD ["app.py"]