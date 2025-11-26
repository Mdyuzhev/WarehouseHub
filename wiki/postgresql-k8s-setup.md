# Развёртывание PostgreSQL в Kubernetes (K3s)

## Обзор

Данный документ описывает процесс развёртывания PostgreSQL 15 в кластере K3s для использования в качестве основной базы данных приложения warehouse-api. Развёртывание выполнено в рамках задачи WH-12.

## Дата выполнения

26 ноября 2025

## Архитектура решения

PostgreSQL развёрнут как StatefulSet в отдельном namespace `warehouse` с persistent storage для сохранения данных между перезапусками. Решение включает три типа сервисов для различных сценариев доступа.
```
┌─────────────────────────────────────────────────────────────┐
│                    K3s Cluster                              │
│  ┌───────────────────────────────────────────────────────┐ │
│  │               namespace: warehouse                     │ │
│  │                                                        │ │
│  │   ┌──────────────┐     ┌───────────────────────────┐  │ │
│  │   │  postgres-0  │◄────│  postgres-service         │  │ │
│  │   │  (StatefulSet│     │  ClusterIP: 5432          │  │ │
│  │   │   + PVC 5Gi) │     │  NodePort: 30432          │  │ │
│  │   └──────────────┘     └───────────────────────────┘  │ │
│  │         │                                              │ │
│  │         ▼                                              │ │
│  │   ┌──────────────┐                                    │ │
│  │   │ postgres-data│ ← PersistentVolumeClaim (5Gi)      │ │
│  │   └──────────────┘                                    │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Параметры подключения

### Для приложений внутри кластера (warehouse-api)

| Параметр | Значение |
|----------|----------|
| Host | `postgres-service.warehouse.svc.cluster.local` |
| Port | `5432` |
| Database | `warehouse` |
| User | `warehouse_user` |
| Password | `warehouse_secret_2025` |

JDBC URL для Spring Boot:
```
jdbc:postgresql://postgres-service.warehouse.svc.cluster.local:5432/warehouse
```

### Для внешнего доступа (DBeaver, отладка)

| Параметр | Значение |
|----------|----------|
| Host | `192.168.1.74` |
| Port | `30432` |
| Database | `warehouse` |
| User | `warehouse_user` |
| Password | `warehouse_secret_2025` |

## Структура манифестов

Все манифесты размещены на сервере в директории `~/k8s-postgres/`:

| Файл | Назначение |
|------|------------|
| `00-namespace.yaml` | Создание namespace warehouse |
| `01-secret.yaml` | Хранение credentials (пароли БД) |
| `02-configmap-init.yaml` | Init-скрипт для создания БД и пользователя |
| `03-pvc.yaml` | PersistentVolumeClaim на 5Gi |
| `04-statefulset.yaml` | StatefulSet с PostgreSQL 15 |
| `05-service.yaml` | Три сервиса (ClusterIP, Headless, NodePort) |

## Пошаговый процесс развёртывания

### Шаг 1: Создание Namespace

Namespace изолирует все ресурсы приложения warehouse от других workloads в кластере.
```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: warehouse
  labels:
    app.kubernetes.io/name: warehouse
    environment: development
```

Применение:
```bash
kubectl apply -f ~/k8s-postgres/00-namespace.yaml
```

### Шаг 2: Создание Secret с credentials

Secret хранит чувствительные данные — пароли для PostgreSQL. Используется тип `stringData` для читаемости, Kubernetes автоматически кодирует значения в base64.
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: postgres-credentials
  namespace: warehouse
type: Opaque
stringData:
  POSTGRES_USER: "postgres"
  POSTGRES_PASSWORD: "postgres_admin_2025"
  APP_DB_USER: "warehouse_user"
  APP_DB_PASSWORD: "warehouse_secret_2025"
  APP_DB_NAME: "warehouse"
  DATABASE_URL: "jdbc:postgresql://postgres-service.warehouse.svc.cluster.local:5432/warehouse"
```

Применение:
```bash
kubectl apply -f ~/k8s-postgres/01-secret.yaml
```

### Шаг 3: Создание ConfigMap с init-скриптом

ConfigMap содержит shell-скрипт, который выполняется при первом запуске PostgreSQL (когда data directory пустой). Скрипт создаёт базу данных, пользователя и настраивает права доступа.
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgres-init-script
  namespace: warehouse
data:
  01-init-database.sh: |
    #!/bin/bash
    set -e
    # Создание пользователя warehouse_user
    # Создание базы данных warehouse
    # Настройка прав доступа
    # Установка расширения uuid-ossp
```

Применение:
```bash
kubectl apply -f ~/k8s-postgres/02-configmap-init.yaml
```

### Шаг 4: Создание PersistentVolumeClaim

PVC запрашивает 5Gi постоянного хранилища. K3s использует local-path provisioner, который создаёт директорию на хосте в `/var/lib/rancher/k3s/storage/`.
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-data
  namespace: warehouse
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: local-path
  resources:
    requests:
      storage: 5Gi
```

Применение:
```bash
kubectl apply -f ~/k8s-postgres/03-pvc.yaml
```

### Шаг 5: Создание StatefulSet

StatefulSet — основной ресурс, который запускает контейнер PostgreSQL. Выбран StatefulSet вместо Deployment, потому что он обеспечивает стабильные сетевые идентификаторы и привязку к конкретному PVC.

Ключевые особенности конфигурации:

- **Образ**: `postgres:15-alpine` — легковесная версия PostgreSQL 15
- **Ресурсы**: requests 256Mi RAM / 100m CPU, limits 512Mi RAM / 500m CPU
- **Probes**: readinessProbe и livenessProbe через `pg_isready`
- **Volumes**: данные в PVC, init-скрипты из ConfigMap
```bash
kubectl apply -f ~/k8s-postgres/04-statefulset.yaml
```

### Шаг 6: Создание Services

Создаются три сервиса для разных сценариев использования:

1. **postgres-service** (ClusterIP) — основной сервис для доступа из других подов
2. **postgres-headless** — headless сервис для StatefulSet DNS discovery
3. **postgres-external** (NodePort:30432) — для внешнего доступа при отладке
```bash
kubectl apply -f ~/k8s-postgres/05-service.yaml
```

## Проверка работоспособности

### Проверка статуса ресурсов
```bash
kubectl get all -n warehouse
```

Ожидаемый результат:
```
NAME             READY   STATUS    RESTARTS   AGE
pod/postgres-0   1/1     Running   0          5m

NAME                          TYPE        CLUSTER-IP      PORT(S)
service/postgres-service      ClusterIP   10.43.35.38     5432/TCP
service/postgres-headless     ClusterIP   None            5432/TCP
service/postgres-external     NodePort    10.43.x.x       5432:30432/TCP

NAME                        READY
statefulset.apps/postgres   1/1
```

### Проверка подключения
```bash
# Подключение как суперпользователь
kubectl exec -it -n warehouse postgres-0 -- psql -U postgres -c "\l"

# Подключение как пользователь приложения
kubectl exec -it -n warehouse postgres-0 -- psql -U warehouse_user -d warehouse -c "SELECT current_user, current_database();"
```

### Проверка persistence
```bash
# Создать тестовые данные
kubectl exec -it -n warehouse postgres-0 -- psql -U warehouse_user -d warehouse -c "
CREATE TABLE test_persistence (id SERIAL, message TEXT);
INSERT INTO test_persistence (message) VALUES ('Test data');
SELECT * FROM test_persistence;"

# Удалить под (Kubernetes пересоздаст его)
kubectl delete pod postgres-0 -n warehouse

# Дождаться перезапуска
kubectl wait --for=condition=Ready pod/postgres-0 -n warehouse --timeout=120s

# Проверить что данные сохранились
kubectl exec -it -n warehouse postgres-0 -- psql -U warehouse_user -d warehouse -c "SELECT * FROM test_persistence;"
```

## Интеграция с Spring Boot

Для подключения warehouse-api к PostgreSQL добавь в `application.yaml`:
```yaml
spring:
  datasource:
    url: jdbc:postgresql://postgres-service.warehouse.svc.cluster.local:5432/warehouse
    username: warehouse_user
    password: warehouse_secret_2025
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: update
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
```

Или через environment variables в Kubernetes Deployment:
```yaml
env:
  - name: SPRING_DATASOURCE_URL
    valueFrom:
      secretKeyRef:
        name: postgres-credentials
        key: DATABASE_URL
  - name: SPRING_DATASOURCE_USERNAME
    valueFrom:
      secretKeyRef:
        name: postgres-credentials
        key: APP_DB_USER
  - name: SPRING_DATASOURCE_PASSWORD
    valueFrom:
      secretKeyRef:
        name: postgres-credentials
        key: APP_DB_PASSWORD
```

## Полезные команды
```bash
# Статус всех ресурсов
kubectl get all -n warehouse

# Логи PostgreSQL
kubectl logs -n warehouse postgres-0

# Интерактивный psql
kubectl exec -it -n warehouse postgres-0 -- psql -U warehouse_user -d warehouse

# Проверка PVC
kubectl get pvc -n warehouse

# Описание пода (для диагностики)
kubectl describe pod postgres-0 -n warehouse
```

## Удаление (при необходимости)
```bash
kubectl delete -f ~/k8s-postgres/05-service.yaml
kubectl delete -f ~/k8s-postgres/04-statefulset.yaml
kubectl delete -f ~/k8s-postgres/03-pvc.yaml  # Удалит данные!
kubectl delete -f ~/k8s-postgres/02-configmap-init.yaml
kubectl delete -f ~/k8s-postgres/01-secret.yaml
kubectl delete -f ~/k8s-postgres/00-namespace.yaml
```

## Критерии приёмки (выполнены)

- [x] PostgreSQL запущен в namespace `warehouse`
- [x] Под в статусе `Running` и `Ready`
- [x] База данных `warehouse` создана
- [x] Пользователь `warehouse_user` создан с правами
- [x] Данные сохраняются после перезапуска пода
- [x] Credentials хранятся в Kubernetes Secret
- [x] Доступ из кластера через ClusterIP работает
- [x] Внешний доступ через NodePort работает

---

*Задача: WH-12*
*Автор: Flomaster*
*Дата: 26 ноября 2025*