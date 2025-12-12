# Шаблон постановки задач для Claude

Правила эффективной работы с Claude Code.

---

## Принципы хорошей задачи

### 1. Конкретность
Указывай точно ЧТО нужно сделать, не оставляя места для интерпретации.

### 2. Контекст
Объясни ЗАЧЕМ это нужно и как связано с проектом.

### 3. Критерии готовности
Опиши как проверить что задача выполнена.

---

## Примеры

### Плохо

```
добавь авторизацию
```

### Хорошо

```
Добавь JWT авторизацию в API:
- POST /api/auth/login принимает {username, password}
- Возвращает {token} с временем жизни 24 часа
- Токен проверяется через Redis кэш
- Роли: EMPLOYEE, MANAGER, ADMIN

Проверка: curl -X POST /api/auth/login -d '{"username":"admin","password":"admin123"}'
```

---

### Плохо

```
почини баг
```

### Хорошо

```
При создании Receipt с facilityId=1 возвращается 400.

Ожидаемое: 201 Created
Фактическое: 400 Bad Request

Команда для воспроизведения:
curl -X POST http://192.168.1.74:31080/api/receipts \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"facilityId":1,"items":[{"productId":1,"quantity":10}]}'
```

---

### Плохо

```
напиши тесты
```

### Хорошо

```
Напиши E2E тесты для Receipt API:

1. CRUD операции (create, read, update, delete)
2. State machine (DRAFT → APPROVED → CONFIRMED → COMPLETED)
3. Ролевой доступ (EMPLOYEE создаёт, MANAGER approve)
4. Негативные сценарии (400, 403, 404)

Использовать: REST-assured + JUnit 5
Расположение: testing/e2e-tests/src/test/java/
```

---

### Плохо

```
сделай деплой
```

### Хорошо

```
Задеплой API в warehouse-dev:

1. Собери образ: docker build -t warehouse-api:latest api/
2. Импортируй в k3s: docker save | k3s ctr import
3. Рестарт: kubectl rollout restart deployment/warehouse-api -n warehouse-dev
4. Проверь: curl http://192.168.1.74:31080/actuator/health
```

---

## Структура задачи на фичу

```markdown
## Цель
[Одно предложение - что делаем]

## Контекст
[Почему это нужно, как связано с проектом]

## Требования
- [ ] Требование 1
- [ ] Требование 2
- [ ] Требование 3

## Технические детали
- Файлы: [где создавать/изменять]
- Паттерн: [на какой код ориентироваться]
- Ограничения: [что НЕ делать]

## Проверка
[Команды/действия для проверки]
```

---

## Пример полной задачи

```markdown
## Цель
Добавить API для Issue Acts (акты выдачи в ПВЗ)

## Контекст
Issue Acts - документы выдачи товара клиенту в ПВЗ (Pickup Points).
Часть документооборота Phase 2. После Receipt и Shipment.

## Требования
- [ ] Entity IssueAct + IssueActItem
- [ ] Flyway миграция V10
- [ ] Repository с поиском по facility
- [ ] Service с state machine: DRAFT → COMPLETED
- [ ] На COMPLETED списывать stock (instant, без reserve)
- [ ] Только для facility.type = PP
- [ ] REST Controller: create, getById, getByFacility, complete

## Технические детали
- Файлы: api/src/main/java/com/warehouse/
- Паттерн: Receipt документы (ReceiptDocument.java, ReceiptDocumentService.java)
- НЕ делать: Kafka events, approve этап

## Проверка
curl -X POST http://192.168.1.74:31080/api/issue-acts \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"facilityId":4,"customerName":"Test","items":[{"productId":1,"quantity":1}]}'
# Ожидаем 201, facilityId=4 это PP-C-001
```

---

## Чек-лист перед отправкой

- [ ] Указан конкретный результат
- [ ] Есть контекст (зачем)
- [ ] Перечислены требования
- [ ] Указаны файлы/паттерны
- [ ] Описана проверка

---

## Anti-patterns

| Плохо | Почему | Лучше |
|-------|--------|-------|
| "сделай как надо" | Нет критериев | Конкретные требования |
| "посмотри сам" | Трата времени на анализ | Указать файлы |
| "потом разберёмся" | Неопределённость | Чёткие границы задачи |
| "добавь всё что нужно" | Scope creep | Минимальный MVP |
| "исправь все баги" | Бесконечная задача | Один конкретный баг |

---

## Работа с большими задачами

Разбивай на блоки с чекпоинтами:

```markdown
## Блок 1: Entity + Migration
[Описание]
### Checkpoint: ./mvnw compile

## Блок 2: Service
[Описание]
### Checkpoint: ./mvnw test

## Блок 3: Controller
[Описание]
### Checkpoint: curl проверка

## Блок 4: Deploy
[Описание]
### Checkpoint: health check
```

После каждого блока - проверка и подтверждение.

---

## Формат ответа от Claude

Ожидай структурированный ответ:

1. **Понял задачу** - краткое повторение
2. **План** - шаги выполнения
3. **Выполнение** - код/команды
4. **Проверка** - результат тестов
5. **Итог** - что сделано

---

*Последнее обновление: 2025-12-12*
