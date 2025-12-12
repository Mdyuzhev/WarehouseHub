# Warehouse Frontend

Frontend SPA для системы управления складом.

## Технологии

- Vue.js 3.4
- Vite 5
- Vue Router 4

## Запуск

```bash
npm install
npm run dev
```

## Сборка

```bash
npm run build
```

## Git Workflow

Проект использует упрощенный Git Flow с двумя основными ветками.

### Ветки

**main** - production-ready код. Эта ветка защищена от прямых пушей. Все изменения попадают сюда только через merge request после code review. Каждый коммит в main автоматически деплоится в production.

**develop** - основная ветка разработки. Сюда мержатся все feature-ветки. Каждый коммит в develop автоматически деплоится в dev-окружение.

### Процесс разработки

1. Создать feature-ветку от develop:
```bash
git checkout develop
git pull origin develop
git checkout -b feature/WH-XXX-краткое-описание
```

2. Разработать функциональность, регулярно коммитя изменения. В сообщениях коммитов указывать номер задачи:
```bash
git commit -m "feat(WH-XXX): добавлен компонент FacilityCard"
```

3. Запушить ветку и создать merge request в develop:
```bash
git push -u origin feature/WH-XXX-краткое-описание
```

4. После code review и успешного прохождения CI - смержить в develop.

5. Для релиза в production создать merge request из develop в main.

### Hotfix

Для срочных исправлений production:

1. Создать hotfix-ветку от main:
```bash
git checkout main
git checkout -b hotfix/WH-XXX-описание-бага
```

2. Исправить баг, создать MR в main.

3. После мержа в main - создать MR того же hotfix в develop, чтобы исправление не потерялось.

### Именование веток

- `feature/WH-XXX-описание` - новая функциональность
- `bugfix/WH-XXX-описание` - исправление бага в develop
- `hotfix/WH-XXX-описание` - срочное исправление production
- `refactor/WH-XXX-описание` - рефакторинг без изменения функционала

### Именование коммитов

Используем Conventional Commits:

- `feat(WH-XXX): описание` - новая функциональность
- `fix(WH-XXX): описание` - исправление бага
- `refactor(WH-XXX): описание` - рефакторинг
- `docs(WH-XXX): описание` - документация
- `test(WH-XXX): описание` - тесты
- `chore(WH-XXX): описание` - инфраструктура, зависимости
