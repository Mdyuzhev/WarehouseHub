# Troubleshooting Guide

Руководство по устранению типичных проблем в проекте warehouse-api.

---

# Обновление от 30 ноября 2025

## Нагрузочное тестирование — Проблемы и решения (WH-103)

### Проблема: BCrypt bottleneck при нагрузочном тестировании

**Симптомы:**
- Login endpoint показывает 20-60% ошибок при нагрузке
- Высокая latency на /api/auth/login (20+ секунд)
- CPU API pod на 100%

**Причина:**
BCrypt использует cost factor 12 по умолчанию, что требует ~250ms CPU на каждый хэш. При высокой нагрузке это становится bottleneck.

**Решение (без изменения кода):**
```bash
# Горизонтальное масштабирование
kubectl scale deployment/warehouse-api -n warehouse --replicas=2
kubectl set resources deployment/warehouse-api -n warehouse --limits=cpu=1500m,memory=1Gi
```

**Результат:** 2 реплики API с 1500m CPU дают 63 RPS и 0% ошибок при 150 concurrent users.

---

### Проблема: PostgreSQL connection exhaustion

**Симптомы:**
```
HikariPool-1 - Connection is not available, request timed out after 30000ms
```

**Причина:**
При 4+ репликах API, каждая с HikariCP pool = 20, общее количество connections превышает max_connections PostgreSQL.

**Диагностика:**
```bash
kubectl exec -n warehouse postgres-0 -- psql -U postgres -d warehouse -c "SELECT count(*) FROM pg_stat_activity;"
kubectl exec -n warehouse postgres-0 -- psql -U postgres -d warehouse -c "SHOW max_connections;"
```

**Решение:**
```bash
# Увеличить max_connections PostgreSQL
kubectl exec -n warehouse postgres-0 -- psql -U postgres -c "ALTER SYSTEM SET max_connections = 200;"
kubectl rollout restart statefulset/postgres -n warehouse

# Уменьшить HikariCP pool per pod
kubectl set env deployment/warehouse-api -n warehouse SPRING_DATASOURCE_HIKARI_MAXIMUM_POOL_SIZE=10
```

---

### Проблема: Locust workers перезапускаются во время теста

**Симптомы:**
- Workers показывают RESTARTS > 0
- Тест прерывается, статистика теряется

**Причина:**
Недостаточно памяти для workers или слишком много virtual users на worker.

**Решение:**
```bash
# Проверить причину рестартов
kubectl describe pod -n loadtest -l app=locust-worker

# Увеличить ресурсы workers
kubectl set resources deployment/locust-worker -n loadtest --limits=cpu=500m,memory=512Mi
```

---

### Проблема: Redis FLUSHALL во время теста

**Симптомы:**
- Внезапный рост latency после очистки Redis
- Первые запросы после flush медленнее

**Причина:**
Кэш Redis очищен, все запросы идут напрямую в PostgreSQL.

**Решение:**
Не очищать Redis во время нагрузочного тестирования. Очистка — только перед началом теста:
```bash
kubectl exec -n warehouse deployment/redis -- redis-cli FLUSHALL
# Подождать прогрев кэша перед началом теста
```

---

### Рекомендуемые лимиты для Production (по результатам WH-103)

| Сценарий | Users | RPS | Error Rate | Конфигурация |
|----------|-------|-----|------------|--------------|
| **Safe** | 150 | 63 | 0% | 2 replicas, 1500m CPU |
| Moderate | 200-250 | 50-60 | <1% | 2 replicas, 1500m CPU |
| Max | 350-400 | 40-50 | <2% | 2 replicas, 1500m CPU |

---

# Обновление от 26 ноября 2025

## CI/CD Pipeline — Проблемы и решения

### Проблема: gitlab-runner не может выполнить sudo k3s ctr images import

**Симптомы:**
```
sudo: a terminal is required to read the password
```
или pipeline зависает на стадии `image`.

**Причина:**
Пользователь `gitlab-runner` не имеет прав sudo для выполнения команд K3s без пароля.

**Решение:**
Создать файл sudoers с разрешениями для конкретных команд:

```bash
sudo bash -c 'cat > /etc/sudoers.d/cicd-automation << EOF
# CI/CD automation for gitlab-runner
gitlab-runner ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images import *
gitlab-runner ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images list
gitlab-runner ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images rm *
gitlab-runner ALL=(ALL) NOPASSWD: /bin/rm -f /tmp/warehouse-api.tar

# Manual deployments for flomaster
flomaster ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images import *
flomaster ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images list
flomaster ALL=(ALL) NOPASSWD: /usr/local/bin/k3s ctr images rm *
EOF'

sudo chmod 440 /etc/sudoers.d/cicd-automation
```

**Best Practice:**
Давать sudo права только для конкретных команд, а не полный NOPASSWD: ALL.

---

### Проблема: permission denied при docker build

**Симптомы:**
```
permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock
```

**Причина:**
Пользователь `gitlab-runner` не входит в группу `docker`.

**Решение:**
```bash
sudo usermod -aG docker gitlab-runner
sudo systemctl restart gitlab-runner
```

**Проверка:**
```bash
sudo -u gitlab-runner docker ps
```

**Best Practice:**
После добавления пользователя в группу необходимо перезапустить сервис, чтобы изменения вступили в силу.

---

### Проблема: cannot remove '/tmp/warehouse-api.tar': Operation not permitted

**Симптомы:**
Pipeline падает на очистке временных файлов после успешного импорта образа.

**Причина:**
Файл создаётся Docker с определёнными правами, и gitlab-runner не может его удалить.

**Решение:**
1. Добавить право на удаление в sudoers (см. выше)
2. В .gitlab-ci.yml использовать:
```yaml
- sudo rm -f /tmp/$IMAGE_NAME.tar || true
```

**Best Practice:**
Использовать `|| true` для некритичных операций очистки, чтобы pipeline не падал.

---

### Проблема: error validating data: failed to download openapi

**Симптомы:**
```
error: error validating "k8s/configmap.yaml": error validating data: failed to download openapi
```

**Причина:**
Пользователь `gitlab-runner` не имеет kubeconfig или не имеет прав на его чтение.

**Решение:**
Скопировать kubeconfig K3s для пользователя gitlab-runner:

```bash
sudo mkdir -p /home/gitlab-runner/.kube
sudo cp /etc/rancher/k3s/k3s.yaml /home/gitlab-runner/.kube/config
sudo chown -R gitlab-runner:gitlab-runner /home/gitlab-runner/.kube
sudo chmod 600 /home/gitlab-runner/.kube/config
```

**Проверка:**
```bash
sudo -u gitlab-runner kubectl get nodes
```

**Best Practice:**
Каждый пользователь, работающий с kubectl, должен иметь свою копию kubeconfig с правильными правами доступа (chmod 600).

---

### Проблема: Pod в статусе 0/1 Running с рестартами

**Симптомы:**
Pod запускается, но не переходит в Ready, происходят рестарты.

**Причина:**
Обычно — приложение не может подключиться к базе данных или отсутствует зависимость.

**Диагностика:**
```bash
# Логи текущего контейнера
kubectl logs -n warehouse -l app=warehouse-api

# Логи предыдущего контейнера (до рестарта)
kubectl logs -n warehouse -l app=warehouse-api --previous

# Описание пода
kubectl describe pod -n warehouse -l app=warehouse-api
```

**Частые причины:**
1. Неверные credentials PostgreSQL
2. PostgreSQL недоступен
3. Отсутствует зависимость spring-boot-starter-actuator (для health probes)

**Решение для actuator:**
Добавить в pom.xml:
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
</dependency>
```

---

### Проблема: ErrImageNeverPull

**Симптомы:**
```
Failed to pull image "warehouse-api:latest": rpc error: code = Unknown desc = failed to pull and unpack image
```

**Причина:**
`imagePullPolicy: Never` указывает K8s использовать локальный образ, но образ не импортирован в containerd K3s.

**Решение:**
```bash
# Экспортировать из Docker
docker save warehouse-api:latest -o /tmp/warehouse-api.tar

# Импортировать в K3s
sudo k3s ctr images import /tmp/warehouse-api.tar

# Проверить
sudo k3s ctr images list | grep warehouse-api
```

**Best Practice:**
K3s использует containerd, а не Docker. Образы из Docker нужно экспортировать и импортировать в containerd.

---

## Инфраструктура — Проблемы и решения

### Проблема: Дублирование компонентов (PostgreSQL, GitLab Runner)

**Симптомы:**
Несколько экземпляров одного сервиса (например, PostgreSQL в Docker и в K8s одновременно).

**Последствия:**
- Путаница при конфигурации (какой использовать?)
- Расход ресурсов
- Потенциальные конфликты портов

**Диагностика:**
```bash
# Docker контейнеры
docker ps --format "table {{.Names}}\t{{.Ports}}"

# K8s pods
kubectl get pods -A

# Helm releases
helm list -A
```

**Решение:**
1. Определить, какой экземпляр использовать
2. Удалить дублирующийся

Удаление Docker контейнера:
```bash
docker stop <container_name>
docker rm <container_name>
```

Удаление Helm release:
```bash
helm uninstall <release_name> -n <namespace>
kubectl delete namespace <namespace>
```

**Best Practice:**
Перед развёртыванием нового компонента проверять, не существует ли он уже в другом месте. Документировать архитектуру в ARCHITECTURE.md.

---

## YouTrack API — Проблемы и решения

### Проблема: 401 Unauthorized при запросе к API

**Симптомы:**
```json
{"error": "Unauthorized", "error_description": "You are not logged in."}
```

**Причина:**
Токен истёк, отозван или неверный.

**Решение:**
1. Создать новый Permanent Token в YouTrack:
   - Profile → Account Security → Tokens → New token
   - Scope: YouTrack
   - Скопировать токен (показывается один раз!)

2. Обновить переменную окружения:
```bash
export YOUTRACK_TOKEN="perm:NEW_TOKEN_HERE"
echo 'export YOUTRACK_TOKEN="perm:NEW_TOKEN_HERE"' >> ~/.bashrc
```

**Проверка:**
```bash
curl -s "http://192.168.1.74:8088/api/admin/projects?fields=id,name" \
  -H "Authorization: Bearer $YOUTRACK_TOKEN" \
  -H "Accept: application/json"
```

**Best Practice:**
Хранить токен в переменной окружения `$YOUTRACK_TOKEN`, а не в коде или командах. При смене токена достаточно обновить одно место.

---

## Конфигурация приложения — Проблемы и решения

### Проблема: Приложение не может подключиться к PostgreSQL после миграции

**Симптомы:**
```
Connection refused to 192.168.1.74:5432
```

**Причина:**
После миграции PostgreSQL из Docker в K8s изменились: порт (5432 → 30432), credentials, hostname.

**Решение:**
Обновить application.properties:

```properties
# Для локальной разработки (NodePort)
spring.datasource.url=jdbc:postgresql://192.168.1.74:30432/warehouse

# Для K8s (ClusterIP) - в application-k8s.properties
spring.datasource.url=jdbc:postgresql://postgres-service.warehouse.svc.cluster.local:5432/warehouse

# Новые credentials
spring.datasource.username=warehouse_user
spring.datasource.password=warehouse_secret_2025
```

**Best Practice:**
Использовать Spring profiles (application-k8s.properties) для разных окружений. В K8s передавать credentials через environment variables из Secrets.

---

## Best Practices — Сводка

### CI/CD Pipeline
1. Давать sudo права только для конкретных команд
2. Добавлять gitlab-runner в группу docker
3. Создавать отдельный kubeconfig для gitlab-runner
4. Использовать `|| true` для некритичных операций
5. Разделять стадии: только main branch для deploy

### Kubernetes
1. Использовать imagePullPolicy: Never для локальных образов
2. Импортировать образы в containerd при использовании K3s
3. Настраивать readiness и liveness probes
4. Хранить secrets в Kubernetes Secrets, не в ConfigMaps

### Инфраструктура
1. Документировать архитектуру (ARCHITECTURE.md)
2. Избегать дублирования компонентов
3. Использовать namespaces для изоляции
4. Хранить чувствительные данные в переменных окружения

### YouTrack интеграция
1. Хранить токен в $YOUTRACK_TOKEN
2. Использовать правильный project ID (0-1 для warehouse)
3. Привязывать коммиты к задачам через #WH-XX в сообщении
