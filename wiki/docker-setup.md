# Docker Setup для warehouse-api

## Обзор

Данный документ описывает настройку Docker для сборки и запуска приложения warehouse-api. Используется multi-stage сборка для оптимизации размера финального образа.

## Задача

WH-17: Создать Dockerfile для warehouse-api

## Архитектура Docker образа

Dockerfile использует двухэтапную сборку (multi-stage build), что позволяет значительно уменьшить размер финального образа.

### Stage 1: Builder

На этапе сборки используется полный JDK 17 (eclipse-temurin:17-jdk-alpine) для компиляции исходного кода. Maven wrapper скачивает зависимости и собирает JAR-файл. Этот этап занимает больше времени при первой сборке, но последующие сборки используют кэш Docker для слоёв с зависимостями.

### Stage 2: Runtime

На этапе выполнения используется облегчённый JRE 17 (eclipse-temurin:17-jre-alpine), который содержит только runtime-компоненты Java без компилятора и инструментов разработки. Это уменьшает размер образа примерно в 2-3 раза.

## Структура файлов

```
warehouse-api/
├── Dockerfile          # Основной файл сборки
├── .dockerignore       # Исключения при сборке
└── src/
    └── main/
        └── resources/
            ├── application.properties      # Конфигурация по умолчанию
            └── application-k8s.properties  # Конфигурация для Kubernetes
```

## Команды сборки

### Локальная сборка образа
```bash
docker build -t warehouse-api:latest .
```

### Сборка с тегом версии
```bash
docker build -t warehouse-api:1.0.0 .
```

### Сборка для GitLab Registry
```bash
docker build -t 192.168.1.74:8080/root/warehouse-api:latest .
```

## Запуск контейнера

### Локальный запуск (подключение к K8s PostgreSQL)
```bash
docker run -d \
  --name warehouse-api \
  -p 8080:8080 \
  -e SPRING_DATASOURCE_URL=jdbc:postgresql://192.168.1.74:30432/warehouse \
  -e SPRING_DATASOURCE_USERNAME=warehouse_user \
  -e SPRING_DATASOURCE_PASSWORD=warehouse_secret_2025 \
  warehouse-api:latest
```

### Запуск с профилем Kubernetes
```bash
docker run -d \
  --name warehouse-api \
  -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=k8s \
  -e DB_USERNAME=warehouse_user \
  -e DB_PASSWORD=warehouse_secret_2025 \
  warehouse-api:latest
```

## Проверка работоспособности

### Health check
```bash
curl http://localhost:8080/actuator/health
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

### Swagger UI
```bash
curl http://localhost:8080/swagger-ui.html
```

Или откройте в браузере: http://localhost:8080/swagger-ui.html

## Переменные окружения

| Переменная | Описание | Значение по умолчанию |
|------------|----------|----------------------|
| SPRING_PROFILES_ACTIVE | Активный профиль Spring | default |
| SPRING_DATASOURCE_URL | JDBC URL базы данных | jdbc:postgresql://192.168.1.74:30432/warehouse |
| SPRING_DATASOURCE_USERNAME | Пользователь БД | warehouse_user |
| SPRING_DATASOURCE_PASSWORD | Пароль БД | warehouse_secret_2025 |
| JAVA_OPTS | Дополнительные параметры JVM | - |

## Особенности безопасности

Образ реализует несколько best practices для безопасности контейнеров.

Во-первых, приложение запускается от непривилегированного пользователя `appuser` (UID 1001), а не от root. Это ограничивает потенциальный ущерб в случае компрометации контейнера.

Во-вторых, используется минимальный базовый образ Alpine Linux, который содержит меньше потенциально уязвимых компонентов.

В-третьих, финальный образ не содержит исходный код, только скомпилированный JAR-файл.

## Оптимизации JVM для контейнеров

В ENTRYPOINT указаны специальные флаги JVM для корректной работы в контейнерах.

Флаг `-XX:+UseContainerSupport` включает поддержку контейнерных лимитов (cgroups), что позволяет JVM корректно определять доступную память и CPU.

Флаг `-XX:MaxRAMPercentage=75.0` ограничивает использование heap до 75% доступной памяти контейнера, оставляя 25% для метаспейса, стеков потоков и нативной памяти.

Флаг `-Djava.security.egd=file:/dev/./urandom` ускоряет генерацию случайных чисел, что важно для быстрого старта приложения.

## Troubleshooting

### Контейнер не запускается

Проверьте логи контейнера:
```bash
docker logs warehouse-api
```

### Ошибка подключения к базе данных

Убедитесь, что PostgreSQL доступен и credentials корректны:
```bash
# Проверка доступности PostgreSQL
nc -zv 192.168.1.74 30432

# Проверка подключения
psql -h 192.168.1.74 -p 30432 -U warehouse_user -d warehouse
```

### Образ слишком большой

Проверьте что .dockerignore настроен корректно и исключает лишние файлы:
```bash
docker history warehouse-api:latest
```

---

*Задача: WH-17*
*Автор: Flomaster*
*Дата: 26 ноября 2025*
