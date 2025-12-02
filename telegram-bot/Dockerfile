FROM python:3.11-slim

WORKDIR /app

# WH-267: Установка kubectl и openssh-client для cleanup (staging + prod)
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates openssh-client \
    && curl -LO "https://dl.k8s.io/release/v1.28.0/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY config.py .
COPY app.py .
COPY bot/ ./bot/
COPY services/ ./services/

# Порт
EXPOSE 8000

# Запуск
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
