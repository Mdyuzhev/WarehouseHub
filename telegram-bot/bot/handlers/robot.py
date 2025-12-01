# -*- coding: utf-8 -*-
"""
Обработчики команд робота-симулятора.
Запуск сценариев, мониторинг, управление.
"""

import logging
from typing import Dict, Any, Set

from services import robot_service
from config import ROBOT_PASSWORD
from bot.messages import (
    format_robot_menu,
    format_robot_status,
    format_robot_stats,
    format_robot_started,
    format_robot_stopped,
    format_robot_error,
)
from bot.keyboards import (
    get_robot_menu_keyboard,
    get_robot_scenario_keyboard,
    get_robot_duration_keyboard,
    get_robot_environment_keyboard,
    get_robot_speed_keyboard,
    get_robot_schedule_scenario_keyboard,
    get_robot_schedule_env_keyboard,
    get_robot_schedule_time_keyboard,
    get_robot_scheduled_keyboard,
)

logger = logging.getLogger(__name__)

# Ожидание ввода пароля для робота
_pending_robot_password: Set[int] = set()

# Хранилище выбранного сценария для пользователя
_pending_robot_scenario: Dict[int, str] = {}

# Хранилище выбранной продолжительности для пользователя
_pending_robot_duration: Dict[int, int] = {}

# Хранилище выбранного окружения для пользователя
_pending_robot_environment: Dict[int, str] = {}

# Ожидание ввода времени для расписания
_pending_schedule_time: Dict[int, Dict[str, str]] = {}  # chat_id -> {scenario, environment}


def is_pending_robot_password(chat_id: int) -> bool:
    """Проверяет, ожидается ли ввод пароля для робота."""
    return chat_id in _pending_robot_password


def is_pending_robot_scenario(chat_id: int) -> bool:
    """Проверяет, выбран ли сценарий для запуска."""
    return chat_id in _pending_robot_scenario


def is_pending_schedule_time(chat_id: int) -> bool:
    """Проверяет, ожидается ли ввод времени для расписания."""
    return chat_id in _pending_schedule_time


async def handle_robot_menu(send_message, chat_id: int, message_id: int = None) -> None:
    """
    Показать меню робота.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        message_id: ID сообщения для редактирования
    """
    logger.info(f"Robot menu requested by chat {chat_id}")

    # Получаем статус робота
    status = robot_service.get_status()

    if status:
        text = format_robot_menu(status)
    else:
        text = "🤖 *Warehouse Robot*\n\n⚠️ Робот недоступен"

    keyboard = get_robot_menu_keyboard()

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_status(send_message, chat_id: int, message_id: int = None) -> None:
    """
    Показать статус робота.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        message_id: ID сообщения для редактирования
    """
    logger.info(f"Robot status requested by chat {chat_id}")

    status = robot_service.get_status()
    health = robot_service.get_health()

    if status and health:
        text = format_robot_status(status, health)
    else:
        text = "❌ Не удалось получить статус робота"

    keyboard = {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "robot_menu"}]]}

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_stats(send_message, chat_id: int, message_id: int = None) -> None:
    """
    Показать статистику робота.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        message_id: ID сообщения для редактирования
    """
    logger.info(f"Robot stats requested by chat {chat_id}")

    stats = robot_service.get_stats()

    if stats:
        text = format_robot_stats(stats)
    else:
        text = "❌ Не удалось получить статистику робота"

    keyboard = {"inline_keyboard": [[{"text": "⬅️ Назад", "callback_data": "robot_menu"}]]}

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_scenarios(send_message, chat_id: int, message_id: int = None) -> None:
    """
    Показать меню выбора сценария.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        message_id: ID сообщения для редактирования
    """
    logger.info(f"Robot scenarios requested by chat {chat_id}")

    text = "🎬 *Выберите сценарий*\n\n" \
           "📦 *Приёмка* — создание новых товаров\n" \
           "🚚 *Отгрузка* — уменьшение остатков\n" \
           "📋 *Инвентаризация* — корректировка и списание"

    keyboard = get_robot_scenario_keyboard()

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_duration_select(send_message, chat_id: int, scenario: str, message_id: int = None) -> None:
    """
    Показать выбор продолжительности повторения сценария.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        scenario: Название сценария
        message_id: ID сообщения для редактирования
    """
    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }

    text = (
        f"⏱ *Выберите продолжительность*\n\n"
        f"Сценарий: {scenario_names.get(scenario, scenario)}\n\n"
        f"Сценарий будет повторяться с паузами в течение выбранного времени."
    )

    keyboard = get_robot_duration_keyboard(scenario)

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_environment_select(send_message, chat_id: int, scenario: str, duration: int = 0, message_id: int = None) -> None:
    """
    Показать выбор окружения.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        scenario: Название сценария
        duration: Продолжительность в минутах (0 = один раз)
        message_id: ID сообщения для редактирования
    """
    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }
    duration_labels = {
        0: "один раз",
        5: "5 минут",
        30: "30 минут",
        60: "1 час",
    }

    text = (
        f"🌍 *Выберите окружение*\n\n"
        f"Сценарий: {scenario_names.get(scenario, scenario)}\n"
        f"Продолжительность: {duration_labels.get(duration, f'{duration} мин')}"
    )

    keyboard = get_robot_environment_keyboard(scenario, duration)

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def request_robot_password(send_message, chat_id: int, scenario: str, duration: int = 0, environment: str = "staging") -> None:
    """
    Запросить пароль для запуска сценария.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        scenario: Название сценария
        duration: Продолжительность в минутах
        environment: Окружение (staging/prod)
    """
    _pending_robot_password.add(chat_id)
    _pending_robot_scenario[chat_id] = scenario
    _pending_robot_duration[chat_id] = duration
    _pending_robot_environment[chat_id] = environment

    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }
    env_label = "🔧 STAGING" if environment == "staging" else "🚀 PROD"
    duration_labels = {
        0: "один раз",
        5: "5 минут",
        30: "30 минут",
        60: "1 час",
    }

    text = (
        f"🔐 *Введите пароль для запуска*\n\n"
        f"Сценарий: {scenario_names.get(scenario, scenario)}\n"
        f"Продолжительность: {duration_labels.get(duration, f'{duration} мин')}\n"
        f"Окружение: {env_label}"
    )

    await send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
    )


async def handle_robot_password_input(send_message, chat_id: int, password: str) -> None:
    """
    Обработать ввод пароля для запуска сценария.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        password: Введённый пароль
    """
    _pending_robot_password.discard(chat_id)
    scenario = _pending_robot_scenario.pop(chat_id, None)
    duration = _pending_robot_duration.pop(chat_id, 0)
    environment = _pending_robot_environment.pop(chat_id, "staging")

    if not scenario:
        await send_message(
            chat_id=chat_id,
            text="❌ Сценарий не выбран. Начните сначала.",
        )
        return

    if password != ROBOT_PASSWORD:
        await send_message(
            chat_id=chat_id,
            text="❌ Неверный пароль!",
        )
        return

    # Показываем выбор скорости
    await handle_robot_speed_select(send_message, chat_id, scenario, duration, environment)


async def handle_robot_speed_select(send_message, chat_id: int, scenario: str, duration: int = 0, environment: str = "staging") -> None:
    """
    Показать выбор скорости выполнения (пауза между повторениями).

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        scenario: Название сценария
        duration: Продолжительность в минутах
        environment: Окружение (staging/prod)
    """
    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }
    env_label = "🔧 STAGING" if environment == "staging" else "🚀 PROD"
    duration_labels = {
        0: "один раз",
        5: "5 минут",
        30: "30 минут",
        60: "1 час",
    }

    text = (
        f"⚡ *Выберите скорость*\n\n"
        f"Сценарий: {scenario_names.get(scenario, scenario)}\n"
        f"Продолжительность: {duration_labels.get(duration, f'{duration} мин')}\n"
        f"Окружение: {env_label}\n\n"
        f"Скорость определяет паузу между повторениями сценария."
    )

    keyboard = get_robot_speed_keyboard(scenario, duration, environment)

    await send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def handle_robot_start(
    send_message, chat_id: int, scenario: str, duration: int, speed: str, environment: str = "staging", message_id: int = None
) -> None:
    """
    Запустить сценарий робота.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        scenario: Название сценария
        duration: Продолжительность в минутах (0 = один раз)
        speed: Скорость выполнения (slow=15с, normal=5с, fast=1с)
        environment: Окружение (staging/prod)
        message_id: ID сообщения для редактирования
    """
    env_label = "STAGING" if environment == "staging" else "PROD"
    logger.info(f"Starting robot scenario: {scenario} (duration={duration}min, speed={speed}, env={environment}) for chat {chat_id}")

    result = robot_service.start_scenario(scenario, speed, environment, duration)

    if result and result.get("status") == "started":
        text = format_robot_started(scenario, speed, environment, duration)
    else:
        error = result.get("detail", "Неизвестная ошибка") if result else "Робот недоступен"
        text = format_robot_error(error)

    keyboard = {"inline_keyboard": [[{"text": "⬅️ К роботу", "callback_data": "robot_menu"}]]}

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_stop(send_message, chat_id: int, message_id: int = None) -> None:
    """
    Остановить робота.

    Args:
        send_message: Функция отправки сообщения
        chat_id: ID чата
        message_id: ID сообщения для редактирования
    """
    logger.info(f"Stopping robot for chat {chat_id}")

    result = robot_service.stop()

    if result and result.get("status") == "stopping":
        text = format_robot_stopped()
    else:
        error = result.get("detail", "Робот не запущен") if result else "Робот недоступен"
        text = format_robot_error(error)

    keyboard = {"inline_keyboard": [[{"text": "⬅️ К роботу", "callback_data": "robot_menu"}]]}

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


# === Функции для работы с расписанием ===

async def handle_robot_schedule_menu(send_message, chat_id: int, message_id: int = None) -> None:
    """Показать меню выбора сценария для расписания."""
    logger.info(f"Robot schedule menu requested by chat {chat_id}")

    text = "⏰ *Запланировать запуск*\n\n" \
           "Выберите сценарий для планирования:"

    keyboard = get_robot_schedule_scenario_keyboard()

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_schedule_env(send_message, chat_id: int, scenario: str, message_id: int = None) -> None:
    """Показать выбор окружения для расписания."""
    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }

    text = f"🌍 *Выберите окружение*\n\nСценарий: {scenario_names.get(scenario, scenario)}"

    keyboard = get_robot_schedule_env_keyboard(scenario)

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_schedule_time(
    send_message, chat_id: int, scenario: str, environment: str = "staging", message_id: int = None
) -> None:
    """Показать выбор времени для расписания."""
    scenario_names = {
        "receiving": "Приёмка",
        "shipping": "Отгрузка",
        "inventory": "Инвентаризация",
    }
    env_label = "🔧 STAGING" if environment == "staging" else "🚀 PROD"

    text = (
        f"⏰ *Когда запустить?*\n\n"
        f"Сценарий: {scenario_names.get(scenario, scenario)}\n"
        f"Окружение: {env_label}\n\n"
        f"_Время указывается по МСК (UTC+3)_"
    )

    keyboard = get_robot_schedule_time_keyboard(scenario, environment)

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_schedule_create(
    send_message, chat_id: int, scenario: str, minutes: int, environment: str = "staging", message_id: int = None
) -> None:
    """Создать запланированную задачу."""
    from datetime import datetime, timedelta

    scheduled_time = datetime.now() + timedelta(minutes=minutes)
    time_str = scheduled_time.strftime("%H:%M")
    env_label = "🔧 STAGING" if environment == "staging" else "🚀 PROD"

    logger.info(f"Scheduling robot scenario: {scenario} at {time_str} (env={environment}) for chat {chat_id}")

    result = robot_service.schedule_scenario(scenario, time_str, speed="normal", environment=environment)

    if result and result.get("status") == "scheduled":
        task_id = result.get("task_id", "")
        text = (
            f"✅ *Сценарий запланирован!*\n\n"
            f"📋 Сценарий: {scenario}\n"
            f"🌍 Окружение: {env_label}\n"
            f"⏰ Время: {time_str} (МСК)\n"
            f"🆔 ID задачи: `{task_id}`\n\n"
            f"Робот запустится автоматически."
        )
    else:
        error = result.get("detail", "Неизвестная ошибка") if result else "Робот недоступен"
        text = f"❌ *Ошибка планирования*\n\n{error}"

    keyboard = {"inline_keyboard": [[{"text": "⬅️ К роботу", "callback_data": "robot_menu"}]]}

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def request_schedule_time_input(send_message, chat_id: int, scenario: str, environment: str = "staging") -> None:
    """Запросить ввод времени для расписания."""
    _pending_schedule_time[chat_id] = {"scenario": scenario, "environment": environment}
    env_label = "🔧 STAGING" if environment == "staging" else "🚀 PROD"

    text = (
        f"⏰ *Введите время запуска (МСК)*\n\n"
        f"Сценарий: {scenario}\n"
        f"Окружение: {env_label}\n\n"
        f"Формат: HH:MM (например, 14:30)\n"
        f"_Время по Москве (UTC+3)_\n\n"
        f"Если время уже прошло сегодня — запуск будет завтра."
    )

    await send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
    )


async def handle_schedule_time_input(send_message, chat_id: int, time_str: str) -> None:
    """Обработать ввод времени для расписания."""
    pending = _pending_schedule_time.pop(chat_id, None)

    if not pending:
        await send_message(
            chat_id=chat_id,
            text="❌ Сценарий не выбран. Начните сначала.",
        )
        return

    scenario = pending.get("scenario")
    environment = pending.get("environment", "staging")
    env_label = "🔧 STAGING" if environment == "staging" else "🚀 PROD"

    # Валидация формата времени
    import re
    if not re.match(r"^\d{1,2}:\d{2}$", time_str):
        await send_message(
            chat_id=chat_id,
            text="❌ Неверный формат времени. Используйте HH:MM (например, 14:30)",
        )
        return

    logger.info(f"Scheduling robot scenario: {scenario} at {time_str} (env={environment}) for chat {chat_id}")

    result = robot_service.schedule_scenario(scenario, time_str, speed="normal", environment=environment)

    if result and result.get("status") == "scheduled":
        task_id = result.get("task_id", "")
        scheduled = result.get("scheduled_time", "")
        text = (
            f"✅ *Сценарий запланирован!*\n\n"
            f"📋 Сценарий: {scenario}\n"
            f"🌍 Окружение: {env_label}\n"
            f"⏰ Время: {scheduled[:16].replace('T', ' ')}\n"
            f"🆔 ID задачи: `{task_id}`"
        )
    else:
        error = result.get("detail", "Неизвестная ошибка") if result else "Робот недоступен"
        text = f"❌ *Ошибка планирования*\n\n{error}"

    keyboard = {"inline_keyboard": [[{"text": "⬅️ К роботу", "callback_data": "robot_menu"}]]}

    await send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )


async def handle_robot_scheduled_list(send_message, chat_id: int, message_id: int = None) -> None:
    """Показать список запланированных задач."""
    logger.info(f"Robot scheduled list requested by chat {chat_id}")

    tasks = robot_service.get_scheduled()

    if tasks:
        text = "📅 *Запланированные задачи*\n\n"
        for task in tasks:
            scenario = task.get("scenario", "")
            scheduled = task.get("scheduled_time", "")[:16].replace("T", " ")
            task_id = task.get("task_id", "")
            environment = task.get("environment", "staging")
            env_emoji = "🔧" if environment == "staging" else "🚀"
            emoji = {"receiving": "📦", "shipping": "🚚", "inventory": "📋"}.get(scenario, "🤖")
            text += f"{emoji} {scenario} {env_emoji} — {scheduled} (`{task_id}`)\n"
        text += "\nНажмите на задачу для отмены:"
    else:
        text = "📅 *Запланированные задачи*\n\nНет запланированных задач."

    keyboard = get_robot_scheduled_keyboard(tasks)

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )


async def handle_robot_cancel_scheduled(send_message, chat_id: int, task_id: str, message_id: int = None) -> None:
    """Отменить запланированную задачу."""
    logger.info(f"Cancelling scheduled task {task_id} for chat {chat_id}")

    result = robot_service.cancel_scheduled(task_id)

    if result and result.get("status") == "cancelled":
        text = f"✅ Задача `{task_id}` отменена"
    else:
        error = result.get("detail", "Задача не найдена") if result else "Робот недоступен"
        text = f"❌ {error}"

    keyboard = {"inline_keyboard": [[{"text": "⬅️ К расписанию", "callback_data": "robot_scheduled"}]]}

    if message_id:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
            edit_message_id=message_id,
        )
    else:
        await send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
