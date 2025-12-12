# Задача: Настройка E2E тестирования

## Текущий статус
- API: http://192.168.1.74:31080/ - UP
- Frontend: http://192.168.1.74:31081/ - UP
- База: warehouse_dev (PostgreSQL)
- Kafka: ОТКЛЮЧЕНА в dev (SPRING_AUTOCONFIGURE_EXCLUDE)

## Структура проекта
- Тесты: `testing/`
- API: `api/`
- Frontend: `frontend/`

## Тестовые пользователи

| User | Password | Facility |
|------|----------|----------|
| admin | admin123 | - |
| dc_central_mgr | password123 | DC-C-001 |
| wh_north_op | password123 | WH-C-001 |
| wh_south_op | password123 | WH-C-002 |
| pp_1_op | password123 | PP-C-001 |
| pp_2_op | password123 | PP-C-002 |
| pp_3_op | password123 | PP-C-003 |
| pp_4_op | password123 | PP-C-004 |

## API Endpoints (ключевые)

| Controller | Base | Methods |
|------------|------|---------|
| Auth | /api/auth | login, register, me, logout |
| Receipts | /api/receipts | CRUD + approve, confirm, complete |
| Shipments | /api/shipments | CRUD + approve, ship, deliver |
| IssueActs | /api/issue-acts | CRUD + complete |
| InventoryActs | /api/inventory-acts | CRUD + approve, complete |
| Stock | /api/stock | GET, transfer |
| Products | /api/products | CRUD |
| Facilities | /api/facilities | CRUD |

## State Machines для тестирования

```
Receipt:   DRAFT -> APPROVED -> CONFIRMED -> COMPLETED
Shipment:  DRAFT -> APPROVED -> SHIPPED -> DELIVERED
IssueAct:  DRAFT -> COMPLETED
Inventory: DRAFT -> APPROVED -> COMPLETED
```

## Шаги

1. Изучи структуру `testing/` директории
2. Проверь какие тесты уже есть
3. Создай E2E тесты для основных сценариев:
   - Авторизация разных пользователей
   - CRUD операции с документами (receipts, shipments)
   - Переходы по статусам документов
   - Проверка прав доступа по facility
4. Настрой CI/CD для запуска тестов

## Примеры команд

```bash
# Health check
curl http://192.168.1.74:31080/actuator/health

# Login (получить токен)
curl -X POST http://192.168.1.74:31080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# Получить список receipts (с токеном)
curl http://192.168.1.74:31080/api/receipts \
  -H "Authorization: Bearer <TOKEN>"

# Создать receipt
curl -X POST http://192.168.1.74:31080/api/receipts \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"facilityId":1,"supplierId":1,"items":[...]}'
```

## Критичные правила

| НЕ делать | Делать |
|-----------|--------|
| `docker push` | `docker save \| sudo k3s ctr import -` |
| `git push origin main` | MR через GitLab |
| Flyway без проверки | `ls api/src/main/resources/db/migration/` |

## Deploy (если нужно пересобрать)

### API
```bash
cd api
docker build --no-cache -t warehouse-api:latest .
sudo k3s ctr images rm docker.io/library/warehouse-api:latest 2>/dev/null || true
docker save warehouse-api:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-api -n warehouse-dev
```

### Frontend
```bash
cd frontend
docker build --no-cache -t warehouse-frontend:latest .
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-frontend -n warehouse-dev
```

## Известные особенности

- Kafka отключена в dev через `SPRING_AUTOCONFIGURE_EXCLUDE`
- Flyway миграции начинаются с V2 (V1 удалена из истории)
- Redis работает и используется для кэширования
- Liveness probe: initialDelaySeconds=120 (Spring Boot долго стартует)
