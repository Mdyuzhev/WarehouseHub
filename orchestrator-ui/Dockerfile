# 🎮 Dockerfile для Warehouse Orchestrator UI
# 8-bit edition - минималистично, как и должно быть

FROM python:3.11-slim

LABEL maintainer="flomaster"
LABEL description="8-bit control panel for Warehouse orchestration"

# Устанавливаем kubectl для управления K8s
RUN apt-get update && apt-get install -y \
    curl \
    bash \
    && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
    && chmod +x kubectl \
    && mv kubectl /usr/local/bin/ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY . .

# Создаём папку для данных
RUN mkdir -p /app/data

# Порт
EXPOSE 8000

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Запуск
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
