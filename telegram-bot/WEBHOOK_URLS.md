# GitLab Webhook URLs - Шпаргалка

В зависимости от того, где запущен бот, используй разные URL для webhook.

## Сценарий 1: Бот в K8s (рекомендуется)

**Где:** Бот запущен в namespace `notifications` в том же K8s кластере что и GitLab

**Webhook URL:**
```
http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab
```

**Как проверить:**
```bash
kubectl get pods -n notifications | grep telegram-bot
kubectl get svc -n notifications warehouse-telegram-bot
```

**Преимущества:**
- Быстро (внутри кластера)
- Не нужно открывать наружу
- Безопасно

---

## Сценарий 2: Бот на хосте (локально)

**Где:** Бот запущен на том же хосте что и GitLab (192.168.1.74)

**Webhook URL:**
```
http://192.168.1.74:8000/webhook/gitlab
```

**Как запустить:**
```bash
cd /home/flomaster/warehouse-master/telegram-bot
export TELEGRAM_BOT_TOKEN="8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI"
export TELEGRAM_CHAT_ID="290274837"
export GITLAB_URL="http://192.168.1.74:8080"
export GITLAB_TOKEN="glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3"
uvicorn app:app --host 0.0.0.0 --port 8000
```

**Преимущества:**
- Легко дебажить
- Видно логи сразу

**Недостатки:**
- Нужно держать процесс запущенным

---

## Сценарий 3: Бот через NodePort

**Где:** Бот в K8s, но доступен через NodePort снаружи

**Webhook URL:**
```
http://192.168.1.74:30XXX/webhook/gitlab
```

Где `30XXX` - NodePort service.

**Как узнать порт:**
```bash
kubectl get svc -n notifications warehouse-telegram-bot
```

**Пример вывода:**
```
NAME                      TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
warehouse-telegram-bot    NodePort   10.43.123.45    <none>        8000:30800/TCP   1d
```

В этом случае URL будет: `http://192.168.1.74:30800/webhook/gitlab`

---

## Сценарий 4: Бот в другом кластере/сети

**Где:** Бот запущен отдельно от GitLab (другой кластер, другой хост)

**Webhook URL:**
```
http://<public-ip-or-domain>:<port>/webhook/gitlab
```

**Требования:**
- Бот должен быть доступен из сети где находится GitLab
- Если используется HTTPS - настрой SSL/TLS

**Примеры:**
```
http://bot.example.com/webhook/gitlab
https://bot.example.com/webhook/gitlab
http://10.0.0.50:8000/webhook/gitlab
```

---

## Как выбрать?

### Для production:
✅ **Сценарий 1** (K8s internal DNS) - самый надёжный и безопасный

### Для разработки/тестирования:
✅ **Сценарий 2** (локально на хосте) - удобно дебажить

### Если GitLab вне K8s:
✅ **Сценарий 3** (NodePort) или **Сценарий 4** (public URL)

---

## Текущая конфигурация проекта

Для warehouse проекта рекомендуется:

**Production webhook URL:**
```
http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/webhook/gitlab
```

**Локальное тестирование:**
```
http://localhost:8000/webhook/gitlab
```
(запусти бот локально через `uvicorn app:app`)

---

## Проверка доступности

### Из GitLab Runner (внутри K8s):
```bash
kubectl run -it --rm test --image=curlimages/curl --restart=Never -- \
  curl http://warehouse-telegram-bot.notifications.svc.cluster.local:8000/health
```

Должно вернуть:
```json
{"status":"healthy","version":"5.0.0","timestamp":"..."}
```

### С хоста (192.168.1.74):
```bash
curl http://localhost:8000/health
# или
curl http://192.168.1.74:8000/health
```

---

## Troubleshooting

### Connection refused
→ Бот не запущен или URL неправильный
→ Проверь: `kubectl get pods -n notifications`

### Name resolution failed
→ DNS не резолвится (скорее всего GitLab не внутри K8s)
→ Используй NodePort или IP адрес

### SSL certificate problem
→ Если используешь HTTPS с self-signed сертификатом
→ Отключи "Enable SSL verification" в настройках webhook

---

**Рекомендация:** Используй Сценарий 1 для production!
