# k6 Kafka Load Testing

Нагрузочное тестирование Kafka для проекта Warehouse.

## Структура

```
k6-kafka/
├── Dockerfile           # Docker образ с xk6-kafka extension
├── scenarios/
│   ├── producer-test.js # Тест producer (warehouse-api → Kafka)
│   ├── consumer-test.js # Тест consumer (Kafka → analytics-service)
│   └── ramp-test-*.js   # Ramp-up сценарии
└── README.md
```

## Первоначальная настройка (один раз)

### 1. Собрать и импортировать образ в K3s

```bash
cd ~/warehouse-master/k6-kafka

# Удалить старые образы
docker rmi k6-kafka:latest 2>/dev/null || true
sudo k3s ctr images rm docker.io/library/k6-kafka:latest 2>/dev/null || true

# Собрать без кэша
docker build --no-cache -t k6-kafka:latest .

# Импортировать в K3s containerd (ВАЖНО!)
docker save k6-kafka:latest | sudo k3s ctr images import -
```

### 2. Применить ConfigMap со сценариями

```bash
kubectl apply -f k8s/loadtest/k6/k6-configmap.yaml
```

### 3. Импортировать Grafana дашборд

**ВАЖНО:** Datasource UID должен быть `PBFA97CFB590B2093` (не "prometheus")!

```bash
# Проверить UID datasource
curl -s "http://admin:admin123@192.168.1.74:30300/api/datasources" | jq '.[].uid'

# Исправить в дашборде если нужно
sed -i 's/"uid": "prometheus"/"uid": "PBFA97CFB590B2093"/g' monitoring/grafana/dashboards/kafka-load-testing.json

# Импортировать дашборд
curl -s -X POST "http://admin:admin123@192.168.1.74:30300/api/dashboards/db" \
  -H "Content-Type: application/json" \
  -d "{\"dashboard\": $(cat monitoring/grafana/dashboards/kafka-load-testing.json), \"overwrite\": true}"
```

## Быстрый старт

### Запуск базового теста (10 VU / 1 мин)

```bash
kubectl delete job k6-producer-test -n loadtest --ignore-not-found

kubectl apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: k6-producer-test
  namespace: loadtest
spec:
  ttlSecondsAfterFinished: 300
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: k6
          image: k6-kafka:latest
          imagePullPolicy: Never
          args: ["run", "--out", "experimental-prometheus-rw", "/scripts/producer-test.js"]
          env:
            - name: K6_PROMETHEUS_RW_SERVER_URL
              value: "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/write"
            - name: K6_PROMETHEUS_RW_TREND_AS_NATIVE_HISTOGRAM
              value: "true"
            - name: KAFKA_BROKERS
              value: "kafka.warehouse.svc.cluster.local:9092"
            - name: K6_VUS
              value: "10"
            - name: K6_DURATION
              value: "1m"
          volumeMounts:
            - name: scripts
              mountPath: /scripts
      volumes:
        - name: scripts
          configMap:
            name: k6-scripts
EOF

# Следить за логами
kubectl logs -n loadtest -l job-name=k6-producer-test -f
```

### Кастомный тест с параметрами

```bash
# Изменить K6_VUS и K6_DURATION по необходимости
kubectl delete job k6-custom-test -n loadtest --ignore-not-found

kubectl apply -f - <<'EOF'
apiVersion: batch/v1
kind: Job
metadata:
  name: k6-custom-test
  namespace: loadtest
spec:
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: k6
          image: k6-kafka:latest
          imagePullPolicy: Never
          args: ["run", "--out", "experimental-prometheus-rw", "/scripts/producer-test.js"]
          env:
            - name: K6_PROMETHEUS_RW_SERVER_URL
              value: "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/write"
            - name: K6_PROMETHEUS_RW_TREND_AS_NATIVE_HISTOGRAM
              value: "true"
            - name: KAFKA_BROKERS
              value: "kafka.warehouse.svc.cluster.local:9092"
            - name: K6_VUS
              value: "50"
            - name: K6_DURATION
              value: "5m"
          volumeMounts:
            - name: scripts
              mountPath: /scripts
      volumes:
        - name: scripts
          configMap:
            name: k6-scripts
EOF
```

## Метрики в Prometheus

### Имена метрик (с префиксом k6_)

| Метрика Prometheus | Описание |
|-------------------|----------|
| k6_vus | Текущее количество VU |
| k6_iterations_total | Всего итераций |
| k6_kafka_messages_produced_total_total | Количество отправленных сообщений |
| k6_kafka_produce_latency_ms_seconds | Latency отправки (histogram) |
| k6_kafka_produce_success_rate_rate | Процент успешных отправок |
| k6_kafka_writer_error_count_total | Количество ошибок |

### Полезные PromQL запросы

```promql
# Throughput (msg/sec)
sum(rate(k6_kafka_messages_produced_total_total[1m]))

# p95 Latency (ms)
histogram_quantile(0.95, sum(rate(k6_kafka_produce_latency_ms_seconds_bucket[1m])) by (le)) * 1000

# Error rate
sum(rate(k6_kafka_writer_error_count_total[1m]))

# Success rate
k6_kafka_produce_success_rate_rate * 100
```

## Grafana Dashboard

- URL: http://192.168.1.74:30300/d/kafka-load-testing
- Datasource UID: `PBFA97CFB590B2093`

Панели:
- Producer Throughput (msg/sec)
- Producer Latency p95
- Error Rate
- Success Rate (gauge)
- Latency Over Time (p50, p95, p99)
- Throughput Over Time
- Virtual Users
- Total Iterations
- VUs and Iterations Over Time

## Пересборка образа (после изменений)

```bash
cd ~/warehouse-master/k6-kafka

# Полная пересборка
docker rmi k6-kafka:latest 2>/dev/null || true
sudo k3s ctr images rm docker.io/library/k6-kafka:latest 2>/dev/null || true
docker build --no-cache -t k6-kafka:latest .
docker save k6-kafka:latest | sudo k3s ctr images import -

# Обновить ConfigMap если менялись сценарии
kubectl apply -f ../k8s/loadtest/k6/k6-configmap.yaml
```

## Baseline результаты (10 VU / 1 min)

| Параметр | Значение |
|----------|----------|
| VUs | 10 |
| Duration | 1m |
| Iterations | 45,288 |
| Throughput | ~754 msg/sec |
| p95 Write Latency | ~3.16ms |
| Errors | 0 |
| Success Rate | 100% |

## Troubleshooting

### Дашборд пустой (No data)

1. Проверить datasource UID:
```bash
curl -s "http://admin:admin123@192.168.1.74:30300/api/datasources" | jq '.[].uid'
# Должен быть PBFA97CFB590B2093
```

2. Проверить метрики в Prometheus:
```bash
curl -s "http://192.168.1.74:30090/api/v1/query?query=k6_vus"
# Должен вернуть данные
```

3. Переимпортировать дашборд с правильным UID.

### Pod в Error/CrashLoopBackOff

```bash
kubectl logs -n loadtest job/k6-producer-test
kubectl describe pod -n loadtest -l job-name=k6-producer-test
```

### Образ не найден (ErrImageNeverPull)

Образ не импортирован в containerd:
```bash
sudo k3s ctr images ls | grep k6
# Если пусто — импортировать заново
docker save k6-kafka:latest | sudo k3s ctr images import -
```

### Метрики не появляются в Prometheus

Проверить remote write receiver:
```bash
curl -X POST http://192.168.1.74:30090/api/v1/write
# Должен вернуть 204 (не 404)
```

Если 404 — включить remote write:
```bash
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n monitoring \
  --type=merge -p '{"spec":{"enableRemoteWriteReceiver":true,"enableFeatures":["native-histograms"]}}'
```
