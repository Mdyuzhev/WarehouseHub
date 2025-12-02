# Старт работы

## Шаг 0: Проверь репозиторий
```bash
pwd && basename $(git rev-parse --show-toplevel)
```

| Репозиторий | Путь | Назначение |
|-------------|------|------------|
| warehouse-api | ~/warehouse-api | Backend (Java, Spring Boot) |
| warehouse-frontend | ~/warehouse-frontend | Frontend (Vue.js) |
| warehouse-master | ~/warehouse-master | Инфраструктура, Bot, K8s |

Если нужен другой — переключись: `cd ~/warehouse-api`

## Шаг 1: PROJECT_STATUS.md

Единственный обязательный документ. Остальные — по типу задачи.

## Шаг 2: Health check
```bash
curl -s http://192.168.1.74:30080/actuator/health | jq .status
```

## Ответ
```
Репозиторий: XXX
Ветка: XXX
API: UP
Готов!
```

## Критичные правила

1. Проверь репозиторий перед работой
2. K3s ≠ Docker — нужен k3s ctr import
3. Main protected — merge через MR
4. YouTrack — только Basic Auth
5. Docker build — НЕ локально (OOM)
