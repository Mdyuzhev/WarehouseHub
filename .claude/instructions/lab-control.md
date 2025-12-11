# Lab Control - Управление окружениями сервера

> **Версия:** 2.0
> **Сервер:** 192.168.1.74 (24GB RAM)
> **Скрипт:** `/home/flomaster/scripts/lab-control.sh`

---

## ОБЯЗАТЕЛЬНОЕ ПРАВИЛО

**ПЕРЕД началом работы** - поднять нужное окружение
**ПОСЛЕ завершения работы** - остановить окружение
**Если не уверен** - выполнить `lab stop-all` в конце сессии

---

## Режимы работы сервера

| Режим | RAM Used | Экономия vs Baseline | Что работает |
|-------|----------|----------------------|--------------|
| **IDLE** | ~4-5GB | 75% | K3s control plane, Docker daemon |
| **CI/CD** | ~7-9GB | 60% | IDLE + GitLab |
| **FULL** | ~14-16GB | 30% | GitLab + YouTrack + Grafana/Prometheus |
| Baseline (до) | ~22GB | 0% | Всё включено |

---

## Команды управления

### Рабочие сессии

```bash
# Полная рабочая сессия (начало рабочего дня)
lab start-session

# Только CI/CD (для пайплайнов)
lab start-ci

# Завершение сессии (конец рабочего дня)
lab stop-session

# Проверка состояния
lab status
```

### Внешние сервисы

```bash
# GitLab
lab start-gitlab    # +3-4GB RAM
lab stop-gitlab

# YouTrack
lab start-youtrack  # +2-3GB RAM
lab stop-youtrack

# Мониторинг (Grafana + Prometheus)
lab start-monitoring  # +500MB RAM
lab stop-monitoring
```

### K3s окружения

```bash
# Warehouse (production + dev)
lab start-warehouse   # +2GB RAM
lab stop-warehouse

# ErrorLens + Боты
lab start-errorlens   # +800MB RAM
lab stop-errorlens

# Остановить ВСЕ окружения
lab stop-all          # Освобождает ~2.5-3GB RAM
```

---

## Порты после запуска

### После `lab start-session`

| Сервис | URL |
|--------|-----|
| GitLab | http://192.168.1.74:8080 |
| YouTrack | http://192.168.1.74:8088 |
| Grafana | http://192.168.1.74:3001 |

### После `lab start-warehouse`

| Сервис | URL |
|--------|-----|
| Warehouse API | http://192.168.1.74:30080 |
| Warehouse UI | http://192.168.1.74:30081 |

---

## Типичные Workflow

### Работа над Warehouse

```bash
# 1. В начале
lab start-warehouse

# 2. Работа...

# 3. После завершения
lab stop-warehouse
```

### Работа с GitLab/CI

```bash
# 1. Запустить CI/CD режим
lab start-ci

# 2. Работа с GitLab, пайплайны...

# 3. После завершения
lab stop-session
```

### Полная рабочая сессия

```bash
# 1. Начало дня
lab start-session

# 2. Работа весь день...

# 3. Конец дня
lab stop-session
```

---

## Что НЕ останавливается

- `kube-system` - критичная инфраструктура K3s
- `k6-operator` - системный оператор
- StatefulSets (PostgreSQL, Redis) - базы данных остаются работать

---

## Мониторинг ресурсов

```bash
# Проверка RAM
free -h

# Критические пороги:
# < 2GB свободно - СРОЧНО остановить окружения
# 2-5GB свободно - нормально, но запас небольшой
# > 5GB свободно - достаточно места
```

---

## Troubleshooting

### Поды не стартуют

```bash
# 1. Проверить статус
kubectl get pods -n warehouse

# 2. Посмотреть детали
kubectl describe pod <pod-name> -n warehouse

# 3. Если не хватает RAM
lab stop-all
lab start-warehouse
```

### Timeout при ожидании

```bash
# Подождать и проверить вручную
kubectl get pods -n warehouse -w
```

### Команда `lab` не найдена

```bash
# Использовать полный путь
bash /home/flomaster/scripts/lab-control.sh status
```
