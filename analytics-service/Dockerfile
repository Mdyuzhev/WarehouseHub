# Analytics Service Dockerfile
# WH-121: Real-time Kafka Analytics Dashboard

FROM python:3.11-slim

WORKDIR /app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY config.py .
COPY redis_store.py .
COPY kafka_consumer.py .
COPY websocket_manager.py .
COPY app.py .

# Port
EXPOSE 8090

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
