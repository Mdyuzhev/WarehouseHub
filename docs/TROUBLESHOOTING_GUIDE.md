# Troubleshooting Guide

Руководство по устранению типичных проблем в проекте Warehouse.

> Обновлено: 2025-12-02 (WH-200 Dual Environment CI/CD)

---

## Оглавление

1. [Общие принципы диагностики](#общие-принципы-диагностики)
2. [Dev-окружение (WH-192)](#dev-окружение-wh-192)
3. [Dual Environment CI/CD (WH-200)](#dual-environment-cicd-wh-200)
4. [QA подсистема](#qa-подсистема-wh-155)
5. [Warehouse Robot (WH-120)](#warehouse-robot-wh-120)
6. [Analytics Service (WH-121)](#analytics-service-wh-121)
7. [Telegram Bot](#telegram-bot)
8. [K3s и образы](#k3s-и-образы)
9. [CI/CD Pipeline](#cicd-pipeline)
10. [Нагрузочное тестирование](#нагрузочное-тестирование)
11. [YouTrack API](#youtrack-api)
12. [Конфигурация приложений](#конфигурация-приложений)
13. [Frontend](#frontend)
14. [Best Practices](#best-practices)

---

## Общие принципы диагностики

### Шаг 1: Проверить статус сервисов

```bash
# Все поды
kubectl get pods -A

# Конкретный namespace
kubectl get pods -n warehouse

# Детали пода
kubectl describe pod -n warehouse <pod-name>
```

### Шаг 2: Проверить логи

```bash
# Логи пода
kubectl logs -n warehouse <pod-name> --tail=100

# Логи предыдущего контейнера (после рестарта)
kubectl logs -n warehouse <pod-name> --previous

# Follow логов
kubectl logs -n warehouse -l app=warehouse-api -f
```

### Шаг 3: Проверить health endpoints

```bash
# API
curl -s http://192.168.1.74:30080/actuator/health | jq

# Robot
curl -s http://192.168.1.74:30070/health | jq

# Analytics
curl -s http://192.168.1.74:30091/health | jq
```

### Шаг 4: Проверить сетевую связность

```bash
# Из пода в другой сервис
kubectl exec -n warehouse deployment/warehouse-api -- curl -s http://redis:6379

# DNS resolution
kubectl exec -n warehouse deployment/warehouse-api -- nslookup postgres-service
```

---

## Dev-окружение (WH-192)

### Проблема: Сервисы dev не доступны по портам 31xxx

**Симптомы:**
```bash
curl http://192.168.1.74:31080/actuator/health
# Connection refused
```

**Диагностика:**
```bash
# Проверить namespace warehouse-dev
kubectl get all -n warehouse-dev

# Проверить сервисы
kubectl get svc -n warehouse-dev

# Проверить endpoints
kubectl get endpoints -n warehouse-dev
```

**Причины:**
1. Namespace warehouse-dev не создан
2. Deployment не существует в dev namespace
3. NodePort сервис не настроен

**Решение:**
```bash
# Создать namespace если нет
kubectl create namespace warehouse-dev

# Применить манифесты dev окружения
kubectl apply -k ~/warehouse-master/k8s/dev/

# Проверить что сервисы используют правильные порты
kubectl get svc -n warehouse-dev -o wide
```

**Порты dev-окружения:**
| Сервис | NodePort |
|--------|----------|
| API | 31080 |
| Frontend | 31081 |
| Robot | 31070 |
| Analytics | 31091 |

---

### Проблема: Dev и Prod используют одни и те же данные

**Симптомы:**
Изменения в dev появляются в prod и наоборот.

**Причина:**
Dev использует тот же PostgreSQL и Redis что и prod.

**Диагностика:**
```bash
# Проверить DATABASE_URL в dev deployment
kubectl get deployment warehouse-api -n warehouse-dev -o jsonpath='{.spec.template.spec.containers[0].env[?(@.name=="DATABASE_URL")].value}'
```

**Решение:**
Dev окружение должно использовать отдельную базу данных:
```yaml
# Для изоляции данных:
# 1. Отдельная база в том же PostgreSQL
spring.datasource.url=jdbc:postgresql://postgres-service:5432/warehouse_dev

# 2. Или отдельный StatefulSet PostgreSQL в warehouse-dev namespace
```

---

### Проблема: ResourceQuota превышена в dev

**Симптомы:**
```
Error from server (Forbidden): exceeded quota: dev-quota
```

**Диагностика:**
```bash
kubectl describe resourcequota -n warehouse-dev
```

**Решение:**
```bash
# Проверить текущее использование
kubectl get resourcequota -n warehouse-dev -o yaml

# ResourceQuota для warehouse-dev:
# - 4 CPU
# - 8Gi Memory

# Уменьшить ресурсы deployment
kubectl set resources deployment/warehouse-api -n warehouse-dev --limits=cpu=500m,memory=512Mi
```

---

## Dual Environment CI/CD (WH-200)

### Проблема: Pipeline не деплоит в dev автоматически

**Симптомы:**
Push в develop branch, но deploy-dev job не запускается.

**Диагностика:**
```bash
# Проверить что push был в develop
git log --oneline -5

# Проверить GitLab CI jobs
# GitLab UI → CI/CD → Pipelines
```

**Причины:**
1. Push был не в develop branch
2. Job правило не совпадает
3. Pipeline stage зависит от failed job

**Решение:**
Проверить `.gitlab-ci.yml`:
```yaml
deploy-dev:
  stage: deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"  # Должно быть именно develop
  # ...
```

---

### Проблема: deploy-prod не появляется для ручного запуска

**Симптомы:**
Push в main, но кнопка "Play" для deploy-prod отсутствует.

**Диагностика:**
```bash
# Проверить branch
git branch --show-current

# Проверить CI rules
```

**Причина:**
Job deploy-prod имеет `when: manual` только для main branch.

**Решение:**
```yaml
deploy-prod:
  stage: deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual  # Обязательно для prod!
```

Убедиться что:
1. Push именно в main
2. package-image job завершился успешно (dependencies)

---

### Проблема: Health check failed в CI pipeline

**Симптомы:**
```
Health check warning
curl: (7) Failed to connect
```

**Диагностика:**
```bash
# Проверить что pod запустился
kubectl get pods -n warehouse-dev -l app=warehouse-api

# Проверить логи
kubectl logs -n warehouse-dev deployment/warehouse-api --tail=50
```

**Причины:**
1. Pod ещё не готов (startup time)
2. Service не маршрутизирует на pod
3. Неверный URL в переменной

**Решение:**
```bash
# Увеличить sleep в pipeline (по умолчанию 10s)
# Или добавить retry в health check

# Проверить URL
echo $DEV_API_URL  # должен быть http://192.168.1.74:31080
echo $PROD_API_URL # должен быть http://192.168.1.74:30080
```

---

### Проблема: GitLab Environment не обновляется

**Симптомы:**
В GitLab → Deployments → Environments статус устаревший.

**Решение:**
```bash
# Environments обновляются автоматически при успешном deploy job
# Проверить что job имеет блок environment:
deploy-dev:
  environment:
    name: development
    url: $DEV_API_URL

deploy-prod:
  environment:
    name: production
    url: $PROD_API_URL
```

---

### Проблема: Merge Request из develop в main требует ручной деплой

**Симптомы:**
После merge develop→main, prod не обновляется автоматически.

**Объяснение:**
Это **ожидаемое поведение**! Деплой в prod всегда ручной (`when: manual`).

**Workflow:**
```
develop → auto deploy → warehouse-dev (31xxx)
        ↓
    MR в main
        ↓
main → manual deploy → warehouse (30xxx)
```

**Запуск prod deploy:**
1. GitLab → CI/CD → Pipelines
2. Найти pipeline от merge в main
3. Нажать "Play" на job deploy-prod

---

### Проблема: Образ latest не обновился после pipeline

**Симптомы:**
Pipeline успешен, но pod использует старый код.

**Диагностика:**
```bash
# Проверить версию образа в containerd
sudo k3s ctr images list | grep warehouse-api

# Проверить что pod перезапустился
kubectl get pods -n warehouse -l app=warehouse-api -o wide
```

**Причина:**
K3s кэширует образы. `imagePullPolicy: Never` означает что K3s не перезапрашивает образ.

**Решение:**
Pipeline должен включать:
```yaml
# 1. Удаление старого образа из K3s
- sudo k3s ctr images rm docker.io/library/$IMAGE_NAME:latest || true

# 2. Импорт нового
- docker save $IMAGE_NAME:latest -o /tmp/$IMAGE_NAME.tar
- sudo k3s ctr images import /tmp/$IMAGE_NAME.tar

# 3. Rollout restart (принудительный перезапуск pods)
- kubectl rollout restart deployment/warehouse-api -n $NAMESPACE
```

---

## QA подсистема (WH-155)

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

### Проблема: Allure отчёт показывает JSON вместо HTML

**Симптомы:**
При клике на ссылку в Telegram открывается JSON.

**Причина:**
URL не содержит `/index.html` на конце.

**Решение:**
Правильный URL должен быть:
```
https://advertiser-dark-remaining-sail.trycloudflare.com/allure-docker-service/projects/e2e-staging/reports/latest/index.html
```

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

## Warehouse Robot (WH-120)

### Проблема: Robot Service недоступен снаружи кластера

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

### Проблема: Robot не может подключиться к Warehouse API

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

### Проблема: Уведомления от Robot не приходят в Telegram

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

## Analytics Service (WH-121)

### Проблема: WebSocket не подключается

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

### Проблема: Analytics не получает события из Kafka

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

### Проблема: Analytics показывает 0 клиентов WebSocket

**Симптомы:**
```json
{"websocket_clients": 0}
```

**Диагностика:**
```bash
# Проверить что frontend правильно подключается
# Открыть http://192.168.1.74:30081/analytics
# Проверить в DevTools → Network → WS
```

**Решение:**
Проверить что `window.__ANALYTICS_URL__` в frontend правильно определяется:
```javascript
// В index.html должно быть
window.__ANALYTICS_URL__ = 'http://192.168.1.74:30091';
```

---

## Telegram Bot

### Проблема: Кнопки Robot не работают

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

### Проблема: Bot не отвечает на команды

**Симптомы:**
Бот онлайн, но не реагирует на /start, /status и т.д.

**Диагностика:**
```bash
# Логи
kubectl logs -n notifications deployment/gitlab-telegram-bot --tail=100 -f

# Проверить health
curl -s http://192.168.1.74:30088/health
```

**Причины:**
1. Неверный BOT_TOKEN
2. Webhook не настроен
3. Ошибка в обработчиках

**Решение:**
```bash
# Проверить секреты
kubectl get secret gitlab-telegram-bot-secret -n notifications -o yaml

# Перезапустить бота
kubectl rollout restart deployment/gitlab-telegram-bot -n notifications
```

---

## K3s и образы

### Проблема: K3s использует старый образ после пересборки

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
kubectl exec -n NAMESPACE deployment/DEPLOY -- cat /app/VERSION
```

**One-liner:**
```bash
docker rmi IMAGE:TAG; docker build --no-cache -t IMAGE:TAG . && sudo k3s ctr images rm docker.io/library/IMAGE:TAG; docker save IMAGE:TAG | sudo k3s ctr images import - && kubectl delete pod -n NAMESPACE -l app=APP_LABEL
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

---

## CI/CD Pipeline

### Проблема: gitlab-runner не может выполнить sudo k3s ctr images import

**Симптомы:**
```
sudo: a terminal is required to read the password
```

**Причина:**
Пользователь `gitlab-runner` не имеет прав sudo для выполнения команд K3s без пароля.

**Решение:**
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

---

### Проблема: error validating data: failed to download openapi

**Симптомы:**
```
error: error validating "k8s/configmap.yaml": error validating data: failed to download openapi
```

**Причина:**
Пользователь `gitlab-runner` не имеет kubeconfig или не имеет прав на его чтение.

**Решение:**
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

---

## Нагрузочное тестирование

### Проблема: BCrypt bottleneck при нагрузочном тестировании

**Симптомы:**
- Login endpoint показывает 20-60% ошибок при нагрузке
- Высокая latency на /api/auth/login (20+ секунд)
- CPU API pod на 100%

**Причина:**
BCrypt использует cost factor 12 по умолчанию, что требует ~250ms CPU на каждый хэш.

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

### Рекомендуемые лимиты для Production (по результатам WH-103)

| Сценарий | Users | RPS | Error Rate | Конфигурация |
|----------|-------|-----|------------|--------------|
| **Safe** | 150 | 63 | 0% | 2 replicas, 1500m CPU |
| Moderate | 200-250 | 50-60 | <1% | 2 replicas, 1500m CPU |
| Max | 350-400 | 40-50 | <2% | 2 replicas, 1500m CPU |

---

## YouTrack API

### Проблема: 401 Unauthorized при запросе к API

**Симптомы:**
```json
{"error": "Unauthorized", "error_description": "You are not logged in."}
```

**Причина:**
Токен истёк, отозван или неверный.

**Решение:**
**ИСПОЛЬЗОВАТЬ ТОЛЬКО Basic Auth!**
```bash
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-120'
```

---

### Проблема: OAuth и /api/users/login не работают

**Симптомы:**
```json
{"error": "invalid_grant"}
```

**Причина:**
В текущей конфигурации YouTrack OAuth отключен или не настроен.

**Решение:**
**ИСПОЛЬЗОВАТЬ ТОЛЬКО Basic Auth!**
Все запросы к YouTrack API делать через Basic Auth с `-u 'user:password'`.

---

## Конфигурация приложений

### Проблема: Приложение не может подключиться к PostgreSQL

**Симптомы:**
```
Connection refused to 192.168.1.74:5432
```

**Причина:**
Неверный хост или порт PostgreSQL.

**Решение:**

Для K8s deployment (application-k8s.properties):
```properties
spring.datasource.url=jdbc:postgresql://postgres-service.warehouse.svc.cluster.local:5432/warehouse
spring.datasource.username=warehouse_user
spring.datasource.password=warehouse_secret_2025
```

Для локальной разработки (application.properties):
```properties
spring.datasource.url=jdbc:postgresql://192.168.1.74:30432/warehouse
spring.datasource.username=warehouse_user
spring.datasource.password=warehouse_secret_2025
```

---

### Проблема: Pod в статусе 0/1 Running с рестартами

**Симптомы:**
Pod запускается, но не переходит в Ready, происходят рестарты.

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

---

## Frontend

### Проблема: API URL определяется неверно

**Симптомы:**
Frontend делает запросы на неправильный URL.

**Диагностика:**
Открыть DevTools → Console:
```javascript
console.log(window.__API_URL__)
console.log(window.__ANALYTICS_URL__)
```

**Решение:**
Проверить index.html содержит правильный скрипт:
```html
<script>
  (function() {
    var host = window.location.hostname;
    if (host === 'wh-lab.ru' || host === 'www.wh-lab.ru') {
      window.__API_URL__ = 'https://api.wh-lab.ru/api';
      window.__ANALYTICS_URL__ = 'https://analytics.wh-lab.ru';
    } else if (host === '192.168.1.74') {
      window.__API_URL__ = 'http://192.168.1.74:30080/api';
      window.__ANALYTICS_URL__ = 'http://192.168.1.74:30091';
    } else {
      window.__API_URL__ = 'http://' + host + ':30080/api';
      window.__ANALYTICS_URL__ = 'http://' + host + ':30091';
    }
  })();
</script>
```

---

### Проблема: CORS ошибки в браузере

**Симптомы:**
```
Access to fetch at 'http://...' from origin 'http://...' has been blocked by CORS policy
```

**Решение:**
Проверить что origin добавлен в CORS настройки API (application.properties):
```properties
cors.allowed-origins=http://localhost:3000,http://localhost:5173,http://192.168.1.74:30081,https://wh-lab.ru
```

---

## Best Practices

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
5. Использовать Kustomize для применения манифестов с commonLabels

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

### K3s / containerd
1. Всегда удалять старый образ из containerd перед импортом
2. Использовать `--no-cache` при docker build для обновлений
3. Проверять что новый код действительно в контейнере после деплоя
4. Помнить: K3s ≠ Docker!

### Тестирование
1. Использовать отдельные Allure проекты для staging и prod
2. Запускать тесты через Telegram Bot для tracking
3. Проверять Selenoid доступность перед UI тестами
4. Хранить скриншоты при падении тестов

---

---

## Конфигурация через .env (WH-183)

### Проблема: Переменные окружения не применяются

**Симптомы:**
Сервис использует значения по умолчанию вместо `.env`.

**Причина:**
Файл `.env` не создан или не в той директории.

**Решение:**
```bash
# Создать .env из шаблона
cp .env.example .env

# Проверить что .env загружается
docker run --env-file .env ...
```

---

### Проблема: Секреты случайно закоммичены

**Симптомы:**
В git history видны пароли или токены.

**Решение:**
```bash
# Проверить .gitignore
cat .gitignore | grep -E "\.env|secrets"

# Удалить из истории (BFG Repo-Cleaner)
bfg --delete-files .env

# Или через git filter-branch
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

**Профилактика (WH-184):**
Все секретные файлы уже в `.gitignore`:
- `.env`, `*.env.local`
- `credentials.json`, `secrets.yaml`
- `*.pem`, `*.key`, `*.crt`

---

## Locust (WH-185)

### Проблема: Дублирование Locust файлов

**Симптомы:**
Разные сценарии в `loadtest/` и `PerformanceTesting/`.

**Решение (WH-185):**
```bash
# Теперь PerformanceTesting/configs/locustfile.py - это симлинк
ls -la PerformanceTesting/configs/locustfile.py
# lrwxrwxrwx -> ../../loadtest/locustfile.py

# Единственный источник истины:
loadtest/locustfile.py
```

---

### Проблема: JWT токен истекает во время нагрузочного теста

**Симптомы:**
```
401 Unauthorized after 24 hours
```

**Решение:**
Унифицированный `locustfile.py` использует кэширование с thread-safe lock:
```python
_token_cache = {}
_token_lock = threading.Lock()

def get_cached_token(self):
    with _token_lock:
        if username in _token_cache:
            return _token_cache[username]
```

---

*Последнее обновление: 2025-12-02 (WH-200 Dual Environment CI/CD)*
