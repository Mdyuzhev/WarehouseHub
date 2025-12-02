# Инструкция: Старт работы

## Правило
**Читай документы ПО СИТУАЦИИ, не все 10 подряд!**

## Команда запуска
```
Старт
```

## Шаги

### 1. Всегда читай (обязательно)
```
docs/PROJECT_STATUS.md
```
Это единственный обязательный документ.

### 2. Добавь по типу задачи

| Тип задачи | Документы |
|------------|-----------|
| Деплой | DEPLOY_GUIDE.md, CREDENTIALS.md |
| YouTrack | YOUTRACK_API.md |
| Тестирование | TESTING.md, LOAD_TESTING.md |
| Архитектура | ARCHITECTURE.md, COMPONENTS.md |
| Проблемы | TROUBLESHOOTING_GUIDE.md |

**Если задача неизвестна** — читай только PROJECT_STATUS.md и спроси.

### 3. Проверь health
```bash
curl -s http://192.168.1.74:30080/actuator/health | jq .status
```

### 4. Кратко подтверди
```
Контекст загружен. API: UP. Ветка: XXX. Готов!
```

## НЕ делать
- Читать все 10 документов
- Пересказывать документацию
- Выводить длинные таблицы

## Критичные правила
1. K3s != Docker — после build нужен k3s ctr import
2. Main protected — merge через MR
3. YouTrack — только Basic Auth
4. Docker build — НЕ локально (OOM), через CI/CD
5. Секреты в CREDENTIALS.md