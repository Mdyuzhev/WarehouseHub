# 🔍 АУДИТ ПРОЕКТОВ WAREHOUSE

**Дата:** 29 ноября 2025
**Аудитор:** Claude Code
**Версия:** 1.0

---

## 📊 ОБЩАЯ ОЦЕНКА

| Проект | Оценка | Статус |
|--------|--------|--------|
| **warehouse-api** | 7/10 | ⚠️ Требует внимания к безопасности |
| **warehouse-frontend** | 6.5/10 | ⚠️ Требует рефакторинга |

---

# 🔧 WAREHOUSE-API (Spring Boot)

## Структура проекта: ✅ ХОРОШО

```
com.warehouse
├── config/          ✅ Конфигурация
├── controller/      ✅ REST контроллеры
├── dto/             ✅ Data Transfer Objects
├── model/           ✅ Entities
├── repository/      ✅ Data Access Layer
├── security/        ✅ JWT логика
└── service/         ✅ Бизнес-логика
```

Правильная layered architecture, хорошее разделение ответственности.

---

## 🚨 КРИТИЧНЫЕ ПРОБЛЕМЫ

### 1. Захардкодированные секреты в properties

**Файл:** `application.properties`, `application-k8s.properties`

```properties
# ❌ ОПАСНО!
spring.datasource.password=warehouse_secret_2025
jwt.secret=bXlTdXBlclNlY3JldEtleUZvckpXVFRva2VuR2VuZXJhdGlvbjEyMzQ1Njc4OTA=
```

**Решение:**
```properties
spring.datasource.password=${DB_PASSWORD}
jwt.secret=${JWT_SECRET}
```

---

### 2. Уязвимость в AuthController.java (строка 98)

```java
// ❌ Может упасть с StringIndexOutOfBoundsException
String token = authHeader.substring(7);
```

**Решение:**
```java
if (authHeader == null || !authHeader.startsWith("Bearer ") || authHeader.length() < 8) {
    return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
            .body(Map.of("error", "Invalid authorization header"));
}
String token = authHeader.substring(7);
```

---

### 3. Хардкодированные CORS origins в SecurityConfig.java (строки 84-92)

```java
// ❌ IP адреса в коде!
configuration.setAllowedOrigins(Arrays.asList(
    "http://192.168.1.74:30081",
    "http://192.168.1.74:30000"
));
```

**Решение:** Вынести в application.properties:
```properties
cors.allowed-origins=http://localhost:3000,https://wh-lab.ru
```

---

### 4. Чувствительные данные в CI/CD

**Файл:** `.gitlab-ci.yml` (строка 95)

```yaml
# ❌ Путь к локальным секретам в CI!
- cat /home/flomaster/secrets/yc-registry-key.json | docker login ...
```

**Решение:** Использовать GitLab CI/CD Variables.

---

## ⚠️ СРЕДНИЕ ПРОБЛЕМЫ

| # | Проблема | Файл | Строка |
|---|----------|------|--------|
| 5 | Нет валидации в DTOs (@NotBlank, @Size) | AuthRequest.java, RegisterRequest.java | - |
| 6 | deleteProduct не проверяет существование | ProductService.java | - |
| 7 | NoSuchElementException при пустых authorities | JwtService.java | 38 |
| 8 | PUT endpoint объявлен в Security, но не реализован | ProductController.java | - |
| 9 | Отсутствует GET /products/{id} endpoint | ProductController.java | - |
| 10 | Нет глобального ExceptionHandler | - | - |
| 11 | Disabled тест (WH-23) не исправлен | ProductControllerTest.java | 86 |

---

## 📋 НИЗКИЕ ПРОБЛЕМЫ

- Недостаточное логирование в контроллерах
- Отсутствуют Javadoc комментарии
- Нет README.md
- Нет кастомных Exception классов

---

## ✅ ЧТО ХОРОШО

- Spring Boot 3.2.0 (актуальная версия)
- Java 17 LTS
- JWT 0.11.5
- Prometheus метрики интегрированы
- Dockerfile оптимизирован (multi-stage, alpine, non-root user)
- Swagger/OpenAPI документация

---

# 🎨 WAREHOUSE-FRONTEND (Vue.js)

## Структура проекта: ⚠️ ТРЕБУЕТ УЛУЧШЕНИЙ

```
src/
├── components/      ✅ Есть
├── router/          ✅ Есть
├── services/        ✅ Есть
├── stores/          ❌ НЕТ (нужна Pinia)
├── composables/     ❌ НЕТ
├── utils/           ❌ НЕТ
├── __tests__/       ❌ НЕТ (КРИТИЧНО!)
└── assets/          ❌ НЕТ
```

---

## 🚨 КРИТИЧНЫЕ ПРОБЛЕМЫ

### 1. ПОЛНОЕ ОТСУТСТВИЕ ТЕСТОВ

**Покрытие:** 0%
**Файлов с тестами:** 0

Это **абсолютно критично** для production проекта!

**Решение:** Добавить Vitest + Vue Test Utils

---

### 2. Дублирование getApiUrl() в 3 местах

**Файлы:**
- `services/auth.js` (строки 6-17)
- `components/HomePage.vue` (строки 50-55)
- `components/StatusPage.vue` (строки 150-162)

```javascript
// ❌ Повторяется 3 раза!
function getApiUrl() {
  const hostname = window.location.hostname
  if (hostname === 'wh-lab.ru') return 'https://api.wh-lab.ru/api'
  return 'http://192.168.1.74:30080/api'
}
```

**Решение:** Создать `src/utils/apiConfig.js`

---

### 3. Хардкодированные IP адреса

```javascript
// ❌ Везде в коде!
return 'http://192.168.1.74:30080/api'
```

**Решение:** Использовать .env:
```env
VITE_API_URL=http://192.168.1.74:30080
```

---

### 4. Options API вместо Composition API

```vue
<!-- ❌ Устаревший подход -->
export default {
  data() { return { products: [] } },
  methods: { async loadProducts() {} },
  mounted() { this.loadProducts() }
}
```

**Решение:** Мигрировать на `<script setup>`

---

### 5. CI/CD без тестирования

Pipeline деплоит код **без запуска тестов**!

---

## ⚠️ СРЕДНИЕ ПРОБЛЕМЫ

| # | Проблема | Решение |
|---|----------|---------|
| 6 | Нет ESLint/Prettier | Добавить конфиги |
| 7 | Нет Pinia для состояния | Добавить store |
| 8 | Тестовые креды в UI (super123) | Скрыть в production |
| 9 | Vite proxy с хардкодом | Использовать env |
| 10 | Дублирование CSS (роли) | Создать CSS переменные |

---

## 📋 НИЗКИЕ ПРОБЛЕМЫ

- Отсутствует TypeScript
- Нет дизайн-системы
- Нет JSDoc комментариев
- Отсутствует Storybook

---

## ✅ ЧТО ХОРОШО

- Vue 3.4.0 (актуальная версия)
- Vue Router 4
- Vite 5
- Dockerfile оптимизирован (multi-stage, nginx alpine)
- Nginx конфигурация корректная
- Scoped styles используются правильно
- Responsive дизайн

---

# 📈 СВОДНАЯ ТАБЛИЦА ПРОБЛЕМ

## По критичности

| Уровень | API | Frontend | Всего |
|---------|-----|----------|-------|
| 🔴 Критичные | 4 | 5 | **9** |
| 🟡 Средние | 7 | 5 | **12** |
| 🟢 Низкие | 4 | 4 | **8** |
| **Итого** | 15 | 14 | **29** |

## По категориям

| Категория | Кол-во проблем |
|-----------|----------------|
| 🔐 Безопасность | 6 |
| 🧪 Тестирование | 4 |
| 📝 Код/Архитектура | 10 |
| ⚙️ Конфигурация | 5 |
| 🚀 CI/CD | 4 |

---

# 🎯 ПЛАН ИСПРАВЛЕНИЙ

## PHASE 1: КРИТИЧНЫЕ (1-2 недели)

### API:
- [ ] Вынести все секреты в environment variables
- [ ] Защитить endpoint /me от null headers
- [ ] Переместить CORS origins в properties
- [ ] Исправить CI/CD security (GitLab variables)

### Frontend:
- [ ] Добавить Vitest и базовые тесты
- [ ] Создать .env конфигурацию
- [ ] Рефакторить getApiUrl() в один модуль
- [ ] Добавить ESLint

---

## PHASE 2: СРЕДНИЕ (2-3 недели)

### API:
- [ ] Добавить валидацию в DTOs
- [ ] Создать GlobalExceptionHandler
- [ ] Реализовать PUT и GET by ID endpoints
- [ ] Исправить WH-23 тест
- [ ] Добавить unit тесты для JwtService

### Frontend:
- [ ] Мигрировать на Composition API
- [ ] Добавить Pinia для состояния
- [ ] Переделать CI/CD с тестами
- [ ] Скрыть тестовые креды в production

---

## PHASE 3: УЛУЧШЕНИЯ (1 месяц)

### API:
- [ ] Добавить кастомные Exception классы
- [ ] Написать README.md
- [ ] Добавить Javadoc
- [ ] Добавить SAST scanning в CI

### Frontend:
- [ ] Создать дизайн-систему (CSS переменные)
- [ ] Рассмотреть TypeScript миграцию
- [ ] Улучшить структуру папок
- [ ] Добавить component тесты

---

# 📊 МЕТРИКИ ДЛЯ ОТСЛЕЖИВАНИЯ

| Метрика | Сейчас | Цель |
|---------|--------|------|
| API Test Coverage | ~30% | 70%+ |
| Frontend Test Coverage | 0% | 60%+ |
| ESLint Errors (Frontend) | N/A | 0 |
| Security Issues | 6 | 0 |
| Code Duplication | Высокое | Низкое |

---

# 💡 РЕКОМЕНДАЦИИ

## Немедленно (блокирующие production):
1. **Убрать все захардкоженные секреты** - это реальная уязвимость
2. **Добавить хоть какие-то тесты на фронт** - 0% coverage недопустимо
3. **Исправить CI/CD** - нельзя деплоить без тестов

## В течение месяца:
1. Рефакторинг frontend на Composition API
2. Добавить глобальную обработку ошибок в API
3. Настроить proper secrets management

## Долгосрочно:
1. Рассмотреть TypeScript для frontend
2. Добавить E2E тесты (Playwright/Cypress)
3. Внедрить SonarQube для code quality

---

*Отчёт сгенерирован с любовью и сарказмом. Помни: код без тестов - это просто надежда на лучшее! 🎰*

