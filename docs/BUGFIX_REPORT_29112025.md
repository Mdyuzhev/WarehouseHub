# Отчёт об исправлениях багов - 29.11.2025

## Исправленные баги

### WH-99: Frontend - верстка, кнопки, база
**Статус:** Исправлено

**Проблема:** После логина страница требовала обновления для отображения навигации и данных.

**Причина:** Race condition - компонент HomePage запрашивал products до сохранения токена в localStorage.

**Решение:**
- Добавлена задержка 50ms в LoginPage перед редиректом
- Добавлен метод `isReady()` для проверки готовности токена
- Добавлен флаг `authChecked` для триггера реактивности Vue

**Файлы:**
- `warehouse-frontend/src/components/LoginPage.vue`
- `warehouse-frontend/src/components/HomePage.vue`
- `warehouse-frontend/src/App.vue`

---

### WH-100: Grafana - пустые панели
**Статус:** Исправлено

**Проблема:** Панели "API Response Time" и "Service Health" не отображали данные.

**Причина:**
1. `histogram_quantile` требует метрики `_bucket`, которых нет (только `_count` и `_sum`)
2. Запрос `up{application="warehouse-api"}` использовал неверный label

**Решение:**
- Заменили percentile на average latency: `sum(rate(_sum))/sum(rate(_count))`
- Исправили label на `job="warehouse-api-service"`

**Файлы:**
- `k8s/monitoring/grafana-dashboards.yaml`

---

### WH-101: Prometheus 30090 не работает
**Статус:** Исправлено

**Проблема:** Prometheus недоступен по порту 30090.

**Причина:** Отсутствовал NodePort сервис для внешнего доступа.

**Решение:** Создан `prometheus-nodeport.yaml` с NodePort 30090.

**Файлы:**
- `k8s/monitoring/prometheus-nodeport.yaml` (новый файл)

---

### WH-84: Grafana datasource UID mismatch
**Статус:** Исправлено

**Проблема:** Grafana не отображала данные из Prometheus.

**Причина:** Dashboard использовал `uid: "prometheus"`, а реальный UID был `PBFA97CFB590B2093`.

**Решение:** Обновлён UID во всех панелях dashboard.

---

### WH-85: Frontend wrong port
**Статус:** Исправлено

**Проблема:** Frontend недоступен по порту 30000.

**Причина:** Frontend фактически работает на порту 30081.

**Решение:** Документация обновлена с корректным портом.

---

### WH-86: Swagger 403 Forbidden
**Статус:** Исправлено

**Проблема:** Swagger UI возвращал 403.

**Причина:** `/swagger-ui.html` не был в списке permitAll.

**Решение:** Добавлен в SecurityConfig.

---

### WH-87: Grafana datasource URL
**Статус:** Исправлено

**Проблема:** Grafana не могла подключиться к Prometheus.

**Причина:** URL `http://prometheus:9090` не резолвился в k8s.

**Решение:** Исправлен на `http://prometheus-kube-prometheus-prometheus:9090`.

---

### КРИТИЧЕСКИЙ: Хардкод API URL в production build
**Статус:** Исправлено

**Проблема:** Все API запросы шли на `api.wh-lab.ru` вместо локального API.

**Причина:** В `.env.production` был установлен `VITE_API_URL=https://api.wh-lab.ru/api`, который Vite инжектил в бандл при сборке.

**Решение:** Закомментирован `VITE_API_URL` в `.env.production`. Теперь API URL определяется динамически через `window.__API_URL__` в index.html.

**Файлы:**
- `warehouse-frontend/.env.production`

---

## Best Practices для предотвращения подобных ошибок

### 1. Frontend Build Configuration

```javascript
// НЕ устанавливать VITE_API_URL в .env.production!
// API URL должен определяться динамически в runtime
// .env.production
# VITE_API_URL=https://api.example.com/api  // ЗАКОММЕНТИРОВАНО!
```

**Почему:** Vite подставляет значения из `.env.production` при `npm run build`, хардкодя их в бандл. Это делает невозможным использование одного билда для разных окружений.

**Решение:** Использовать runtime конфигурацию через `window.__API_URL__` в index.html:
```html
<script>
  (function() {
    var host = window.location.hostname;
    if (host === 'production.example.com') {
      window.__API_URL__ = 'https://api.example.com/api';
    } else {
      window.__API_URL__ = 'http://' + host + ':30080/api';
    }
  })();
</script>
```

### 2. Vue Reactivity и Auth State

```javascript
// Проблема: computed property не обновляется после login
computed: {
  isAuthenticated() {
    return auth.isAuthenticated()  // Не реактивно!
  }
}

// Решение: использовать флаг для триггера реактивности
data() {
  return { authChecked: false }
},
computed: {
  isAuthenticated() {
    return this.authChecked && auth.isAuthenticated()
  }
},
methods: {
  updateUser() {
    this.authChecked = false
    this.$nextTick(() => { this.authChecked = true })
  }
}
```

### 3. Race Condition при редиректе после Login

```javascript
// Проблема: редирект до сохранения токена
if (result.success) {
  this.$router.push('/')  // Токен ещё не в localStorage!
}

// Решение: добавить микрозадержку
if (result.success) {
  await new Promise(r => setTimeout(r, 50))
  this.$router.push('/')
}
```

### 4. Kubernetes Services

- **ClusterIP** - доступен только внутри кластера
- **NodePort** - доступен извне по `<NodeIP>:<NodePort>`

Всегда создавайте NodePort сервисы для внешнего доступа к Prometheus, Grafana, Selenoid.

### 5. Grafana Prometheus Queries

```yaml
# Неправильно: histogram_quantile без bucket метрик
histogram_quantile(0.95, sum(rate(..._bucket[5m])))

# Правильно: проверить доступные метрики
# Если есть только _count и _sum, использовать avg:
sum(rate(..._sum[5m])) / sum(rate(..._count[5m]))
```

### 6. Spring Security permitAll

```java
// Не забывать добавлять статические ресурсы
.requestMatchers("/favicon.ico", "/favicon.svg", "/*.png").permitAll()
.requestMatchers("/swagger-ui/**", "/swagger-ui.html", "/v3/api-docs/**").permitAll()
```

### 7. Grafana Datasource Configuration

Всегда проверять:
1. UID datasource совпадает в dashboard и provisioning
2. URL Prometheus корректный (полное DNS имя в k8s)
3. Datasource доступен: `kubectl exec -n monitoring deploy/grafana -- curl http://prometheus:9090/api/v1/query?query=up`

---

## Чек-лист перед деплоем

- [ ] `.env.production` НЕ содержит хардкод URLs
- [ ] `index.html` содержит runtime конфигурацию API URL
- [ ] SecurityConfig включает все публичные endpoints
- [ ] Grafana datasource UID совпадает
- [ ] NodePort сервисы созданы для внешнего доступа
- [ ] Prometheus метрики доступны (проверить через curl)
- [ ] Vue auth state использует реактивные флаги

---

## Ссылки на сервисы

| Сервис | URL | Порт |
|--------|-----|------|
| Frontend | http://192.168.1.74:30081 | 30081 |
| API | http://192.168.1.74:30080 | 30080 |
| Swagger | http://192.168.1.74:30080/swagger-ui/index.html | 30080 |
| Grafana | http://192.168.1.74:30300 | 30300 |
| Prometheus | http://192.168.1.74:30090 | 30090 |
| Selenoid | http://192.168.1.74:30040 | 30040 |
