# Load Testing Guide

Руководство по нагрузочному тестированию проекта Warehouse.

## Инструменты

| Инструмент | Назначение | Namespace |
|------------|------------|-----------|
| k6-operator | Распределённое тестирование Kafka | loadtest |
| Locust | HTTP нагрузка на API | loadtest |

## k6 Kafka Load Testing

### Компоненты

- **k6-operator** — оператор для распределённого запуска k6 тестов
- **k6-kafka** — кастомный образ k6 с xk6-kafka extension
- **TestRun CRD** — манифест для запуска распределённых тестов

### Grafana Dashboard

- **URL:** http://192.168.1.74:30300/d/kafka-load-testing
- **Datasource UID:** `PBFA97CFB590B2093` (НЕ "prometheus"!)

### Сценарии

| Файл | Описание |
|------|----------|
| `k6-kafka/scenarios/producer-test.js` | Базовый тест (K6_VUS/K6_DURATION) |
| `k6-kafka/scenarios/distributed-300vu.js` | Ramp-up 0→300 VU, 6 воркеров |

### Пересборка образа k6-kafka

```bash
cd ~/warehouse-master/k6-kafka

# Сборка без кэша
docker build --no-cache -t k6-kafka:latest .

# Импорт в K3s containerd (ВАЖНО: K3s != Docker!)
docker save k6-kafka:latest -o /tmp/k6-kafka.tar
sudo k3s ctr images import /tmp/k6-kafka.tar
```

### Обновление ConfigMap

```bash
kubectl delete configmap k6-scripts -n loadtest --ignore-not-found

kubectl create configmap k6-scripts -n loadtest \
  --from-file=producer-test.js=k6-kafka/scenarios/producer-test.js \
  --from-file=distributed-300vu.js=k6-kafka/scenarios/distributed-300vu.js
```

### Запуск распределённого теста

```bash
kubectl apply -f k8s/loadtest/k6/k6-testrun-distributed.yaml
```

### Остановка теста

```bash
kubectl delete testrun --all -n loadtest
```

### Мониторинг

```bash
# Статус подов
kubectl get pods -n loadtest -l app=k6

# CPU/Memory
kubectl top pods -n loadtest -l app=k6

# Логи воркера
kubectl logs -n loadtest -l app=k6 --tail=50
```

---

## Очистка тестовых данных

**ОБЯЗАТЕЛЬНО выполнить ПЕРЕД запуском нагрузочного теста!**

### Порядок очистки

1. Остановить текущие тесты
2. Очистить Kafka топики
3. Очистить Redis аналитику
4. Проверить что данные удалены
5. Запустить тест

### 1. Остановка тестов

```bash
kubectl delete testrun --all -n loadtest
kubectl delete job --all -n loadtest --ignore-not-found
```

### 2. Очистка Kafka топиков

```bash
# Найти pod Kafka
kubectl get pods -n warehouse | grep kafka

# Очистка warehouse.audit (заменить kafka-XXX на актуальное имя пода)
kubectl exec -n warehouse kafka-5f6944cd48-fsktl -- bash -c 'cat > /tmp/delete-audit.json << EOF
{"partitions":[{"topic":"warehouse.audit","partition":0,"offset":-1},{"topic":"warehouse.audit","partition":1,"offset":-1},{"topic":"warehouse.audit","partition":2,"offset":-1}],"version":1}
EOF
/opt/kafka/bin/kafka-delete-records.sh --bootstrap-server localhost:9092 --offset-json-file /tmp/delete-audit.json'

# Очистка warehouse.notifications
kubectl exec -n warehouse kafka-5f6944cd48-fsktl -- bash -c 'cat > /tmp/delete-notifications.json << EOF
{"partitions":[{"topic":"warehouse.notifications","partition":0,"offset":-1},{"topic":"warehouse.notifications","partition":1,"offset":-1},{"topic":"warehouse.notifications","partition":2,"offset":-1}],"version":1}
EOF
/opt/kafka/bin/kafka-delete-records.sh --bootstrap-server localhost:9092 --offset-json-file /tmp/delete-notifications.json'
```

**Ожидаемый результат:**
```
Records delete operation completed:
partition: warehouse.audit-0    low_watermark: 0
partition: warehouse.audit-1    low_watermark: 0
partition: warehouse.audit-2    low_watermark: 0
```

### 3. Очистка Redis (аналитика)

```bash
# Найти pod Redis
kubectl get pods -n warehouse | grep redis

# Очистить DB 1 (аналитика analytics-service)
kubectl exec -n warehouse redis-58b9ffc964-drwnc -- redis-cli -n 1 FLUSHDB
```

**Ожидаемый результат:** `OK`

### 4. Проверка очистки

- http://192.168.1.74:30081/analytics — должна показывать пустую аналитику
- Kafka топики пусты (low_watermark: 0)

---

## Locust HTTP Testing

### Запуск

```bash
kubectl apply -f k8s/loadtest/
```

### Web UI

http://192.168.1.74:30089

### Конфигурация

- Master: `locust-master` pod
- Workers: 5 реплик `locust-worker`
- Сценарий: `k8s/loadtest/locust-configmap.yaml`

---

## Метрики в Prometheus

### k6 метрики (native histograms)

| Метрика | Описание |
|---------|----------|
| `k6_vus` | Текущее количество VU |
| `k6_iterations_total` | Всего итераций |
| `k6_kafka_messages_produced_total_total` | Отправлено сообщений |
| `k6_kafka_produce_latency_ms_seconds` | Latency (histogram) |
| `k6_kafka_produce_success_rate_rate` | Success rate |
| `k6_kafka_writer_error_count_total` | Ошибки |

### PromQL запросы

```promql
# Throughput (msg/sec)
sum(rate(k6_kafka_messages_produced_total_total[1m]))

# p95 Latency (native histogram)
histogram_quantile(0.95, k6_kafka_produce_latency_ms_seconds) * 1000

# Error rate
sum(rate(k6_kafka_writer_error_count_total[1m]))

# Success rate %
k6_kafka_produce_success_rate_rate * 100
```

---

## Troubleshooting

### Dashboard пустой (No data)

1. Проверить datasource UID:
```bash
curl -s "http://admin:admin123@192.168.1.74:30300/api/datasources" | jq '.[].uid'
# Должен быть PBFA97CFB590B2093
```

2. Проверить метрики в Prometheus:
```bash
curl -s "http://192.168.1.74:30090/api/v1/query?query=k6_vus"
```

3. Переимпортировать дашборд с правильным UID

### Pod в Error/CrashLoopBackOff

```bash
kubectl logs -n loadtest job/k6-XXX
kubectl describe pod -n loadtest -l app=k6
```

### Образ не найден (ErrImageNeverPull)

```bash
# Проверить что образ есть в containerd
sudo k3s ctr images ls | grep k6

# Если нет — импортировать заново
docker save k6-kafka:latest -o /tmp/k6-kafka.tar
sudo k3s ctr images import /tmp/k6-kafka.tar
```

### CPU в потолке

Если один воркер упирается в CPU (~100% на 2-4 ядра при ~50 VU):
- Используй k6-operator с несколькими воркерами
- TestRun с `parallelism: 6` распределяет нагрузку

### Метрики latency не отображаются

k6 экспортирует **native histograms**, НЕ classic buckets!

**Неправильно:**
```promql
histogram_quantile(0.95, sum(rate(k6_kafka_produce_latency_ms_seconds_bucket[1m])) by (le))
```

**Правильно:**
```promql
histogram_quantile(0.95, k6_kafka_produce_latency_ms_seconds)
```

---

## Telegram Bot Load Testing Wizard (WH-217)

Бот v5.6 поддерживает запуск нагрузочных тестов через 7-шаговый wizard:

### Шаги wizard

1. **Среда** — staging / production
2. **Пароль** — простой (staging) / надёжный (production)
3. **Сценарий** — Locust (HTTP API) / k6 (Kafka)
4. **VU** — 10 / 25 / 50 виртуальных пользователей
5. **Время** — 2 / 5 / 10 минут
6. **Паттерн** — constant (ровная нагрузка) / ramp-up (постепенный рост)
7. **Подтверждение** — review параметров + запуск

### Cooldown

- **30 минут** между запусками (защита от перегрузки)
- Cooldown показывается в боте с обратным отсчётом

### Пароли

| Среда | Переменная | Описание |
|-------|------------|----------|
| staging | `LOAD_TEST_STAGING_PASSWORD` | Простой пароль (по умолчанию "1") |
| production | `LOAD_TEST_PROD_PASSWORD` | Надёжный пароль (обязателен!) |

### Кнопки в боте

- **[Нагрузка]** — запуск wizard
- **[Очистка]** — очистка Redis/Kafka/PostgreSQL

---

## Baseline результаты

### 10 VU / 1 min (single pod)

| Параметр | Значение |
|----------|----------|
| VUs | 10 |
| Duration | 1m |
| Iterations | ~45,000 |
| Throughput | ~750 msg/sec |
| p95 Latency | ~3ms |
| Errors | 0 |
| Success Rate | 100% |

### Лимиты single pod

- ~50 VU — CPU bottleneck (4 cores)
- ~80 VU — OOMKilled при 1Gi RAM

Для >50 VU используй распределённый тест (k6-operator).

---

## k6 Kafka для Production (WH-217)

### Конфигурация

| Параметр | Staging | Production |
|----------|---------|------------|
| Kafka brokers | kafka.warehouse.svc.cluster.local:9092 | 130.193.44.34:29092 |
| Env var | KAFKA_STAGING_BROKERS | KAFKA_PROD_BROKERS |

### docker-compose.yml (Production)

Kafka на prod настроен с EXTERNAL listener:
```yaml
kafka:
  environment:
    - KAFKA_LISTENERS=PLAINTEXT://:9092,EXTERNAL://:29092,CONTROLLER://:9093
    - KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092,EXTERNAL://130.193.44.34:29092
  ports:
    - "29092:29092"
```

### Запуск через Telegram Bot

1. Нажать **[Нагрузка]** или через QA меню
2. Выбрать **Production**
3. Ввести пароль (LOAD_TEST_PROD_PASSWORD)
4. Выбрать **k6 (Kafka)**
5. Настроить VU / время / паттерн
6. Подтвердить запуск

---

*Последнее обновление: 2025-12-02 (WH-217)*
