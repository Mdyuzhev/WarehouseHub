# Контекст проекта Warehouse

## ПЕРВЫМ ДЕЛОМ
**При старте работ ОБЯЗАТЕЛЬНО прочитай эту инструкцию полностью!**
Путь: `/home/flomaster/warehouse-master/.claude/project-context.md`

---

## Общая информация
- **Проект:** Warehouse - система управления складом
- **Владелец:** flomaster (Миша)
- **Стиль общения:** С юмором, без лишних церемоний
- **Мастер-репозиторий:** warehouse-master (оркестрация всего)

---

## КРИТИЧНО: Управление ресурсами сервера

**Сервер имеет 24GB RAM - ресурсы ограничены!**

### Режимы работы

| Режим | RAM | Команда | Когда использовать |
|-------|-----|---------|-------------------|
| **IDLE** | ~4-5GB | `lab stop-session` | Сервер включен, никто не работает |
| **CI/CD** | ~7-9GB | `lab start-ci` | Только пайплайны GitLab |
| **FULL** | ~14-16GB | `lab start-session` | Полная рабочая сессия |

### ОБЯЗАТЕЛЬНЫЕ действия

```bash
# ПЕРЕД началом работы с Warehouse
lab start-warehouse

# ПОСЛЕ завершения работы
lab stop-warehouse

# Если нужен GitLab/YouTrack
lab start-session

# В конце рабочего дня
lab stop-session
```

**Полная инструкция:** `.claude/instructions/lab-control.md`

## Стиль общения Claude

**ВАЖНО:** Всегда отвечать Мише с юмором!

- Все статусы, отчёты и комментарии писать с шутками
- Использовать эмодзи по настроению
- Добавлять dev-юмор и мемные отсылки
- Не быть занудой - мы тут не на собеседовании
- Сарказм приветствуется (в меру)
- Если что-то сломалось - не паниковать, а шутить про дедлайны

---

## КРИТИЧЕСКИ ВАЖНО: Vite/Rollup и API URL

### Проблема (решена 2025-11-29)
Vite/Rollup при сборке АГРЕССИВНО оптимизирует код и заменяет runtime-логику на статические строки!

**Симптомы:**
- Frontend на staging/prod обращается к неправильному API URL
- В бандле вместо `window.location.hostname` захардкожен URL
- CORS ошибки, 502, 401 при логине

**Решение (3 компонента):**

1. **index.html** - runtime скрипт ДО загрузки бандла:
```html
<script>
  (function() {
    var host = window.location.hostname;
    if (host === 'wh-lab.ru' || host === 'www.wh-lab.ru') {
      window.__API_URL__ = 'https://api.wh-lab.ru/api';
    } else if (host === '192.168.1.74') {
      window.__API_URL__ = 'http://192.168.1.74:30080/api';
    } else {
      window.__API_URL__ = 'http://' + host + ':30080/api';
    }
  })();
</script>
```

2. **auth.js** - использовать `new Function()` для обхода оптимизации:
```javascript
function getApi() {
  const getUrl = new Function('return window.__API_URL__');
  return getUrl() || 'http://192.168.1.74:30080/api';
}
```

3. **vite.config.js** - отключить оптимизацию:
```javascript
build: {
  minify: false,
  rollupOptions: { treeshake: false }
}
```

**Проверка что работает:**
```bash
curl -s https://wh-lab.ru/ | grep "__API_URL__"
curl -s https://wh-lab.ru/assets/index-*.js | grep "new Function"
```

---

## Архитектура репозиториев

```
warehouse-master/     # Оркестрация, деплой, тесты, бот
warehouse-api/        # Spring Boot REST API
warehouse-frontend/   # Vue.js SPA
```

## Инфраструктура

### Staging (K3s кластер на 192.168.1.74)
| Сервис | URL | Namespace |
|--------|-----|-----------|
| API | http://192.168.1.74:30080 | warehouse |
| Frontend | http://192.168.1.74:30081 | warehouse |
| PostgreSQL | StatefulSet | warehouse |
| Locust | http://192.168.1.74:30089 | loadtest |
| Telegram Bot | - | notifications |

### Production (Yandex Cloud - 130.193.44.34)
| Сервис | URL |
|--------|-----|
| API | https://api.wh-lab.ru |
| Frontend | https://wh-lab.ru |
| Registry | cr.yandex/crpf5fukf1ili7kudopb |

**Деплой на прод:**
```bash
# SSH ключ с правильными правами
cp ~/.ssh/yc_prod_key /tmp/deploy_key && chmod 600 /tmp/deploy_key

# Деплой
ssh -i /tmp/deploy_key ubuntu@130.193.44.34 << 'ENDSSH'
cd /opt/warehouse
sudo docker compose pull frontend  # или api
sudo docker compose up -d frontend
ENDSSH
```

### Сервисы на хосте (192.168.1.74)
| Сервис | URL |
|--------|-----|
| GitLab | http://192.168.1.74:8080 |
| Allure Server | http://192.168.1.74:5050 |
| Allure UI | http://192.168.1.74:5252 |
| Claude Proxy | http://192.168.1.74:8765 |

**YouTrack отключён** - задачи ведутся в GitHub Project

---

## GitHub (Task Tracking)

- **Repo:** https://github.com/Mdyuzhev/WaregouseHub
- **Project:** https://github.com/users/Mdyuzhev/projects/3
- **Issues:** 200 задач мигрированы из YouTrack

### Работа с задачами:
```bash
# Список открытых задач
gh issue list --repo Mdyuzhev/WaregouseHub

# Создать задачу
gh issue create --repo Mdyuzhev/WaregouseHub --title "Название" --body "Описание"

# Закрыть задачу
gh issue close 123 --repo Mdyuzhev/WaregouseHub

# Посмотреть задачу
gh issue view 123 --repo Mdyuzhev/WaregouseHub
```

### API (через curl):
```bash
# Список issues
curl -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/Mdyuzhev/WaregouseHub/issues"

# Создать issue
curl -X POST -H "Authorization: token $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  "https://api.github.com/repos/Mdyuzhev/WaregouseHub/issues" \
  -d '{"title":"Название","body":"Описание"}'
```

---

## Тестовые пользователи

### Staging (192.168.1.74:30081)
| Логин | Пароль | Роль |
|-------|--------|------|
| ivanov | password123 | SUPER_USER |
| petrova | password123 | ADMIN |
| sidorov | password123 | MANAGER |
| kozlova | password123 | EMPLOYEE |

### Production (wh-lab.ru)
| Логин | Пароль | Роль |
|-------|--------|------|
| superuser | password123 | SUPER_USER |
| admin | password123 | ADMIN |
| manager | password123 | MANAGER |
| employee | password123 | EMPLOYEE |
| ivanov | password123 | SUPER_USER |
| petrova | password123 | ADMIN |
| sidorov | password123 | MANAGER |
| kozlova | password123 | EMPLOYEE |

---

## Production docker-compose

Файл: `/opt/warehouse/docker-compose.yml`

**Важные переменные:**
- `DB_PASSWORD` - из `.env` файла
- `JWT_SECRET` - должен быть валидный base64 (без `_`)

Если API падает с ошибкой JWT:
```bash
# Генерируем новый ключ
JWT_KEY=$(openssl rand -base64 48 | tr -d '\n' | head -c 64)
sudo sed -i "s|JWT_SECRET=.*|JWT_SECRET=${JWT_KEY}|" docker-compose.yml
sudo docker compose up -d api
```

---

## Частые проблемы и решения

### 1. Frontend показывает CORS / 502 / старый API URL
**Причина:** Vite закешировал или оптимизировал API URL
**Решение:** Пересобрать с `--no-cache`, проверить что в бандле есть `new Function`

### 2. API на проде в Restarting
**Проверить логи:** `sudo docker logs warehouse-api --tail 50`
**Частые причины:**
- `JWT_SECRET` содержит недопустимые символы (`_`)
- Неверный пароль БД (проверить `.env`)
- БД ещё не готова (подождать)

### 3. Медленная загрузка товаров
**Причина:** Много тестовых данных в БД (от нагрузочных тестов)
**Решение:**
```bash
sudo docker exec warehouse-db psql -U warehouse -d warehouse -c "DELETE FROM products WHERE name LIKE 'LoadProduct_%';"
```

### 4. Docker кеширует старый образ
**Решение:** Собирать с `--no-cache`:
```bash
docker build --no-cache -t warehouse-frontend:latest .
```

---

## GitLab CI/CD

### warehouse-master (оркестрация)
Ручные триггеры в GitLab:
- Deploy API Staging / Production
- Deploy Frontend Staging / Production
- Deploy All Staging / Production
- Run E2E Tests
- Run Load Tests
- Deploy Telegram Bot

---

## Рабочие директории
```
/home/flomaster/warehouse-master    # Оркестрация
/home/flomaster/warehouse-api       # API
/home/flomaster/warehouse-frontend  # Frontend
```

## Секреты
- GitHub Token: в переменной GITHUB_TOKEN (ghp_...)
- GitLab Token: glpat-Ou0qfvnfGfUOGkbs3nmv8m86MQp1OjEH.01.0w0ojabq3
- Telegram Bot Token: 8532494921:AAEoxQ87qQVcutgCSa8d8DntT_47xhvrCAI
- Telegram Chat ID: 290274837
- Yandex Cloud SSH: ~/.ssh/yc_prod_key

---

## Changelog

### 2025-11-29
- **WH-42 FIXED:** Исправлена проблема с API URL на staging/prod
  - Vite агрессивно оптимизировал код, заменяя runtime логику на статику
  - Решение: runtime скрипт в index.html + new Function() + отключение minify/treeshake
- **Production:** Полностью настроен и работает
  - Добавлены пользователи ivanov, petrova, sidorov, kozlova
  - Очищена БД от 175795 тестовых товаров
  - Исправлен JWT_SECRET (валидный base64)
- **Frontend:** Добавлено автообновление списка товаров при навигации
