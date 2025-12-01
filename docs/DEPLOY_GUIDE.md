# Deploy Guide

> Все процедуры деплоя для проекта Warehouse. Обновлено: 2025-12-01

---

## КРИТИЧЕСКИ ВАЖНО: K3s использует containerd, НЕ Docker!

При `imagePullPolicy: Never` K3s берёт образ из containerd, а не из Docker cache.
Простой `docker build` недостаточен!

---

## Универсальный процесс деплоя в K3s

```bash
# Шаг 1: Узнать текущий тег образа
kubectl get deployment DEPLOY -n NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}'

# Шаг 2: Удалить старый Docker образ
docker rmi IMAGE:TAG 2>/dev/null || true

# Шаг 3: Собрать без кэша
docker build --no-cache -t IMAGE:TAG .

# Шаг 4: Удалить из K3s containerd
sudo k3s ctr images rm docker.io/library/IMAGE:TAG

# Шаг 5: Импортировать в K3s
docker save IMAGE:TAG | sudo k3s ctr images import -

# Шаг 6: Перезапустить pod
kubectl delete pod -n NAMESPACE -l app=APP_LABEL

# Шаг 7: ПРОВЕРИТЬ (обязательно!)
kubectl exec -n NAMESPACE deployment/DEPLOY -- grep 'PATTERN' FILE
```

### One-liner

```bash
docker rmi IMAGE:TAG; docker build --no-cache -t IMAGE:TAG . && sudo k3s ctr images rm docker.io/library/IMAGE:TAG; docker save IMAGE:TAG | sudo k3s ctr images import - && kubectl delete pod -n NAMESPACE -l app=APP_LABEL
```

---

## Конкретные сервисы

### Telegram Bot (v5.4)

```bash
cd ~/warehouse-master/telegram-bot

# Деплой
docker rmi gitlab-telegram-bot:v5.4 2>/dev/null || true
docker build --no-cache -t gitlab-telegram-bot:v5.4 .
sudo k3s ctr images rm docker.io/library/gitlab-telegram-bot:v5.4 2>/dev/null || true
docker save gitlab-telegram-bot:v5.4 | sudo k3s ctr images import -
kubectl delete pod -n notifications -l app=gitlab-telegram-bot

# Проверка
kubectl logs -n notifications deployment/gitlab-telegram-bot --tail=20
curl http://192.168.1.74:30088/health
```

### Warehouse Robot (WH-120)

```bash
cd ~/warehouse-master/warehouse-robot

# Деплой
docker build --no-cache -t warehouse-robot:latest .
sudo k3s ctr images rm docker.io/library/warehouse-robot:latest 2>/dev/null || true
docker save warehouse-robot:latest | sudo k3s ctr images import -

# ВАЖНО: Использовать Kustomize!
kubectl apply -k ~/warehouse-master/k8s/robot/

# Проверка
kubectl get pods -n warehouse -l app=warehouse-robot
curl http://192.168.1.74:30070/health
```

### Analytics Service (WH-121)

```bash
cd ~/warehouse-master/analytics-service

# Деплой
docker build --no-cache -t analytics-service:latest .
sudo k3s ctr images rm docker.io/library/analytics-service:latest 2>/dev/null || true
docker save analytics-service:latest | sudo k3s ctr images import -

# ВАЖНО: Использовать Kustomize!
kubectl apply -k ~/warehouse-master/k8s/analytics/

# Проверка
kubectl get pods -n warehouse -l app=analytics-service
curl http://192.168.1.74:30091/health
```

### Warehouse API

```bash
cd ~/warehouse-api

# Сборка
./mvnw package -DskipTests
docker build --no-cache -t warehouse-api:latest .

# Деплой в K3s
sudo k3s ctr images rm docker.io/library/warehouse-api:latest 2>/dev/null || true
docker save warehouse-api:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-api -n warehouse

# Проверка
kubectl get pods -n warehouse -l app=warehouse-api
curl http://192.168.1.74:30080/actuator/health
```

### Warehouse Frontend

```bash
cd ~/warehouse-frontend

# Сборка
npm install && npm run build
docker build --no-cache -t warehouse-frontend:latest .

# Деплой в K3s
sudo k3s ctr images rm docker.io/library/warehouse-frontend:latest 2>/dev/null || true
docker save warehouse-frontend:latest | sudo k3s ctr images import -
kubectl rollout restart deployment/warehouse-frontend -n warehouse

# Проверка
curl -s http://192.168.1.74:30081/ -o /dev/null -w "%{http_code}"
```

---

## Production деплой

### SSH на прод

```bash
ssh -i ~/.ssh/yc_prod_key ubuntu@130.193.44.34
```

### Обновление сервисов

```bash
cd /opt/warehouse

# Pull новых образов
sudo docker compose pull

# Перезапуск
sudo docker compose up -d

# Очистка старых образов
sudo docker image prune -f

# Проверка
sudo docker compose ps
curl -s https://api.wh-lab.ru/actuator/health
curl -s https://wh-lab.ru -o /dev/null -w "%{http_code}"
```

---

## Деплой через GitLab CI

### Staging (manual triggers)

| Job | Описание |
|-----|----------|
| `deploy-api-staging` | API в K3s |
| `deploy-frontend-staging` | Frontend в K3s |
| `deploy-all-staging` | API + Frontend |
| `deploy-telegram-bot` | Telegram Bot |
| `deploy-robot` | Warehouse Robot |
| `deploy-analytics` | Analytics Service |

### Production (manual triggers)

| Job | Описание |
|-----|----------|
| `deploy-api-prod` | API на Yandex Cloud |
| `deploy-frontend-prod` | Frontend на Yandex Cloud |
| `deploy-all-prod` | API + Frontend |

---

## Полезные команды

### Проверка статуса

```bash
# Все поды
kubectl get pods -A | grep -v Running

# Логи с ошибками
kubectl logs -n warehouse deployment/warehouse-api --tail=100 | grep -i error

# События
kubectl get events -n warehouse --sort-by='.lastTimestamp' | tail -20
```

### Откат

```bash
# История деплоев
kubectl rollout history deployment/warehouse-api -n warehouse

# Откат на предыдущую версию
kubectl rollout undo deployment/warehouse-api -n warehouse

# Откат на конкретную ревизию
kubectl rollout undo deployment/warehouse-api -n warehouse --to-revision=2
```

### Масштабирование

```bash
# Увеличить реплики
kubectl scale deployment/warehouse-api -n warehouse --replicas=3

# Изменить ресурсы
kubectl set resources deployment/warehouse-api -n warehouse --limits=cpu=1500m,memory=1Gi
```

---

## Чеклист перед деплоем

- [ ] Код закоммичен и запушен
- [ ] Тесты прошли (unit, e2e)
- [ ] Версия/тег образа корректный
- [ ] Secrets актуальны
- [ ] Health check работает локально

## Чеклист после деплоя

- [ ] Pod в статусе Running (не CrashLoopBackOff)
- [ ] Health endpoint отвечает 200
- [ ] Логи без ошибок
- [ ] Функционал работает (smoke test)

---

*Последнее обновление: 2025-12-01*
