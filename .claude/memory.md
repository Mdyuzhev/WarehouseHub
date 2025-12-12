# Claude Code Memory - Warehouse API

## Критические знания о проекте

### K3s/Docker Image Caching Issue (WH-22)

**ВАЖНО:** При CI/CD с k3s containerd tar-файлы Docker образов могут не перезаписываться из-за прав доступа.

**Симптомы:**
- Новые контроллеры возвращают 404
- Hash образа в k3s не меняется между сборками
- Старые endpoints работают, новые - нет

**Решение в .gitlab-ci.yml:**
```yaml
# 1. Очистка старых файлов В НАЧАЛЕ с sudo
- sudo rm -f /tmp/warehouse-api*.tar || true

# 2. Уникальное имя файла с commit SHA
- docker save $IMAGE_NAME:$IMAGE_TAG -o /tmp/$IMAGE_NAME-$CI_COMMIT_SHORT_SHA.tar

# 3. Удаление старого образа из k3s
- sudo k3s ctr images rm docker.io/library/$IMAGE_NAME:$IMAGE_TAG || true

# 4. Импорт и очистка с sudo
- sudo k3s ctr images import /tmp/$IMAGE_NAME-$CI_COMMIT_SHORT_SHA.tar
- sudo rm -f /tmp/$IMAGE_NAME-$CI_COMMIT_SHORT_SHA.tar || true
```

### Spring Security с JWT

**Структура:**
- `SecurityConfig.java` - в `com.warehouse.config`
- `JwtService.java`, `JwtAuthenticationFilter.java` - в `com.warehouse.security`
- `CustomUserDetailsService.java` - в `com.warehouse.service`

**AuthController:**
- Использует `@Lazy` для `AuthenticationManager` чтобы избежать circular dependency
- Explicit constructor injection вместо `@RequiredArgsConstructor`

### Profiles

- `test` - H2 in-memory database для тестов
- `k8s` - PostgreSQL в Kubernetes

**application-k8s.properties должен содержать:**
- JWT configuration (jwt.secret, jwt.expiration)
- Database URL для k8s service
- Actuator endpoints exposure

### Тестирование

**Пропущенный тест (WH-24):**
- `shouldReturnBadRequestWhenNameIsEmpty` в `ProductControllerTest`
- Возвращает 403 вместо 400
- Помечен `@Disabled`

### Инфраструктура

- GitLab: http://192.168.1.74:8080
- K8s API: http://192.168.1.74:30080
- YouTrack: http://192.168.1.74:8088
- Namespace: warehouse

### API Endpoints

**Public:**
- POST /api/auth/login
- POST /api/auth/register
- GET /actuator/health

**Authenticated:**
- GET /api/products - все роли
- POST /api/products - SUPER_USER, EMPLOYEE
- DELETE /api/products/{id} - SUPER_USER, EMPLOYEE

**Admin only:**
- /actuator/** (кроме health)
- /api/users/**

### Роли

- SUPER_USER - полный доступ
- ADMIN - управление пользователями, статус системы
- MANAGER - просмотр продуктов, отчёты
- EMPLOYEE - добавление/удаление продуктов

### Тестовые пользователи

| Username | Password | Role |
|----------|----------|------|
| superuser | super123 | SUPER_USER |
| admin | admin123 | ADMIN |
| manager | manager123 | MANAGER |
| employee | employee123 | EMPLOYEE |