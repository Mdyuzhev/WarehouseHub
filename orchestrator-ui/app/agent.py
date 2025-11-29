"""
🤖 Интеграция с Claude Agent
Общаемся с ИИ прямо из 8-битной консоли!
"""

import httpx
from anthropic import AsyncAnthropic
from typing import Optional
import json

from .config import CLAUDE_PROXY_URL, ANTHROPIC_API_KEY
from .database import (
    get_or_create_session,
    add_message,
    get_session_messages
)

# Системный промпт для агента
SYSTEM_PROMPT = """Ты - помощник для управления Warehouse системой. Твои возможности:

1. **Анализ логов** - можешь разобраться что пошло не так
2. **Советы по деплою** - подсказать как лучше развернуть
3. **Диагностика проблем** - помочь найти причину ошибок
4. **Ответы на вопросы** - по архитектуре, K8s, Docker и т.д.

Контекст системы:
- Warehouse API: Spring Boot приложение на K8s
- Frontend: Vue.js SPA
- База данных: PostgreSQL
- Кеш: Redis
- Кластер: K3s на 192.168.1.74

ВАЖНО: Отвечай с юмором! Ты в 8-битной консоли, так что можно добавить:
- Отсылки к ретро-играм
- ASCII-арт (но небольшой)
- Эмодзи по настроению
- Сарказм (в меру)

Но при этом будь полезным и давай конкретные советы!
"""


class AgentService:
    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        """Инициализация клиента Anthropic"""
        if ANTHROPIC_API_KEY:
            self.client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        else:
            # Используем прокси
            self.client = AsyncAnthropic(
                api_key="dummy",  # Прокси не требует ключ
                base_url=CLAUDE_PROXY_URL
            )

    async def chat(self, user_message: str, context: Optional[str] = None) -> str:
        """
        Отправить сообщение агенту и получить ответ
        context - дополнительный контекст (логи, статус и т.д.)
        """
        try:
            # Получаем или создаём сессию
            session_id = await get_or_create_session()

            # Сохраняем сообщение пользователя
            await add_message(session_id, "user", user_message)

            # Получаем историю для контекста
            history = await get_session_messages(session_id, limit=20)

            # Формируем сообщения для API
            messages = []

            # Добавляем контекст если есть
            if context:
                messages.append({
                    "role": "user",
                    "content": f"[Контекст системы]\n{context}"
                })
                messages.append({
                    "role": "assistant",
                    "content": "Понял, учту этот контекст."
                })

            # Добавляем историю
            for msg in history:
                messages.append({
                    "role": msg["role"] if msg["role"] == "user" else "assistant",
                    "content": msg["content"]
                })

            # Вызываем Claude
            response = await self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages
            )

            # Извлекаем ответ
            assistant_message = response.content[0].text

            # Сохраняем ответ
            await add_message(session_id, "agent", assistant_message)

            return assistant_message

        except Exception as e:
            error_msg = f"🔥 Упс! Агент временно недоступен: {str(e)}"
            return error_msg

    async def analyze_logs(self, logs: str) -> str:
        """Попросить агента проанализировать логи"""
        prompt = f"""Проанализируй эти логи и скажи что происходит:

```
{logs[:3000]}  # Ограничиваем размер
```

Найди ошибки, предупреждения и дай рекомендации."""

        return await self.chat(prompt)

    async def diagnose_problem(self, problem_description: str, service_status: dict) -> str:
        """Диагностика проблемы с учётом статуса сервисов"""
        context = f"Текущий статус сервисов:\n{json.dumps(service_status, indent=2, ensure_ascii=False)}"

        prompt = f"""Помоги разобраться с проблемой:

{problem_description}

Что может быть не так и как это починить?"""

        return await self.chat(prompt, context=context)

    async def get_history(self, limit: int = 50) -> list:
        """Получить историю чата"""
        session_id = await get_or_create_session()
        return await get_session_messages(session_id, limit=limit)


# Глобальный экземпляр
agent_service = AgentService()
