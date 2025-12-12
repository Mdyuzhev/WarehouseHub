Быстрый старт работы:

1. Определи репо: `pwd && basename $(git rev-parse --show-toplevel 2>/dev/null || echo "not-git")`
2. Проверь ветку: `git branch --show-current`
3. Health check: `curl -s http://192.168.1.74:30080/actuator/health 2>/dev/null | jq -r .status || echo "DOWN"`

Ответь:
```
📁 Репо: [название]
🌿 Ветка: [название]
💚 API: [UP/DOWN]
✅ Готов!
```
