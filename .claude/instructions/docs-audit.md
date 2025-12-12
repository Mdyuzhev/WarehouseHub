# Docs Audit — Ревизия документации

## Когда запускать
- После Epic/User Story
- После архитектурных изменений
- Раз в неделю

## Чеклист

### 1. Код
```bash
# API - новые контроллеры/сервисы
ls /home/flomaster/warehouse-api/src/main/java/com/warehouse/controller/
ls /home/flomaster/warehouse-api/src/main/java/com/warehouse/service/

# Frontend - новые views/компоненты
ls /home/flomaster/warehouse-frontend/src/views/
ls /home/flomaster/warehouse-frontend/src/components/

# Flyway - новые миграции
ls /home/flomaster/warehouse-api/src/main/resources/db/migration/
```

### 2. Инфра
```bash
# K8s - манифесты
ls /home/flomaster/warehouse-master/k8s/warehouse/

# Health
curl -s http://192.168.1.74:30080/actuator/health | jq
curl -s https://api.wh-lab.ru/actuator/health | jq
```

### 3. Обновить документы
| Что изменилось | Обновить |
|----------------|----------|
| Новые endpoints | docs/TESTING.md |
| Новые компоненты | docs/COMPONENTS.md |
| K8s изменения | docs/INFRASTRUCTURE_GUIDE.md |
| Решённые проблемы | docs/TROUBLESHOOTING_GUIDE.md |

### 4. Коммит
```bash
git add docs/
git commit -m "docs: Update documentation after [описание]"
```

## НЕ автоматически
Только по запросу пользователя.
