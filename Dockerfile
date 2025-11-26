# =============================================================================
# Dockerfile для warehouse-api (Spring Boot)
# Multi-stage build для оптимизации размера образа
# Задача: WH-17
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build
# -----------------------------------------------------------------------------
FROM eclipse-temurin:17-jdk-alpine AS builder

WORKDIR /app

# Копируем Maven wrapper и pom.xml для кэширования зависимостей
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./

# Делаем mvnw исполняемым и скачиваем зависимости (кэшируется Docker)
RUN chmod +x mvnw && ./mvnw dependency:go-offline -B

# Копируем исходный код
COPY src/ src/

# Собираем JAR без тестов (тесты запускаются в CI)
RUN ./mvnw package -DskipTests -B

# -----------------------------------------------------------------------------
# Stage 2: Runtime
# -----------------------------------------------------------------------------
FROM eclipse-temurin:17-jre-alpine AS runtime

WORKDIR /app

# Создаём пользователя для безопасности (не запускаем от root)
RUN addgroup -g 1001 appgroup && \
    adduser -u 1001 -G appgroup -D appuser

# Копируем JAR из builder stage
COPY --from=builder /app/target/*.jar app.jar

# Устанавливаем владельца
RUN chown -R appuser:appgroup /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Порт приложения
EXPOSE 8080

# Health check для Docker и Kubernetes
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD wget -qO- http://localhost:8080/actuator/health || exit 1

# Запуск приложения с оптимизациями для контейнеров
ENTRYPOINT ["java", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "-jar", "app.jar"]