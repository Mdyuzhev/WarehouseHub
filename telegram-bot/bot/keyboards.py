"""
Keyboards for Telegram bot.
Minimal: status, metrics, robot, help.
"""


def get_reply_keyboard() -> dict:
    return {
        "keyboard": [
            [{"text": "🏥 Статус"}, {"text": "📊 Метрики"}],
            [{"text": "🤖 Robot"}, {"text": "❓ Помощь"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
        "input_field_placeholder": "Жми кнопку",
    }


def get_main_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "🏥 Статус", "callback_data": "health"},
                {"text": "📊 Метрики", "callback_data": "metrics"},
            ],
            [
                {"text": "🤖 Robot", "callback_data": "robot_menu"},
                {"text": "❓ Помощь", "callback_data": "help"},
            ],
        ]
    }


def get_robot_menu_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "▶️ Запустить сценарий", "callback_data": "robot_scenarios"}],
            [{"text": "⏰ Запланировать", "callback_data": "robot_schedule"}],
            [{"text": "🛑 Остановить", "callback_data": "robot_stop"}],
            [
                {"text": "📊 Статус", "callback_data": "robot_status"},
                {"text": "📈 Статистика", "callback_data": "robot_stats"},
            ],
            [{"text": "📅 Расписание", "callback_data": "robot_scheduled"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }


def get_robot_scenario_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📦 Приёмка", "callback_data": "robot_run_receiving"}],
            [{"text": "🚚 Отгрузка", "callback_data": "robot_run_shipping"}],
            [{"text": "📋 Инвентаризация", "callback_data": "robot_run_inventory"}],
            [{"text": "🎲 Все сценарии", "callback_data": "robot_run_all"}],
            [{"text": "⬅️ Назад", "callback_data": "robot_menu"}],
        ]
    }


def get_robot_duration_keyboard(scenario: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "⚡ 5 минут", "callback_data": f"robot_dur_{scenario}_5"}],
            [{"text": "⏱ 30 минут", "callback_data": f"robot_dur_{scenario}_30"}],
            [{"text": "🕐 1 час", "callback_data": f"robot_dur_{scenario}_60"}],
            [{"text": "🔂 Один раз", "callback_data": f"robot_dur_{scenario}_0"}],
            [{"text": "⬅️ Назад", "callback_data": "robot_scenarios"}],
        ]
    }


def get_robot_environment_keyboard(scenario: str, duration: int = 0) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🔧 STAGING (тест)", "callback_data": f"robot_env_{scenario}_{duration}_staging"}],
            [{"text": "🚀 PROD (боевой)", "callback_data": f"robot_env_{scenario}_{duration}_prod"}],
            [{"text": "⬅️ Назад", "callback_data": f"robot_run_{scenario}"}],
        ]
    }


def get_robot_speed_keyboard(scenario: str, duration: int, environment: str = "staging") -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🐢 Медленно (15с)", "callback_data": f"robot_speed_{scenario}_{duration}_{environment}_slow"}],
            [{"text": "🚶 Нормально (5с)", "callback_data": f"robot_speed_{scenario}_{duration}_{environment}_normal"}],
            [{"text": "🚀 Быстро (1с)", "callback_data": f"robot_speed_{scenario}_{duration}_{environment}_fast"}],
            [{"text": "⬅️ Назад", "callback_data": f"robot_env_{scenario}_{duration}_{environment}"}],
        ]
    }


def get_robot_schedule_scenario_keyboard() -> dict:
    return {
        "inline_keyboard": [
            [{"text": "📦 Приёмка", "callback_data": "robot_sched_receiving"}],
            [{"text": "🚚 Отгрузка", "callback_data": "robot_sched_shipping"}],
            [{"text": "📋 Инвентаризация", "callback_data": "robot_sched_inventory"}],
            [{"text": "⬅️ Назад", "callback_data": "robot_menu"}],
        ]
    }


def get_robot_schedule_env_keyboard(scenario: str) -> dict:
    return {
        "inline_keyboard": [
            [{"text": "🔧 STAGING (тест)", "callback_data": f"robot_schedenv_{scenario}_staging"}],
            [{"text": "🚀 PROD (боевой)", "callback_data": f"robot_schedenv_{scenario}_prod"}],
            [{"text": "⬅️ Назад", "callback_data": "robot_schedule"}],
        ]
    }


def get_robot_schedule_time_keyboard(scenario: str, environment: str = "staging") -> dict:
    return {
        "inline_keyboard": [
            [
                {"text": "⏰ +5 мин", "callback_data": f"robot_time_{scenario}_{environment}_5"},
                {"text": "⏰ +15 мин", "callback_data": f"robot_time_{scenario}_{environment}_15"},
                {"text": "⏰ +30 мин", "callback_data": f"robot_time_{scenario}_{environment}_30"},
            ],
            [
                {"text": "🕐 +1 час", "callback_data": f"robot_time_{scenario}_{environment}_60"},
                {"text": "🕑 +2 часа", "callback_data": f"robot_time_{scenario}_{environment}_120"},
                {"text": "🕕 +6 часов", "callback_data": f"robot_time_{scenario}_{environment}_360"},
            ],
            [{"text": "✏️ Ввести время (HH:MM)", "callback_data": f"robot_time_{scenario}_{environment}_custom"}],
            [{"text": "⬅️ Назад", "callback_data": f"robot_sched_{scenario}"}],
        ]
    }


def get_robot_scheduled_keyboard(tasks: list) -> dict:
    buttons = []
    for task in tasks[:5]:
        task_id = task.get("task_id", "")
        scenario = task.get("scenario", "")
        emoji = {"receiving": "📦", "shipping": "🚚", "inventory": "📋"}.get(scenario, "🤖")
        buttons.append([{"text": f"❌ {emoji} {scenario} ({task_id})", "callback_data": f"robot_cancel_{task_id}"}])
    buttons.append([{"text": "⬅️ Назад", "callback_data": "robot_menu"}])
    return {"inline_keyboard": buttons}
