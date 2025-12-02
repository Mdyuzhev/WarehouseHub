"""
Обработчики очистки данных.
Чистим Redis, Kafka, PostgreSQL до блеска! 🧹
WH-233, WH-241-244
"""

import logging
from bot.telegram import send_message_with_reply_keyboard, send_message_with_inline_keyboard, send_message, send_chat_action
from bot.keyboards import get_reply_keyboard, get_cleanup_env_keyboard, get_cleanup_confirm_keyboard
from bot.messages import format_cleanup_result
from services import cleanup_redis, cleanup_kafka, cleanup_postgres, cleanup_all
from config import LOAD_TEST_STAGING_PASSWORD, LOAD_TEST_PROD_PASSWORD

logger = logging.getLogger(__name__)

# =============================================================================
# State - ожидание пароля для cleanup
# =============================================================================
pending_cleanup_auth = {}  # chat_id -> {environment, component}


# =============================================================================
# Cleanup Menu
# =============================================================================

async def handle_cleanup_menu(chat_id: int):
    """Показывает меню выбора среды для очистки."""
    msg = """<b>🧹 Очистка данных</b>

Выбери среду для очистки тестовых данных:

<i>⚠️ Будут удалены только тестовые данные (с маркерами LoadTest, k6)</i>
    """
    await send_message_with_inline_keyboard(msg.strip(), get_cleanup_env_keyboard(), chat_id=chat_id)


async def handle_cleanup_env(chat_id: int, environment: str):
    """Показывает меню выбора компонента для очистки."""
    env_names = {"staging": "🧪 STAGING", "prod": "🚀 PRODUCTION"}
    env_name = env_names.get(environment, environment)

    warning = ""
    if environment == "prod":
        warning = "\n\n⚠️ <b>ВНИМАНИЕ!</b> Это боевая среда!"

    msg = f"""<b>🧹 Очистка: {env_name}</b>{warning}

Выбери что очистить:

🗑 <b>Redis</b> — кэш и сессии
📨 <b>Kafka</b> — consumer groups
🗄 <b>PostgreSQL</b> — тестовые данные
💥 <b>Всё сразу</b> — полная очистка
    """
    await send_message_with_inline_keyboard(msg.strip(), get_cleanup_confirm_keyboard(environment), chat_id=chat_id)


async def request_cleanup_password(chat_id: int, environment: str, component: str):
    """Запрашивает пароль для очистки."""
    global pending_cleanup_auth

    pending_cleanup_auth[chat_id] = {
        "environment": environment,
        "component": component,
    }

    env_names = {"staging": "🧪 STAGING", "prod": "🚀 PRODUCTION"}
    component_names = {
        "redis": "🗑 Redis",
        "kafka": "📨 Kafka",
        "postgres": "🗄 PostgreSQL",
        "all": "💥 Всё сразу"
    }

    env_name = env_names.get(environment, environment)
    comp_name = component_names.get(component, component)

    msg = f"""<b>🔐 Требуется авторизация</b>

<b>Операция:</b> Очистка данных
<b>Среда:</b> {env_name}
<b>Компонент:</b> {comp_name}

<b>Введи пароль:</b>
    """
    await send_message(msg.strip(), chat_id=chat_id)


async def handle_cleanup_password(chat_id: int, password: str) -> bool:
    """Обрабатывает ввод пароля для очистки."""
    global pending_cleanup_auth

    if chat_id not in pending_cleanup_auth:
        return False

    auth_data = pending_cleanup_auth[chat_id]
    environment = auth_data["environment"]
    component = auth_data["component"]

    # Проверяем пароль
    expected_password = LOAD_TEST_STAGING_PASSWORD if environment == "staging" else LOAD_TEST_PROD_PASSWORD

    if not expected_password:
        del pending_cleanup_auth[chat_id]
        await send_message_with_reply_keyboard(
            "❌ <b>Пароль не настроен!</b>\n\n<i>Обратись к администратору.</i>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return True

    if password != expected_password:
        del pending_cleanup_auth[chat_id]
        await send_message_with_reply_keyboard(
            "❌ <b>Неверный пароль!</b>",
            get_reply_keyboard(),
            chat_id=chat_id
        )
        return True

    # Пароль верный — выполняем очистку
    del pending_cleanup_auth[chat_id]
    await execute_cleanup(chat_id, environment, component)
    return True


async def execute_cleanup(chat_id: int, environment: str, component: str):
    """Выполняет очистку."""
    await send_chat_action(chat_id, "typing")

    component_names = {
        "redis": "Redis",
        "kafka": "Kafka",
        "postgres": "PostgreSQL",
        "all": "всех компонентов"
    }
    comp_name = component_names.get(component, component)

    await send_message(
        f"🧹 <b>Очистка {comp_name}...</b>\n\n<i>Это может занять несколько секунд...</i>",
        chat_id=chat_id
    )

    try:
        if component == "redis":
            result = {"redis": await cleanup_redis(environment)}
        elif component == "kafka":
            result = {"kafka": await cleanup_kafka(environment)}
        elif component == "postgres":
            result = {"postgres": await cleanup_postgres(environment)}
        else:  # all
            result = await cleanup_all(environment)

        msg = format_cleanup_result(result)
        await send_message_with_reply_keyboard(msg, get_reply_keyboard(), chat_id=chat_id)

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        await send_message_with_reply_keyboard(
            f"❌ <b>Ошибка очистки:</b>\n\n<code>{str(e)[:200]}</code>",
            get_reply_keyboard(),
            chat_id=chat_id
        )


def is_pending_cleanup_password(chat_id: int) -> bool:
    """Проверяет, ожидается ли пароль для cleanup."""
    return chat_id in pending_cleanup_auth
