# Базовый образ с Python

FROM python:3.11-slim-bookworm

# Обновляем системные пакеты для устранения уязвимостей
RUN apt-get update && apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /APP

# Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
    
# Копируем все файлы проекта
COPY . .

# Указываем порт, который будет использоваться приложением
EXPOSE 8000

# Команда для запуска бота
CMD ["python", "main.py"]