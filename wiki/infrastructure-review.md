# Ревизия инфраструктуры DevOps Home Lab

## Обзор

Данный документ описывает ревизию инфраструктуры DevOps-стенда, проведённую 26 ноября 2025 года. В ходе ревизии были устранены дублирующиеся компоненты и консолидирована архитектура системы.

## Дата выполнения

26 ноября 2025

## Задача

WH-16: Ревизия инфраструктуры

## Исходное состояние

До ревизии инфраструктура содержала дублирующиеся компоненты, которые создавали путаницу и расходовали ресурсы сервера.

### Обнаруженные дублирования

**PostgreSQL — два экземпляра:**

| Расположение | Версия | Порт | Назначение |
|--------------|--------|------|------------|
| Docker контейнер `warehouse-postgres` | PostgreSQL 16 | 5432 | Старая установка |
| K8s StatefulSet `postgres-0` | PostgreSQL 15 | 30432 | Новая установка (WH-12) |

**GitLab Runner — два экземпляра:**

| Расположение | Executor | Статус |
|--------------|----------|--------|
| Systemd service | Shell executor | Рабочий, используется в CI/CD |
| K8s Deployment (Helm) | Kubernetes executor | Не использовался |

## Принятые решения

После анализа были приняты следующие решения по консолидации инфраструктуры.

**PostgreSQL:** Оставить K8s версию (PostgreSQL 15 в namespace warehouse), так как она была развёрнута по best practices с PersistentVolumeClaim, init-скриптами и полной документацией. Docker контейнер удалить.

**GitLab Runner:** Оставить Shell executor (systemd), так как он уже настроен, протестирован и успешно выполняет CI/CD pipeline. Kubernetes executor удалить для экономии ресурсов.

**YouTrack:** Оставить в Docker без изменений — работает стабильно, миграция в K8s отложена на будущее.

## Выполненные действия

### Удаление Docker PostgreSQL
```bash
docker stop warehouse-postgres
docker rm warehouse-postgres
docker rmi postgres:16-alpine
```

Результат: контейнер удалён, освобождено ~275MB дискового пространства.

### Удаление GitLab Runner из Kubernetes
```bash
helm uninstall gitlab-runner -n gitlab-runner
kubectl delete namespace gitlab-runner
```

Результат: Helm release удалён, namespace очищен, ресурсы кластера освобождены.

## Итоговая архитектура

После ревизии инфраструктура имеет следующую структуру:
```
┌─────────────────────────────────────────────────────────────────┐
│              flomasterserver (192.168.1.74)                     │
│              Ubuntu 24.04 LTS | 12 CPU | 24GB RAM               │
├─────────────────────────────────────────────────────────────────┤
│  DOCKER CONTAINERS                                              │
│  ├── gitlab (:8080, :8443, :2222) — GitLab CE                  │
│  └── youtrack (:8088) — YouTrack 2024.3                        │
├─────────────────────────────────────────────────────────────────┤
│  K3s CLUSTER (v1.33.6)                                          │
│  ├── kube-system/                                               │
│  │   ├── CoreDNS                                                │
│  │   ├── Traefik Ingress                                        │
│  │   ├── Metrics Server                                         │
│  │   └── Local Path Provisioner                                 │
│  ├── monitoring/                                                │
│  │   ├── Prometheus                                             │
│  │   ├── Grafana (:3000)                                        │
│  │   ├── AlertManager                                           │
│  │   └── Node Exporter                                          │
│  └── warehouse/                                                 │
│      └── PostgreSQL 15 StatefulSet (:30432)                    │
├─────────────────────────────────────────────────────────────────┤
│  SYSTEMD SERVICES                                               │
│  ├── docker.service                                             │
│  ├── k3s.service                                                │
│  └── gitlab-runner.service (Shell executor)                    │
└─────────────────────────────────────────────────────────────────┘
```

## Таблица сервисов и портов

| Сервис | Тип | Порт | Назначение |
|--------|-----|------|------------|
| GitLab CE | Docker | 8080 | CI/CD платформа, Git-репозитории |
| GitLab SSH | Docker | 2222 | Git over SSH |
| YouTrack | Docker | 8088 | Issue tracking |
| PostgreSQL | K8s NodePort | 30432 | База данных warehouse-api |
| Grafana | K8s (port-forward) | 3000 | Мониторинг и дашборды |
| Prometheus | K8s ClusterIP | 9090 | Сбор метрик |
| K3s API | K8s | 6443 | Kubernetes API |

## Helm Releases

| Release | Namespace | Chart | Назначение |
|---------|-----------|-------|------------|
| prometheus | monitoring | kube-prometheus-stack-79.7.1 | Стек мониторинга |
| traefik | kube-system | traefik-37.1.1 | Ingress controller |

## Kubernetes Namespaces

| Namespace | Назначение |
|-----------|------------|
| default | Системный (не используется) |
| kube-system | Системные компоненты K3s |
| kube-public | Публичные ресурсы |
| kube-node-lease | Heartbeat нод |
| monitoring | Prometheus + Grafana + AlertManager |
| warehouse | PostgreSQL и будущие компоненты приложения |

## Проверка работоспособности

После ревизии все компоненты проверены и работают корректно.

**Docker контейнеры:**
```bash
docker ps
# gitlab: Up, healthy
# youtrack: Up
```

**PostgreSQL в Kubernetes:**
```bash
kubectl get pods -n warehouse
# postgres-0: 1/1 Running

kubectl exec -n warehouse postgres-0 -- pg_isready -U postgres
# accepting connections
```

**GitLab Runner:**
```bash
sudo gitlab-runner list
# shell-runner: active
```

## Освобождённые ресурсы

| Компонент | Освобождено |
|-----------|-------------|
| Docker образ postgres:16-alpine | ~275MB |
| K8s GitLab Runner pod | ~200MB RAM |
| K8s namespace gitlab-runner | Очищен |

## Следующие шаги

Согласно плану развития инфраструктуры, следующими задачами являются:

1. **WH-15:** Настройка CI/CD для warehouse-api с автоматическим деплоем в K8s
2. **WH-13:** Миграция GitLab из Docker в Kubernetes (опционально)
3. **WH-14:** Миграция YouTrack из Docker в Kubernetes (опционально)

## Выводы

Ревизия инфраструктуры позволила устранить дублирование компонентов, освободить ресурсы и создать чёткую, документированную архитектуру. Теперь каждый компонент существует в единственном экземпляре, что упрощает поддержку и отладку.

Текущая архитектура представляет собой гибридное решение: критичные stateful-сервисы (GitLab, YouTrack) работают в Docker для стабильности, а Kubernetes используется для оркестрации приложений (PostgreSQL, мониторинг) и будущего деплоя warehouse-api.

---

*Задача: WH-16*
*Автор: Flomaster*
*Дата: 26 ноября 2025*