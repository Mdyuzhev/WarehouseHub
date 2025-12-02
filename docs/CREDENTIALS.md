# Credentials & Secrets

> Все учётные данные проекта Warehouse. **НЕ КОММИТИТЬ В ПУБЛИЧНЫЕ РЕПОЗИТОРИИ!**

---

## Серверы

### Staging (192.168.1.74)

| Параметр | Значение |
|----------|----------|
| IP | 192.168.1.74 |
| VPN IP | 100.81.243.12 (Tailscale) |
| User | flomaster |
| SSH | `ssh flomaster@192.168.1.74` |

### Production (130.193.44.34)

| Параметр | Значение |
|----------|----------|
| IP | 130.193.44.34 |
| User | ubuntu |
| SSH | `ssh -i ~/.ssh/yc_prod_key ubuntu@130.193.44.34` |
| Path | /opt/warehouse |

---

## Базы данных

### PostgreSQL (K8s)

| Параметр | Значение |
|----------|----------|
| Host (K8s) | `postgres-service.warehouse.svc.cluster.local` |
| Host (external) | `192.168.1.74:30432` |
| Database | `warehouse` |
| Admin User | `postgres` |
| Admin Password | `postgres_admin_2025` |
| App User | `warehouse_user` |
| App Password | `warehouse_secret_2025` |

```bash
# Подключение
kubectl exec -n warehouse postgres-0 -- psql -U postgres -d warehouse
```

### Redis

| Параметр | Значение |
|----------|----------|
| Host | `redis.warehouse.svc.cluster.local` |
| Port | 6379 |
| DB 0 | General cache |
| DB 1 | Analytics Service |

```bash
kubectl exec -n warehouse deployment/redis -- redis-cli PING
```

### Kafka

| Параметр | Значение |
|----------|----------|
| Host | `kafka.warehouse.svc.cluster.local` |
| Port | 9092 |
| Topics | `warehouse.audit`, `warehouse.notifications` |

---

## Внешние сервисы

### GitLab

| Параметр | Значение |
|----------|----------|
| URL | http://192.168.1.74:8080 |
| User | root |
| Password | Misha2021@1@ |
| Token | `glpat-2vUJYwQIOuT-PxvU-tcg-W86MQp1OjEH.01.0w0ykqxat` |

### YouTrack

| Параметр | Значение |
|----------|----------|
| URL | http://192.168.1.74:8088 |
| User | admin |
| Password | Misha2021@1@ |
| Auth | **ТОЛЬКО Basic Auth!** |
| Project ID | 0-1 |
| Project Short | WH |

```bash
# Пример запроса
curl -s -u 'admin:Misha2021@1@' 'http://192.168.1.74:8088/api/issues/WH-120'
```

### Grafana

| Параметр | Значение |
|----------|----------|
| URL | http://192.168.1.74:30300 |
| User | admin |
| Password | admin123 |

### Telegram Bot

| Параметр | Значение |
|----------|----------|
| Bot Token | `8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI` |
| Chat ID | `290274837` |
| Webhook Secret | `warehouse-webhook-secret-2024` |

### Пароли для Telegram бота

| Функция | Пароль |
|---------|--------|
| Deploy | Misha2021@1@ |
| Load Test | Misha2021@1@ |
| Robot | (в K8s secrets) |
| Guest | Guest |

---

## JWT & Secrets

### JWT Secret (Staging)

```
BcxfC7EDiXdnfjCdjdIRrntE7heN1RcvA/3pnHCT1kw=
```

### Yandex Container Registry

```bash
# Registry
cr.yandex/crpf5fukf1ili7kudopb

# Auth
cat /home/flomaster/secrets/yc-registry-key.json | docker login --username json_key --password-stdin cr.yandex
```

---

## Тестовые пользователи (Warehouse API)

> Пароль для всех: `password123`

| Username | Role | Права |
|----------|------|-------|
| superuser | SUPER_USER | Все |
| admin | ADMIN | Управление пользователями |
| manager | MANAGER | Просмотр товаров |
| employee | EMPLOYEE | CRUD товаров |
| analyst | ANALYST | Только аналитика |

---

## SSH ключи

```
/home/flomaster/.ssh/
├── yc_prod_key       # Приватный ключ для прода
├── yc_deploy_key     # Альтернативный ключ
└── id_ed25519        # Общий SSH ключ
```

---

*Последнее обновление: 2025-12-01*
