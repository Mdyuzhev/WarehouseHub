# k6 Kafka Load Testing

Нагрузочное тестирование Kafka для проекта Warehouse.

## Структура

```
k6-kafka/
├── Dockerfile           # Docker образ с xk6-kafka extension
├── scenarios/
│   ├── producer-test.js # Тест producer (warehouse-api → Kafka)
│   └── consumer-test.js # Тест consumer (Kafka → analytics-service)
└── README.md
```

## Быстрый старт

### 1. Запуск теста вручную

```bash
# Удалить предыдущий тест
kubectl delete job k6-kafka-test -n loadtest --ignore-not-found

# Применить Job
kubectl apply -f k8s/loadtest/k6/k6-job.yaml

# Следить за логами
kubectl logs -n loadtest -l app=k6 -f
```

### 2. Кастомные параметры

```bash
# Запуск с 50 VU на 5 минут
kubectl delete job k6-custom-test -n loadtest --ignore-not-found

cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: k6-custom-test
  namespace: loadtest
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      serviceAccountName: k6-runner
      restartPolicy: Never
      containers:
        - name: k6
          image: k6-kafka:latest
          imagePullPolicy: Never
          args: ["run", "--out", "experimental-prometheus-rw", "/scripts/producer-test.js"]
          env:
            - name: K6_PROMETHEUS_RW_SERVER_URL
              value: "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/write"
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

## Метрики

### Кастомные метрики k6

| Метрика | Описание |
|---------|----------|
| kafka_produce_latency_ms | Latency отправки сообщения |
| kafka_produce_errors_total | Количество ошибок |
| kafka_messages_produced_total | Количество отправленных сообщений |
| kafka_produce_success_rate | Процент успешных отправок |

### Thresholds

- `p(95) < 100ms` - 95-й перцентиль latency
- `p(99) < 500ms` - 99-й перцентиль latency
- `success_rate > 99%` - Процент успешных операций
- `errors < 10` - Максимум ошибок за тест

## Grafana Dashboard

URL: http://192.168.1.74:30300/d/kafka-load-testing

Панели:
- Producer Throughput (msg/sec)
- Producer Latency p95
- Error Rate
- Success Rate
- Latency/Throughput Over Time
- Virtual Users
- Total Iterations

## Telegram Bot

```python
from services import start_k6_test, stop_k6_test, get_k6_status

# Запуск теста
result = await start_k6_test(scenario="producer", vus=10, duration="2m")

# Статус
status = await get_k6_status()

# Остановка
await stop_k6_test()
```

## Пересборка образа

```bash
cd ~/warehouse-master/k6-kafka

# Сборка
docker build --no-cache -t k6-kafka:latest .

# Импорт в K3s
docker save k6-kafka:latest | sudo k3s ctr images import -

# Обновить ConfigMap
kubectl delete configmap k6-scripts -n loadtest
kubectl create configmap k6-scripts \
  --from-file=producer-test.js=scenarios/producer-test.js \
  --from-file=consumer-test.js=scenarios/consumer-test.js \
  -n loadtest
```

## Baseline результаты

| Параметр | Значение |
|----------|----------|
| VUs | 10 |
| Duration | 1m |
| Throughput | ~186 msg/sec |
| p95 Latency | ~96ms |
| p99 Latency | ~174ms |
| Success Rate | 100% |
| Errors | 0 |

## Troubleshooting

### Pod в Error

```bash
kubectl logs -n loadtest job/k6-kafka-test
kubectl describe pod -n loadtest -l app=k6
```

### DNS ошибки

Проверить что Kafka advertised listeners содержит FQDN:
```bash
kubectl exec -n warehouse deployment/kafka -- env | grep ADVERTISED
# Должно быть: kafka.warehouse.svc.cluster.local:9092
```

### Метрики не появляются в Prometheus

Проверить remote write receiver:
```bash
curl -X POST http://192.168.1.74:30090/api/v1/write
# Должен вернуть 204 (не 404)
```

Если 404 - включить remote write:
```bash
kubectl patch prometheus prometheus-kube-prometheus-prometheus -n monitoring \
  --type=merge -p '{"spec":{"enableRemoteWriteReceiver":true}}'
```
