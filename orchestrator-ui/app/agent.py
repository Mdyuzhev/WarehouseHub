"""
🤖 Интеграция с Claude Agent
Общаемся с ИИ прямо из 8-битной консоли!
"""

import httpx
from typing import Optional
import json
import traceback

from .config import CLAUDE_PROXY_URL, ANTHROPIC_API_KEY
from .database import (
    get_or_create_session,
    add_message,
    get_session_messages
)

# Системный промпт для агента
SYSTEM_PROMPT = """Ты - помощник для управления Warehouse системой. Отвечай коротко и по делу.

Контекст:
- Warehouse API: Spring Boot на K8s
- Frontend: Vue.js SPA
- База: PostgreSQL
- Кластер: K3s на 192.168.1.74

Отвечай с юмором, но будь полезным!
"""


class AgentService:
    def __init__(self):
        self.proxy_url = CLAUDE_PROXY_URL

    async def chat(self, user_message: str, context: Optional[str] = None) -> str:
        """
        Отправить сообщение агенту и получить ответ
        """
        try:
            # Получаем или создаём сессию
            session_id = await get_or_create_session()

            # Сохраняем сообщение пользователя
            await add_message(session_id, "user", user_message)

            # Получаем историю для контекста (последние 10 сообщений)
            history = await get_session_messages(session_id, limit=10)

            # Формируем сообщения для API
            messages = []
            for msg in history:
                role = "user" if msg["role"] == "user" else "assistant"
                messages.append({"role": role, "content": msg["content"]})

            # Вызываем Claude через прокси напрямую
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.proxy_url}/v1/messages",
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1024,
                        "system": SYSTEM_PROMPT,
                        "messages": messages
                    },
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    return f"🔥 Прокси вернул ошибку {response.status_code}: {response.text[:200]}"

                data = response.json()

                # Извлекаем ответ
                if "content" in data and len(data["content"]) > 0:
                    assistant_message = data["content"][0].get("text", "")
                else:
                    assistant_message = str(data)

            # Сохраняем ответ
            await add_message(session_id, "agent", assistant_message)

            return assistant_message

        except httpx.TimeoutException:
            return "⏰ Таймаут! Агент думает слишком долго, попробуй ещё раз."
        except Exception as e:
            error_msg = f"🔥 Ошибка: {str(e)}"
            print(f"Agent error: {traceback.format_exc()}")
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
