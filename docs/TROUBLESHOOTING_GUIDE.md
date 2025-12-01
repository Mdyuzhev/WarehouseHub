# Troubleshooting Guide

Руководство по устранению типичных проблем в проекте Warehouse.

---

# Обновление от 1 декабря 2025 (WH-155 QA)

## QA подсистема — Проблемы и решения

### Проблема: E2E тесты не запускаются в CI/CD

**Симптомы:**
```
./mvnw: No such file or directory
```

**Причина:**
Maven Wrapper отсутствует в директории e2e-tests.

**Решение:**
```bash
# Скопировать Maven Wrapper из ui-tests
cp ~/warehouse-master/ui-tests/mvnw ~/warehouse-master/e2e-tests/
cp -r ~/warehouse-master/ui-tests/.mvn ~/warehouse-master/e2e-tests/
chmod +x ~/warehouse-master/e2e-tests/mvnw
git add e2e-tests/mvnw e2e-tests/.mvn
git commit -m "fix: Add Maven Wrapper to e2e-tests"
```

---

### Проблема: Permission denied на pom.xml в CI/CD

**Симптомы:**
```
[ERROR] Error executing Maven
Permission denied
```

**Причина:**
pom.xml имеет неправильные права доступа (600 вместо 644).

**Решение:**
```bash
chmod 644 ~/warehouse-master/e2e-tests/pom.xml
git add e2e-tests/pom.xml
git commit -m "fix: Fix pom.xml permissions"
```

---

### Проблема: AccessDeniedException при компиляции тестов

**Симптомы:**
```
java.nio.file.AccessDeniedException: /builds/.../target/test-classes
```

**Причина:**
Директория target/ принадлежит gitlab-runner от предыдущих запусков.

**Решение:**
```bash
# В .gitlab-ci.yml добавить очистку:
script:
  - rm -rf target/ || true
  - ./mvnw test ...

# Или перезапустить pipeline (новый workspace)
```

---

### Проблема: Allure проект не существует

**Симптомы:**
```
Project 'e2e-staging' does not exist
```

**Решение:**
```bash
# Создать проект через API
curl -X POST "http://192.168.1.74:5050/allure-docker-service/projects" \
  -H "Content-Type: application/json" \
  -d '{"id": "e2e-staging"}'
```

**Все 4 проекта:**
- e2e-staging
- e2e-prod
- ui-staging
- ui-prod

**Публичный доступ к Allure:**
- Внутренний URL: http://192.168.1.74:5050
- Внешний URL: https://advertiser-dark-remaining-sail.trycloudflare.com
- Cloudflared tunnel: `nohup cloudflared tunnel --url http://localhost:5050 &`

---

### Проблема: Отчёт Allure не обновляется

**Симптомы:**
Запуск тестов прошёл, но в Allure UI старый отчёт.

**Диагностика:**
```bash
# Проверить статистику через API
curl -s "http://192.168.1.74:5050/allure-docker-service/projects/e2e-staging/reports/latest/widgets/summary.json"
```

**Решение:**
1. Проверить, что RESULTS_DIRECTORY в CI правильный
2. Проверить, что generate-report вызван после upload
3. Очистить кэш браузера (Ctrl+Shift+R)

---

### Проблема: QA кнопки в боте не работают

**Симптомы:**
Кнопка "🔬 QA" не отвечает или выдаёт ошибку.

**Диагностика:**
```bash
kubectl logs -n notifications deployment/gitlab-telegram-bot --tail=100 | grep -i qa
```

**Решение:**
```bash
# Проверить handlers/__init__.py содержит testing router
# Проверить keyboards.py содержит qa_menu_keyboard()
# Передеплоить бота
kubectl rollout restart deployment/gitlab-telegram-bot -n notifications
```

---

### Проблема: Тесты проходят локально, но падают в CI

**Симптомы:**
Локально `./mvnw test` проходит, в GitLab падает.

**Причины:**
1. Разные BASE_URL (staging vs localhost)
2. Selenoid недоступен из CI
3. Разные версии Java/Maven

**Решение:**
```bash
# Проверить переменные в .gitlab-ci.yml
variables:
  BASE_URL: "http://192.168.1.74:30080"
  SELENOID_URL: "http://192.168.1.74:4444/wd/hub"

# Проверить доступность Selenoid
curl http://192.168.1.74:4444/wd/hub/status
```

---

## Новые компоненты (WH-120, WH-121, WH-122)

### Warehouse Robot — Проблемы и решения

#### Проблема: Robot Service недоступен снаружи кластера

**Симптомы:**
```bash
curl http://192.168.1.74:30070/health
# Пустой ответ или connection refused
```

**Причина:**
Рассогласование меток между Pod и Service selector. Service был применён через Kustomize с `commonLabels`, а Deployment напрямую.

**Решение:**
```bash
# Удалить и переприменить через Kustomize
kubectl delete deployment warehouse-robot -n warehouse
kubectl delete svc warehouse-robot-service -n warehouse
kubectl apply -k ~/warehouse-master/k8s/robot/

# Проверить
kubectl get pods -n warehouse -l app=warehouse-robot
curl http://192.168.1.74:30070/health
```

**Best Practice:**
При использовании `commonLabels` в kustomization.yaml ВСЕ ресурсы должны применяться через `kubectl apply -k`, а не напрямую.

---

#### Проблема: Robot не может подключиться к Warehouse API

**Симптомы:**
```
HTTPError: 401 Unauthorized
Connection refused to warehouse-api-service:8080
```

**Диагностика:**
```bash
# Проверить секреты
kubectl get secret warehouse-robot-secrets -n warehouse -o yaml

# Проверить подключение
kubectl exec -n warehouse deployment/warehouse-robot -- curl -s http://warehouse-api-service:8080/actuator/health
```

**Решение:**
1. Проверить, что секреты созданы:
```bash
kubectl apply -f ~/warehouse-master/k8s/robot/robot-secrets.yaml
```

2. Проверить credentials:
```bash
kubectl get secret warehouse-robot-secrets -n warehouse -o jsonpath='{.data.employee-username}' | base64 -d
```

---

#### Проблема: Уведомления от Robot не приходят в Telegram

**Симптомы:**
Сценарий выполняется, но уведомление в чат не приходит.

**Диагностика:**
```bash
# Логи Robot
kubectl logs -n warehouse deployment/warehouse-robot --tail=50

# Проверить URL Telegram бота
kubectl get deployment warehouse-robot -n warehouse -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="ROBOT_TELEGRAM_BOT_URL")].value}'
```

**Решение:**
URL должен быть: `http://gitlab-telegram-bot.notifications.svc.cluster.local:8000`

---

### Analytics Service — Проблемы и решения

#### Проблема: WebSocket не подключается

**Симптомы:**
Frontend показывает "Отключено", WebSocket не устанавливается.

**Диагностика:**
```bash
# Health check
curl http://192.168.1.74:30091/health

# Проверить WebSocket (wscat)
wscat -c ws://192.168.1.74:30091/ws
```

**Причина:**
1. Analytics Service не запущен
2. Kafka не доступен
3. Redis не доступен

**Решение:**
```bash
# Проверить поды
kubectl get pods -n warehouse -l app=analytics-service

# Логи
kubectl logs -n warehouse deployment/analytics-service --tail=100

# Проверить Kafka и Redis
kubectl exec -n warehouse deployment/analytics-service -- curl -s redis:6379
kubectl exec -n warehouse deployment/kafka -- kafka-topics.sh --list --bootstrap-server localhost:9092
```

---

#### Проблема: Analytics не получает события из Kafka

**Симптомы:**
Analytics Service работает, но события не появляются в feed.

**Диагностика:**
```bash
# Проверить топики
kubectl exec -n warehouse deployment/kafka -- kafka-topics.sh --list --bootstrap-server localhost:9092

# Проверить consumer groups
kubectl exec -n warehouse deployment/kafka -- kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list

# Просмотреть сообщения
kubectl exec -n warehouse deployment/kafka -- kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic warehouse.audit --from-beginning --max-messages 5
```

**Решение:**
1. Убедиться, что топики созданы:
```bash
kubectl exec -n warehouse deployment/kafka -- kafka-topics.sh --create --topic warehouse.audit --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
kubectl exec -n warehouse deployment/kafka -- kafka-topics.sh --create --topic warehouse.notifications --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

2. Проверить, что API отправляет события (в логах API):
```bash
kubectl logs -n warehouse deployment/warehouse-api --tail=100 | grep -i kafka
```

---

### Telegram Bot Robot — Проблемы и решения

#### Проблема: Кнопки Robot не работают

**Симптомы:**
При нажатии на кнопку ничего не происходит или ошибка "Не удалось подключиться к Robot API".

**Диагностика:**
```bash
# Логи бота
kubectl logs -n notifications deployment/gitlab-telegram-bot --tail=100

# Проверить ROBOT_API_URL
kubectl get deployment gitlab-telegram-bot -n notifications -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="ROBOT_API_URL")].value}'
```

**Решение:**
```bash
# Проверить, что Robot доступен из namespace notifications
kubectl exec -n notifications deployment/gitlab-telegram-bot -- curl -s http://warehouse-robot-service.warehouse.svc.cluster.local:8070/health
```

---

### K3s Image Update — Проблемы и решения

#### Проблема: K3s использует старый образ после пересборки

**Симптомы:**
После `docker build` и перезапуска pod, pod запускается со старым кодом.

**Причина:**
K3s использует containerd, а не Docker. `imagePullPolicy: Never` означает, что K3s берёт образ из containerd, а не из Docker cache.

**Решение (ОБЯЗАТЕЛЬНЫЙ процесс):**
```bash
# 1. Удалить старый Docker образ
docker rmi IMAGE:TAG 2>/dev/null || true

# 2. Собрать без кэша
docker build --no-cache -t IMAGE:TAG .

# 3. Удалить из K3s containerd
sudo k3s ctr images rm docker.io/library/IMAGE:TAG

# 4. Импортировать в K3s
docker save IMAGE:TAG | sudo k3s ctr images import -

# 5. Перезапустить pod
kubectl delete pod -n NAMESPACE -l app=APP_LABEL

# 6. ПРОВЕРИТЬ (обязательно!)
kubectl exec -n NAMESPACE deployment/DEPLOY -- grep 'PATTERN' FILE
```

**One-liner:**
```bash
docker rmi IMAGE:TAG; docker build --no-cache -t IMAGE:TAG . && sudo k3s ctr images rm docker.io/library/IMAGE:TAG; docker save IMAGE:TAG | sudo k3s ctr images import - && kubectl delete pod -n NAMESPACE -l app=APP_LABEL
```

---

### YouTrack API — Проблемы и решения

#### Проблема: OAuth и /api/users/login не работают

**Симптомы:**
```json
{"error": "invalid_grant"}
```

**Причина:**
В текущей конфигурации YouTrack OAuth отключен или не настроен.

**Решение:**
**ИСПОЛЬЗОВАТЬ ТОЛЬКО Basic Auth!**
```bash
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-120'
```

**Best Practice:**
Все запросы к YouTrack API делать через Basic Auth с `-u 'user:password'`.

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
1. Хранить токен в $YOUTRACK_TOKEN или использовать Basic Auth
2. Использовать правильный project ID (0-1 для warehouse)
3. Привязывать коммиты к задачам через #WH-XX в сообщении
4. **ТОЛЬКО Basic Auth!** OAuth не работает

---

---

### Проблема: Allure отчёт показывает JSON вместо HTML

**Симптомы:**
При клике на ссылку в Telegram открывается JSON:
```json
{"data":{"project":"e2e-staging"...}}
```

**Причина:**
URL не содержит `/index.html` на конце.

**Решение:**
Правильный URL должен быть:
```
https://advertiser-dark-remaining-sail.trycloudflare.com/allure-docker-service/projects/e2e-staging/reports/latest/index.html
```

Исправить в `services/allure.py`:
```python
def get_allure_report_url(project_id: str = "warehouse-api") -> str:
    return f"{ALLURE_PUBLIC_URL}/allure-docker-service/projects/{project_id}/reports/latest/index.html"
```

---

### Проблема: get_allure_report_url() takes 0 positional arguments but 1 was given

**Симптомы:**
```
TypeError: get_allure_report_url() takes 0 positional arguments but 1 was given
```

**Причина:**
Функция `get_allure_report_url()` не принимает параметр `project_id`.

**Решение:**
Обновить `services/allure.py`:
```python
# Было
def get_allure_report_url() -> str:
    return f"{ALLURE_SERVER_URL}/allure-docker-service/projects/warehouse-api/reports/latest"

# Стало
def get_allure_report_url(project_id: str = "warehouse-api") -> str:
    return f"{ALLURE_PUBLIC_URL}/allure-docker-service/projects/{project_id}/reports/latest/index.html"
```

---

*Последнее обновление: 2025-12-01 (WH-120 Robot, WH-121 Analytics, WH-122 Schedule, WH-155 QA v5.4)*
