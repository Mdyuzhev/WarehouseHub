Изучи контекст проекта Warehouse:

1. Прочитай `.claude/instructions/00-main.md`
2. Прочитай `.claude/CLAUDE.md`
3. Прочитай `.claude/project-context.md`
4. Проверь текущий репозиторий: `pwd && basename $(git rev-parse --show-toplevel)`
5. Проверь ветку: `git branch --show-current`
6. Проверь статус API: `curl -s http://192.168.1.74:30080/actuator/health 2>/dev/null | jq -r .status || echo "DOWN"`

Ответь кратко:
```
Репозиторий: [название]
Ветка: [название]
API Prod: [UP/DOWN]
Готов к работе!
```
