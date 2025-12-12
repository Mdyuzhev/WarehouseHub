# Warehouse Testing

Тестовый репозиторий для Warehouse проекта.

## Структура

```
warehouse-testing/
├── e2e-tests/           # E2E API тесты (RestAssured + JUnit5 + Allure)
├── ui-tests/            # UI тесты (Selenide + JUnit5 + Allure)
├── loadtest/            # Нагрузочные тесты (Locust)
├── k8s/                 # K8s манифесты
│   └── loadtest/        # Locust/K6 в K8s
├── infrastructure/      # Инфраструктура для тестов
│   ├── selenoid/        # Docker Selenium Grid
│   └── allure/          # Allure Report Server
└── scripts/             # Скрипты запуска
```

## Компоненты

### E2E Tests
- **Технологии:** Java 17, RestAssured 5.4, JUnit 5, Allure 2.25
- **Тесты:** Health API, Auth API, Products API
- **Запуск:** `cd e2e-tests && ./mvnw test -Dbase.url=http://192.168.1.74:30080`

### UI Tests
- **Технологии:** Java 17, Selenide 7.0, JUnit 5, Allure 2.25
- **Тесты:** Login, Products, Analytics, Role Access
- **Запуск:** `cd ui-tests && ./mvnw test -Dbase.url=http://192.168.1.74:30081 -Dselenoid.url=http://192.168.1.74:4444/wd/hub`

### Load Tests
- **Технологии:** Python, Locust
- **Сценарии:** 4 роли пользователей, Linear/Step профили нагрузки
- **Запуск:** `locust -f loadtest/locustfile.py --host=http://192.168.1.74:30080`

## Окружения

| Env | API URL | Frontend URL |
|-----|---------|--------------|
| Dev | http://192.168.1.74:31080 | http://192.168.1.74:31081 |
| Prod | http://192.168.1.74:30080 | http://192.168.1.74:30081 |
| Yandex | https://api.wh-lab.ru | https://wh-lab.ru |

## Инфраструктура

### Selenoid
```bash
cd infrastructure/selenoid && docker-compose up -d
# UI: http://192.168.1.74:8090
# API: http://192.168.1.74:4444/wd/hub
```

### Allure
```bash
cd infrastructure/allure && docker-compose up -d
# UI: http://192.168.1.74:5252
# API: http://192.168.1.74:5050
```

## CI/CD

Jobs в `.gitlab-ci.yml`:
- `run-e2e-tests-staging` - E2E на staging
- `run-e2e-tests-prod` - E2E на production
- `run-ui-tests-staging` - UI на staging
- `run-ui-tests-prod` - UI на production
- `run-load-tests` - Нагрузочное тестирование

## Учётные данные

| User | Password | Role |
|------|----------|------|
| admin | admin123 | ADMIN |
| employee | password123 | EMPLOYEE |
