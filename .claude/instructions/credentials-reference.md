# Credentials Reference - Домашний сервер 192.168.1.74

> **Версия:** 1.0
> **Обновлено:** 2025-12-11

---

## Структура хранения секретов

| Тип | Местоположение | Формат |
|-----|---------------|--------|
| Database credentials | K8s Secrets | base64 encoded |
| API keys | K8s Secrets + .env | plaintext в .env |
| JWT/Signing keys | docker-compose.yml | plaintext |
| Shell tokens | ~/.bashrc | export variables |
| SSH keys | ~/.ssh/authorized_keys | SSH public keys |

---

## Warehouse Project

### Production (namespace: warehouse)

**K8s Secrets:**
- `postgres-credentials` - доступ к PostgreSQL
- `postgres-replica-credentials` - реплика PostgreSQL
- `warehouse-api-secrets` - API секреты
- `warehouse-robot-secrets` - интеграции

**PostgreSQL:**
- Host: `postgres-service.warehouse.svc.cluster.local:5432`
- Database: `warehouse`
- App User: `warehouse_user`
- Password: см. K8s Secret `postgres-credentials`

**Redis:**
- Host: `redis:6379` (docker) / `warehouse.svc.cluster.local` (k8s)
- Password: не установлен
- Maxmemory: 256mb

### Development (namespace: warehouse-dev)

**K8s Secrets:**
- `postgres-credentials`
- `warehouse-api-secrets`

---

## Внешние сервисы

### YouTrack
- URL: http://192.168.1.74:8088
- Credentials: см. `.claude/project-context.md` секция "Секреты"
- API: Basic Auth

### GitLab
- URL: http://192.168.1.74:8080
- Token: см. `~/.gitlab-token` или `.claude/project-context.md`

### Telegram Bot (Warehouse)
- Token: см. `.claude/project-context.md` секция "Секреты"
- Chat ID: см. `.claude/project-context.md`

---

## Другие проекты на сервере

### ErrorLens (namespace: errorlens-stage)

**K8s Secrets:**
- `errorlens-db-credentials`
- `errorlens-api-secrets`

**Docker Compose:** `/home/flomaster/projects/errorlens/.env`

### Bots (namespace: bots)

**ErrorLens Bot:**
- .env: `/home/flomaster/projects/bots/el-bot/.env`
- K8s Secrets: `el-bot-telegram-credentials`, `el-bot-api-credentials`

### Monitoring (namespace: monitoring)

**K8s Secrets:**
- `grafana-admin-credentials`
- `prometheus-config`
- `loki-config`
- `alertmanager-config`

---

## Получение секретов из K8s

```bash
# Список секретов в namespace
kubectl get secrets -n warehouse

# Просмотр секрета (base64)
kubectl get secret postgres-credentials -n warehouse -o yaml

# Декодирование значения
kubectl get secret postgres-credentials -n warehouse -o jsonpath='{.data.password}' | base64 -d
```

---

## Переменные окружения (~/.bashrc)

```bash
export KUBECONFIG=~/.kube/config
export YOUTRACK_TOKEN=<хранится в переменной>
export HUB_TOKEN=<хранится в переменной>
```

---

## Важные файлы

| Файл | Содержимое |
|------|------------|
| `~/.gitlab-token` | GitLab Personal Access Token |
| `~/.bashrc` | YOUTRACK_TOKEN, HUB_TOKEN |
| `/home/flomaster/warehouse-master/production/.env` | Production DB password |
| `/home/flomaster/projects/errorlens/.env` | ErrorLens credentials |
| `/home/flomaster/projects/bots/el-bot/.env` | Telegram Bot Token |

---

## Рекомендации по безопасности

1. **JWT_SECRET** захардкожен в docker-compose.yml - вынести в .env
2. **Redis** без пароля в production - добавить requirepass
3. **.env файлы** должны быть в .gitignore
4. **Shell tokens** из .bashrc лучше перенести в K8s secrets
