"""
Клавиатуры Telegram бота.
Все кнопочки в одном месте! 🎹
"""


def get_reply_keyboard() -> dict:
    """Возвращает постоянную клавиатуру снизу экрана."""
    return {
        "keyboard": [
            [{"text": "🏥 Статус"}, {"text": "📊 Метрики"}, {"text": "🚀 Деплой"}],
            [{"text": "🧪 E2E"}, {"text": "🔥 Нагрузка"}, {"text": "🛑 Стоп"}],
            [{"text": "🤖 Claude"}, {"text": "🎰 Шутка"}, {"text": "❓"}],
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
                {"text": "🧪 E2E тесты", "callback_data": "e2e_run"},
            ],
            [
                {"text": "🔥 Нагрузка: STAGING", "callback_data": "load_staging"},
                {"text": "⚠️ Нагрузка: PROD", "callback_data": "load_prod"},
            ],
            [
                {"text": "🛑 Остановить тест", "callback_data": "load_stop"},
                {"text": "📈 Статус теста", "callback_data": "load_status"},
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


def get_e2e_keyboard() -> dict:
    """Возвращает клавиатуру для E2E тестов."""
    return {
        "inline_keyboard": [
            [{"text": "▶️ Запустить тесты", "callback_data": "e2e_run"}],
            [{"text": "📊 Последний отчёт", "callback_data": "e2e_report"}],
            [{"text": "⬅️ Назад", "callback_data": "menu"}],
        ]
    }
