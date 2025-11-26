# Деплой warehouse-api в Kubernetes

## Обзор

Данный документ описывает процесс развёртывания приложения warehouse-api в кластере Kubernetes (K3s). Деплой выполняется локально без использования Container Registry — образ собирается на сервере и импортируется напрямую в K3s.

## Архитектура

После деплоя warehouse-api работает в namespace `warehouse` вместе с PostgreSQL, образуя единую среду приложения.

```
┌─────────────────────────────────────────────────────────────────┐
│                    namespace: warehouse                          │
│                                                                  │
│   ┌─────────────────┐         ┌─────────────────────────────┐   │
│   │  warehouse-api  │────────►│       postgres-0            │   │
│   │   Deployment    │         │      StatefulSet            │   │
│   │   :8080         │         │       :5432                 │   │
│   └────────┬────────┘         └─────────────────────────────┘   │
│            │                                                     │
│            ▼                                                     │
│   ┌─────────────────┐                                           │
│   │ warehouse-api   │                                           │
│   │    Service      │                                           │
│   │ NodePort:30080  │                                           │
│   └─────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

## Структура манифестов

```
k8s/
├── configmap.yaml    # Конфигурация приложения
├── deployment.yaml   # Deployment warehouse-api
└── service.yaml      # Service (NodePort)
```

## Быстрый старт

Для деплоя используйте готовый скрипт. На сервере 192.168.1.74 в директории проекта выполните:

```bash
chmod +x scripts/deploy-local.sh
./scripts/deploy-local.sh
```

Скрипт автоматически соберёт Docker образ, импортирует его в K3s, применит манифесты и дождётся готовности пода.

## Ручной деплой

Если нужен контроль над каждым шагом, выполните команды последовательно.

### Сборка образа

```bash
docker build -t warehouse-api:latest .
```

### Импорт в K3s

K3s использует containerd, а не Docker, поэтому образы нужно экспортировать и импортировать.

```bash
docker save warehouse-api:latest -o /tmp/warehouse-api.tar
sudo k3s ctr images import /tmp/warehouse-api.tar
rm /tmp/warehouse-api.tar
```

### Применение манифестов

```bash
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### Проверка статуса

```bash
kubectl get pods -n warehouse
kubectl get svc -n warehouse
```

## Параметры конфигурации

### ConfigMap (warehouse-api-config)

ConfigMap содержит не-секретные настройки приложения.

| Переменная | Значение | Описание |
|------------|----------|----------|
| SPRING_PROFILES_ACTIVE | k8s | Активный Spring профиль |
| SERVER_PORT | 8080 | Порт приложения |
| SPRING_JPA_HIBERNATE_DDL_AUTO | update | Стратегия обновления схемы |
| SPRING_JPA_SHOW_SQL | false | Логирование SQL |

### Подключение к PostgreSQL

Credentials для PostgreSQL берутся из Secret `postgres-credentials`, который был создан при развёртывании базы данных (задача WH-12).

| Переменная | Источник |
|------------|----------|
| SPRING_DATASOURCE_URL | Hardcoded (ClusterIP) |
| SPRING_DATASOURCE_USERNAME | Secret: postgres-credentials.APP_DB_USER |
| SPRING_DATASOURCE_PASSWORD | Secret: postgres-credentials.APP_DB_PASSWORD |

## Точки доступа

После успешного деплоя приложение доступно по следующим URL.

| Endpoint | URL | Описание |
|----------|-----|----------|
| Health | http://192.168.1.74:30080/actuator/health | Проверка состояния |
| Swagger UI | http://192.168.1.74:30080/swagger-ui.html | Документация API |
| API Docs | http://192.168.1.74:30080/api-docs | OpenAPI спецификация |

## Проверка работоспособности

### Health Check

```bash
curl http://192.168.1.74:30080/actuator/health
```

Ожидаемый ответ:

```json
{
  "status": "UP",
  "components": {
    "db": {"status": "UP"},
    "diskSpace": {"status": "UP"}
  }
}
```

### Тест API

```bash
# Получить список продуктов
curl http://192.168.1.74:30080/api/products

# Создать продукт
curl -X POST http://192.168.1.74:30080/api/products \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Product", "price": 99.99}'
```

## Логи и отладка

### Просмотр логов

```bash
# Текущие логи
kubectl logs -n warehouse -l app=warehouse-api

# Логи в реальном времени
kubectl logs -n warehouse -l app=warehouse-api -f

# Логи с временными метками
kubectl logs -n warehouse -l app=warehouse-api --timestamps
```

### Описание пода

```bash
kubectl describe pod -n warehouse -l app=warehouse-api
```

### Вход в контейнер

```bash
kubectl exec -it -n warehouse deployment/warehouse-api -- /bin/sh
```

## Обновление приложения

При изменении кода выполните повторный деплой.

```bash
./scripts/deploy-local.sh
```

Скрипт автоматически пересоберёт образ, импортирует его и перезапустит деплоймент.

## Удаление

Для удаления warehouse-api из кластера выполните:

```bash
kubectl delete -f k8s/service.yaml
kubectl delete -f k8s/deployment.yaml
kubectl delete -f k8s/configmap.yaml
```

PostgreSQL при этом останется работать в namespace warehouse.

## Troubleshooting

### Pod не запускается (ImagePullBackOff)

Это означает, что образ не найден в K3s. Убедитесь, что образ импортирован.

```bash
sudo k3s ctr images list | grep warehouse-api
```

Если образа нет, выполните импорт заново.

### Pod в статусе CrashLoopBackOff

Проверьте логи для понимания причины падения.

```bash
kubectl logs -n warehouse -l app=warehouse-api --previous
```

### Ошибка подключения к базе данных

Убедитесь, что PostgreSQL запущен и доступен.

```bash
kubectl get pods -n warehouse -l app.kubernetes.io/name=postgresql
kubectl exec -n warehouse postgres-0 -- pg_isready
```

---

*Задача: WH-19*
*Автор: Flomaster*
*Дата: 26 ноября 2025*
