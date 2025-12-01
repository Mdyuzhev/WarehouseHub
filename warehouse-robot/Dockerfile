# Warehouse Robot — Docker image
# Робот-симулятор складских операций

FROM python:3.11-slim

LABEL maintainer="flomaster"
LABEL description="Warehouse Robot Simulator"
LABEL version="1.0.0"

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Рабочая директория
WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Порт API
EXPOSE 8070

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8070/health', timeout=5)" || exit 1

# Запуск API сервера
CMD ["python", "robot.py", "api"]
