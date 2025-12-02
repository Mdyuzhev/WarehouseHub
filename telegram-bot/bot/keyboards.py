"""
Клавиатуры Telegram бота.
Все кнопочки в одном месте! 🎹
"""


def get_reply_keyboard() -> dict:
    """
    Возвращает постоянную клавиатуру снизу экрана.
    WH-218: Нагрузка и Очистка перенесены внутрь QA меню.
    """
    return {
        "keyboard": [
            [{"text": "🏥 Статус"}, {"text": "📊 Метрики"}, {"text": "🚀 Деплой"}],
            [{"text": "🔬 QA"}, {"text": "🤖 Robot"}, {"text": "📋 PM"}],
            [{"text": "❓ Помощь"}],
        ],
        "resize_keyboard": True,
        "is_persistent": True,
        "input_field_placeholder": "Жми кнопку ☝️",
    }


def get_main_menu_keyboard() -> dict:
    """Возвращает главное меню с inline кнопками."""
    return {
        "inline_keyboard": [
            [
                {"text": "🏥 Статус серверов", "callback_data": "health"},
                {"text": "📊 Метрики", "callback_data": "metrics"},
            ],
            [
                {"text": "🚀 Деплой", "callback_data": "deploy_menu"},
                {"text": "🔬 QA", "callback_data": "qa_menu"},
            ],
            [
                {"text": "📋 PM Dashboard", "callback_data": "pm_menu"},
                {"text": "🤖 Robot", "callback_data": "robot_menu"},
            ],
            [
                {"text": "🎰 Анекдот", "callback_data": "joke"},
                {"text": "❓ Помощь", "callback_data": "help"},
            ],
        ]
    }


def get_deploy_menu_keyboard() -> dict:
    """Возвращает меню деплоя."""
    return {
        "inline_keyboard": [
            [{"text": "🧪 STAGING", "callback_data": "deploy_menu_staging"}],
            [
                {"text": "🔧 API", "callback_data": "deploy_api_staging"},
                {"text": "🎨 Frontend", "callback_data": "deploy_frontend_staging"},
            ],
            [{"text": "📦 Всё", "callback_data": "deploy_all_staging"}],
            [{"text": "─────────────", "callback_data": "noop"}],
            [{"text": "🚀 PRODUCTION", "callback_data": "deploy_menu_prod"}],
            [
                {"text": "🔧 API", "callback_data": "deploy_api_prod"},
                {"text": "🎨 Frontend", "callback_data": "deploy_frontend_prod"},
            ],
            [{"text": "📦 Всё", "callback_data": "deploy_all_prod"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }


def get_load_test_keyboard(target: str) -> dict:
    """Возвращает клавиатуру для выбора количества пользователей."""
    return {
        "inline_keyboard": [
            [
                {"text": "👤 10", "callback_data": f"lt_users_{target}_10"},
                {"text": "👥 25", "callback_data": f"lt_users_{target}_25"},
                {"text": "👥 50", "callback_data": f"lt_users_{target}_50"},
            ],
            [
                {"text": "💪 100", "callback_data": f"lt_users_{target}_100"},
                {"text": "🔥 200", "callback_data": f"lt_users_{target}_200"},
                {"text": "💀 500", "callback_data": f"lt_users_{target}_500"},
            ],
            [
                {"text": "✏️ Своё число", "callback_data": f"lt_users_{target}_custom"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": "menu"},
            ],
        ]
    }


def get_duration_keyboard(target: str, users: int) -> dict:
    """Возвращает клавиатуру для выбора длительности теста."""
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ 1 мин", "callback_data": f"lt_dur_{target}_{users}_60"},
                {"text": "⏱ 3 мин", "callback_data": f"lt_dur_{target}_{users}_180"},
                {"text": "🕐 5 мин", "callback_data": f"lt_dur_{target}_{users}_300"},
            ],
            [
                {"text": "🕑 10 мин", "callback_data": f"lt_dur_{target}_{users}_600"},
                {"text": "🕒 15 мин", "callback_data": f"lt_dur_{target}_{users}_900"},
                {"text": "🕕 30 мин", "callback_data": f"lt_dur_{target}_{users}_1800"},
            ],
            [
                {"text": "✏️ Своё время", "callback_data": f"lt_dur_{target}_{users}_custom"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": f"load_{target}"},
            ],
        ]
    }


def get_rampup_keyboard(target: str, users: int, duration: int) -> dict:
    """Возвращает клавиатуру для выбора паттерна нарастания нагрузки."""
    return {
        "inline_keyboard": [
            [
                {"text": "📈 Плавный", "callback_data": f"lt_ramp_{target}_{users}_{duration}_smooth"},
            ],
            [
                {"text": "⚡ Быстрый", "callback_data": f"lt_ramp_{target}_{users}_{duration}_fast"},
            ],
            [
                {"text": "🚀 Мгновенный", "callback_data": f"lt_ramp_{target}_{users}_{duration}_instant"},
            ],
            [
                {"text": "📊 Ступенчатый", "callback_data": f"lt_ramp_{target}_{users}_{duration}_step"},
            ],
            [
                {"text": "⬅️ Назад", "callback_data": f"lt_users_{target}_{users}"},
            ],
        ]
    }


def get_qa_menu_keyboard() -> dict:
    """Возвращает главное меню QA — выбор среды."""
    return {
        "inline_keyboard": [
            [{"text": "🧪 STAGING", "callback_data": "qa_staging"}],
            [{"text": "🚀 PRODUCTION", "callback_data": "qa_prod"}],
            [{"text": "⬅️ Назад в меню", "callback_data": "menu"}],
        ]
    }


def get_qa_type_keyboard(env: str) -> dict:
    """
    Возвращает меню выбора типа теста для среды.
    WH-218: Добавлена Очистка, Нагрузка ведёт на wizard.
    """
    env_emoji = "🧪" if env == "staging" else "🚀"
    env_name = "STAGING" if env == "staging" else "PROD"
    return {
        "inline_keyboard": [
            [{"text": f"📝 E2E тесты ({env_name})", "callback_data": f"qa_e2e_{env}"}],
            [{"text": f"🎭 UI тесты ({env_name})", "callback_data": f"qa_ui_{env}"}],
            [{"text": f"🔥 Нагрузка ({env_name})", "callback_data": f"qa_load_{env}"}],
            [{"text": f"🧹 Очистка ({env_name})", "callback_data": f"qa_cleanup_{env}"}],
            [{"text": "⬅️ Назад", "callback_data": "qa_menu"}],
        ]
    }


def get_qa_action_keyboard(test_type: str, env: str) -> dict:
    """Возвращает меню действий для выбранного теста."""
    type_names = {"e2e": "E2E", "ui": "UI", "load": "Нагрузка"}
    type_name = type_names.get(test_type, test_type.upper())
    env_name = "STAGING" if env == "staging" else "PROD"

    return {
        "inline_keyboard": [
            [{"text": "▶️ Запустить", "callback_data": f"qa_run_{test_type}_{env}"}],
            [{"text": "📊 Последний отчёт", "callback_data": f"qa_report_{test_type}_{env}"}],
            [{"text": "⬅️ Назад", "callback_data": f"qa_{env}"}],
        ]
    }


def get_pm_menu_keyboard() -> dict:
    """Возвращает клавиатуру PM Dashboard."""
    return {
        "inline_keyboard": [
            [{"text": "🔄 Сейчас в работе", "callback_data": "pm_in_progress"}],
            [{"text": "📋 Аудит сторей", "callback_data": "pm_audit"}],
            [
                {"text": "📈 За день", "callback_data": "pm_report_day"},
                {"text": "📅 За неделю", "callback_data": "pm_report_week"},
            ],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }


def get_robot_menu_keyboard() -> dict:
    """Возвращает клавиатуру меню робота."""
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
    """Возвращает клавиатуру выбора сценария."""
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
    """Возвращает клавиатуру выбора продолжительности повторения сценария."""
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
    """Возвращает клавиатуру выбора окружения."""
    return {
        "inline_keyboard": [
            [{"text": "🔧 STAGING (тест)", "callback_data": f"robot_env_{scenario}_{duration}_staging"}],
            [{"text": "🚀 PROD (боевой)", "callback_data": f"robot_env_{scenario}_{duration}_prod"}],
            [{"text": "⬅️ Назад", "callback_data": f"robot_run_{scenario}"}],
        ]
    }


def get_robot_speed_keyboard(scenario: str, duration: int, environment: str = "staging") -> dict:
    """
    Возвращает клавиатуру выбора скорости (паузы между повторениями).

    - Медленно: пауза 15 секунд
    - Нормально: пауза 5 секунд (по умолчанию)
    - Быстро: пауза 1 секунда
    """
    return {
        "inline_keyboard": [
            [{"text": "🐢 Медленно (15с)", "callback_data": f"robot_speed_{scenario}_{duration}_{environment}_slow"}],
            [{"text": "🚶 Нормально (5с)", "callback_data": f"robot_speed_{scenario}_{duration}_{environment}_normal"}],
            [{"text": "🚀 Быстро (1с)", "callback_data": f"robot_speed_{scenario}_{duration}_{environment}_fast"}],
            [{"text": "⬅️ Назад", "callback_data": f"robot_env_{scenario}_{duration}_{environment}"}],
        ]
    }


def get_robot_schedule_scenario_keyboard() -> dict:
    """Возвращает клавиатуру выбора сценария для расписания."""
    return {
        "inline_keyboard": [
            [{"text": "📦 Приёмка", "callback_data": "robot_sched_receiving"}],
            [{"text": "🚚 Отгрузка", "callback_data": "robot_sched_shipping"}],
            [{"text": "📋 Инвентаризация", "callback_data": "robot_sched_inventory"}],
            [{"text": "⬅️ Назад", "callback_data": "robot_menu"}],
        ]
    }


def get_robot_schedule_env_keyboard(scenario: str) -> dict:
    """Возвращает клавиатуру выбора окружения для расписания."""
    return {
        "inline_keyboard": [
            [{"text": "🔧 STAGING (тест)", "callback_data": f"robot_schedenv_{scenario}_staging"}],
            [{"text": "🚀 PROD (боевой)", "callback_data": f"robot_schedenv_{scenario}_prod"}],
            [{"text": "⬅️ Назад", "callback_data": "robot_schedule"}],
        ]
    }


def get_robot_schedule_time_keyboard(scenario: str, environment: str = "staging") -> dict:
    """Возвращает клавиатуру выбора времени для расписания."""
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
    """Возвращает клавиатуру списка запланированных задач."""
    buttons = []
    for task in tasks[:5]:  # Максимум 5 задач
        task_id = task.get("task_id", "")
        scenario = task.get("scenario", "")
        emoji = {"receiving": "📦", "shipping": "🚚", "inventory": "📋"}.get(scenario, "🤖")
        buttons.append([{"text": f"❌ {emoji} {scenario} ({task_id})", "callback_data": f"robot_cancel_{task_id}"}])
    buttons.append([{"text": "⬅️ Назад", "callback_data": "robot_menu"}])
    return {"inline_keyboard": buttons}


# =============================================================================
# WH-217: Клавиатуры нагрузочного тестирования
# =============================================================================

def get_load_env_keyboard() -> dict:
    """
    Клавиатура выбора среды для нагрузочного тестирования.
    Шаг 1 из 7 wizard.
    WH-228
    """
    return {
        "inline_keyboard": [
            [{"text": "🧪 STAGING", "callback_data": "load_env_staging"}],
            [{"text": "🚀 PRODUCTION", "callback_data": "load_env_prod"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }


def get_load_scenario_keyboard(environment: str) -> dict:
    """
    Клавиатура выбора типа нагрузочного теста.
    Шаг 3 из 7 wizard.
    WH-229

    Args:
        environment: 'staging' или 'prod'
    """
    return {
        "inline_keyboard": [
            [{"text": "🦗 Locust (HTTP)", "callback_data": f"load_scenario_{environment}_locust"}],
            [{"text": "⚡ k6 (Kafka)", "callback_data": f"load_scenario_{environment}_k6"}],
            [{"text": "⬅️ Назад", "callback_data": "load_menu"}],
        ]
    }


def get_load_users_keyboard(environment: str, scenario: str) -> dict:
    """
    Клавиатура выбора количества VU.
    Шаг 4 из 7 wizard.
    Упрощённый набор: 10, 25, 50 VU.
    WH-230
    """
    return {
        "inline_keyboard": [
            [
                {"text": "👤 10 VU", "callback_data": f"load_users_{environment}_{scenario}_10"},
                {"text": "👥 25 VU", "callback_data": f"load_users_{environment}_{scenario}_25"},
                {"text": "👥 50 VU", "callback_data": f"load_users_{environment}_{scenario}_50"},
            ],
            [{"text": "⬅️ Назад", "callback_data": f"load_scenario_{environment}"}],
        ]
    }


def get_load_duration_keyboard(environment: str, scenario: str, users: int) -> dict:
    """
    Клавиатура выбора длительности теста.
    Шаг 5 из 7 wizard.
    Упрощённый набор: 2, 5, 10 минут.
    WH-231
    """
    return {
        "inline_keyboard": [
            [
                {"text": "⚡ 2 мин", "callback_data": f"load_dur_{environment}_{scenario}_{users}_120"},
                {"text": "⏱ 5 мин", "callback_data": f"load_dur_{environment}_{scenario}_{users}_300"},
                {"text": "🕐 10 мин", "callback_data": f"load_dur_{environment}_{scenario}_{users}_600"},
            ],
            [{"text": "⬅️ Назад", "callback_data": f"load_users_{environment}_{scenario}_{users}"}],
        ]
    }


def get_load_pattern_keyboard(environment: str, scenario: str, users: int, duration: int) -> dict:
    """
    Клавиатура выбора паттерна нарастания нагрузки.
    Шаг 6 из 7 wizard.
    """
    return {
        "inline_keyboard": [
            [{"text": "📈 Плавный", "callback_data": f"load_pattern_{environment}_{scenario}_{users}_{duration}_smooth"}],
            [{"text": "⚡ Быстрый", "callback_data": f"load_pattern_{environment}_{scenario}_{users}_{duration}_fast"}],
            [{"text": "🚀 Мгновенный", "callback_data": f"load_pattern_{environment}_{scenario}_{users}_{duration}_instant"}],
            [{"text": "📊 Ступенчатый", "callback_data": f"load_pattern_{environment}_{scenario}_{users}_{duration}_step"}],
            [{"text": "⬅️ Назад", "callback_data": f"load_dur_{environment}_{scenario}_{users}_{duration}"}],
        ]
    }


def get_load_confirm_keyboard(environment: str, scenario: str, users: int, duration: int, pattern: str) -> dict:
    """
    Клавиатура подтверждения запуска НТ.
    Шаг 7 из 7 wizard — финальное подтверждение.
    WH-232
    """
    return {
        "inline_keyboard": [
            [{"text": "✅ Запустить", "callback_data": f"load_confirm_{environment}_{scenario}_{users}_{duration}_{pattern}"}],
            [{"text": "❌ Отмена", "callback_data": "load_menu"}],
        ]
    }


def get_load_status_keyboard() -> dict:
    """
    Клавиатура статуса нагрузочного теста.
    Показывается когда тест запущен.
    WH-234
    """
    return {
        "inline_keyboard": [
            [
                {"text": "🔄 Обновить", "callback_data": "load_status_refresh"},
                {"text": "🛑 Остановить", "callback_data": "load_stop"},
            ],
            [{"text": "⬅️ В меню", "callback_data": "menu"}],
        ]
    }


def get_load_idle_keyboard() -> dict:
    """
    Клавиатура когда нет активного теста.
    WH-234
    """
    return {
        "inline_keyboard": [
            [{"text": "🔥 Запустить тест", "callback_data": "load_menu"}],
            [{"text": "📊 История", "callback_data": "load_history"}],
            [{"text": "⬅️ В меню", "callback_data": "menu"}],
        ]
    }


# =============================================================================
# WH-233: Клавиатуры очистки данных
# =============================================================================

def get_cleanup_env_keyboard() -> dict:
    """
    Клавиатура выбора среды для очистки данных.
    WH-233
    """
    return {
        "inline_keyboard": [
            [{"text": "🧪 STAGING", "callback_data": "cleanup_staging"}],
            [{"text": "🚀 PRODUCTION ⚠️", "callback_data": "cleanup_prod"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }


def get_cleanup_confirm_keyboard(environment: str) -> dict:
    """
    Клавиатура подтверждения очистки.
    WH-233
    """
    return {
        "inline_keyboard": [
            [{"text": "🗑 Redis", "callback_data": f"cleanup_redis_{environment}"}],
            [{"text": "📨 Kafka", "callback_data": f"cleanup_kafka_{environment}"}],
            [{"text": "🗄 PostgreSQL", "callback_data": f"cleanup_postgres_{environment}"}],
            [{"text": "💥 Всё сразу", "callback_data": f"cleanup_all_{environment}"}],
            [{"text": "⬅️ Назад", "callback_data": "cleanup_menu"}],
        ]
    }
