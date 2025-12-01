"""
Сообщения и юмор бота.
Все шутки, форматирование и мемы живут здесь! 🎭
"""

import random
from datetime import datetime


def format_money(value: float) -> str:
    """
    Форматирует денежную сумму с разделителями тысяч.

    Примеры:
        7553018.76 -> "7 553 018.76 ₽"
        1234.50 -> "1 234.50 ₽"
        500.00 -> "500.00 ₽"
    """
    # Форматируем число с разделителями тысяч (пробелами)
    formatted = f"{value:,.2f}".replace(",", " ")
    return f"{formatted} ₽"

# =============================================================================
# JOKES - Юмористические фразы 🎭
# =============================================================================

JOKES = {
    "start": [
        "Привет, кожаный мешок! 🤖 Я бот, который следит за твоим кодом лучше, чем ты сам.",
        "О, новый раб CI/CD пришёл! Добро пожаловать! 👋",
        "Здравствуй, человек. Надеюсь, твои пайплайны не так сломаны, как твоя жизнь. 😏",
        "Приветствую! Я тот, кто видит все твои failed pipelines в 3 часа ночи. 🌙",
    ],
    "health_good": [
        "Всё работает! Даже странно... 🤔",
        "Серверы живы! В отличие от твоего sleep schedule. 😴",
        "Зелёненькое! Как и должно быть. Наслаждайся, пока можешь. ✨",
        "Удивительно, но всё ОК! Это точно наш проект? 🧐",
    ],
    "health_bad": [
        "Хьюстон, у нас проблемы! 🚨",
        "Что-то сломалось... Опять. Как обычно. 💔",
        "RED ALERT! Кто-то опять запушил в пятницу вечером? 🔥",
        "Пора паниковать! Или кофе. Лучше кофе. ☕",
    ],
    "load_test_start": [
        "Запускаю нагрузку! Сервера, держитесь! 💪",
        "Время стресс-теста! Как твоя жизнь, только для серверов. 🏋️",
        "Поехали! Надеюсь, сервер крепче твоих нервов. 🎢",
        "Unleashing the LOAD! Пристегнись! 🚀",
    ],
    "load_test_stop": [
        "Тест остановлен. Сервера выдохнули. 😮‍💨",
        "Всё, хватит мучать железо на сегодня. 🛑",
        "Нагрузка снята. Можно расслабиться. 🧘",
    ],
    "e2e_start": [
        "Запускаю E2E тесты! Надеюсь, ты ничего не сломал... 🤞",
        "Поехали проверять! Сейчас узнаем, кто тут накосячил. 🔍",
        "E2E тесты в деле! Время узнать правду о твоём коде. 🎯",
        "Тестируем API! Скрестил пальцы за тебя. 🤖",
    ],
    "e2e_success": [
        "ВСЕ ТЕСТЫ ПРОШЛИ! 🎉 Ты красавчик! (или тестов мало...)",
        "Зелёненькое! Редкое зрелище в наши дни. ✅",
        "100% passed! Кажется, сегодня можно спать спокойно. 😌",
        "Тесты в порядке! Чудеса случаются! ✨",
    ],
    "e2e_failure": [
        "Упс... Кто-то сломал тесты! Не ты ли? 🤔",
        "FAILED! Время искать виноватого. Спойлер: это ты. 💀",
        "Тесты упали. Классика. Кофе? ☕",
        "Красненькое! Надеюсь, это не прод... 🔴",
    ],
    "deploy_start": [
        "Поехали деплоить! Держитесь, сервера! 🚀",
        "Запускаю деплой... Надеюсь, ты всё проверил! 🤞",
        "Деплой пошёл! Время пить кофе и ждать... ☕",
        "Отправляю код на сервера! Скрестил пальцы! 🎯",
    ],
    "deploy_success": [
        "Деплой успешен! 🎉 Всё взлетело!",
        "Готово! Сервера обновлены! ✅",
        "Задеплоено! Идём проверять... 🔍",
        "Успех! Ты молодец (ну или CI молодец)! 🏆",
    ],
    "deploy_error": [
        "Деплой упал... 😱 Кто-то будет дебажить!",
        "Ой-ой-ой! Что-то пошло не так! 🔥",
        "Провал! Но не паникуем. Паникуем? 😅",
        "Деплой failed. Время смотреть логи! 📜",
    ],
    "claude_start": [
        "Окей, сейчас разберусь... 🤔",
        "Принято! Погнали работать! 💪",
        "Задача получена, выполняю... 🚀",
        "Есть, босс! Уже делаю! 🤖",
    ],
    "claude_done": [
        "Готово! Я молодец? 😏",
        "Сделано! Чего ещё изволите? 🎩",
        "Выполнено! Следующая задача? 💪",
        "Всё, справился! 🏆",
    ],
    "claude_error": [
        "Упс, что-то пошло не так... 😅",
        "Хьюстон, у нас проблема! 🚨",
        "Не получилось, но я старался! 😬",
    ],
    # PM функции
    "pm_menu": [
        "PM Dashboard! Где мы сейчас и куда идём... 📊",
        "Время проверить статус проекта! 🎯",
        "Добро пожаловать в PM-панель! Тут всё серьёзно. Ну почти. 📋",
        "PM mode activated! Давай посмотрим что творится... 🔍",
    ],
    "pm_audit": [
        "Сейчас посмотрим, что там накопилось... 📋",
        "Аудит time! Кто тут без задач ходит? 🔍",
        "Проверяем беклог... Надеюсь, там не 100500 сторей! 😅",
        "Загружаю список дел... Держись крепче! 📝",
    ],
    "pm_report": [
        "Отчёт готов! Как на планёрке, только без кофе. ☕",
        "Вот что мы наработали! (или не наработали...) 📈",
        "Статистика подъехала! 📊",
        "Смотрим активность... Кто молодец, а кто — ну такое. 🤔",
    ],
    "pm_agent_busy": [
        "Агент трудится! Не мешай гению! 🤖💪",
        "Claude занят делом. В отличие от некоторых... 😏",
        "Работа кипит! Скоро будет результат! ⚙️",
    ],
    "pm_agent_idle": [
        "Агент скучает... Дай ему задачу! 😴",
        "Claude свободен и готов к подвигам! 🦸",
        "Никого нет дома... То есть агент свободен! 🏠",
    ],
}

# Dev jokes для команды /joke
DEV_JOKES = [
    "Почему программисты путают Хэллоуин и Рождество? Потому что Oct 31 = Dec 25 🎃🎄",
    "Есть только 10 типов людей: те кто понимают двоичный код и те кто нет.",
    "— Сколько программистов нужно, чтобы вкрутить лампочку?\n— Ни одного, это hardware проблема!",
    "Почему Java разработчик носит очки? Потому что не видит C# 😎",
    "localhost всегда рядом... только на него можно положиться 💔",
    "Мой код работает, и я не знаю почему. Мой код не работает, и я не знаю почему.",
    "git push --force: Потому что чужие коммиты - это чужие проблемы 🔥",
    "Production - это просто dev environment, который кто-то случайно задеплоил.",
    "99 багов в коде, 99 багов...\nПофикси один, собери...\n127 багов в коде! 🐛",
    "Заказчик: 'Добавьте простую кнопку'\nРазработчик: *плачет в REST API*",
    "Документация? Я думал, код самодокументирующийся! 📚",
    "Senior developer - это junior, который гуглит быстрее.",
    "QA: 'Нашёл баг'\nDev: 'Это фича'\nQA: 'Фича не работает'\nDev: '...'",
    "Код ревью: процесс, где ты узнаёшь, что всё неправильно, но никто не знает как правильно.",
    "Agile - это когда дедлайн каждые две недели, а не раз в год.",
]


def get_random_joke(category: str) -> str:
    """Возвращает случайную шутку из категории."""
    jokes = JOKES.get(category, JOKES["start"])
    return random.choice(jokes)


def get_random_dev_joke() -> str:
    """Возвращает случайный dev-анекдот."""
    return random.choice(DEV_JOKES)


# =============================================================================
# Message Formatters - Форматирование сообщений
# =============================================================================

def format_health_message(health_data: dict) -> str:
    """Форматирует сообщение о здоровье серверов."""
    staging_api = health_data["staging_api"]
    staging_fe = health_data["staging_fe"]
    prod_api = health_data["prod_api"]
    prod_fe = health_data["prod_fe"]
    k8s = health_data["k8s"]
    prod = health_data["prod"]

    def status_icon(s):
        return "✅" if s.get("status") == "UP" else "❌"

    def latency_str(s):
        return f" ({s.get('latency_ms', '?')}ms)" if s.get('latency_ms') else ""

    msg = f"""
<b>🏥 Статус серверов</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

<b>━━━ 🧪 STAGING (K3s) ━━━</b>
{status_icon(staging_api)} <b>API:</b> {staging_api.get('status')}{latency_str(staging_api)}
{status_icon(staging_fe)} <b>Frontend:</b> {staging_fe.get('status')}{latency_str(staging_fe)}
"""

    # K8s pods
    if k8s.get("pods"):
        msg += "\n<b>📦 Поды:</b>\n"
        for pod in k8s["pods"][:6]:
            icon = "🟢" if pod["status"] == "Running" else "🔴"
            restarts = f" (↻{pod['restarts']})" if pod['restarts'] != "0" else ""
            msg += f"  {icon} {pod['name'][:25]}{restarts}\n"

    # K8s node resources
    if k8s.get("node"):
        msg += f"\n<b>💻 Ресурсы ноды:</b>\n"
        msg += f"  CPU: {k8s['node'].get('cpu_percent', '?')} | RAM: {k8s['node'].get('memory_percent', '?')}\n"

    msg += f"""
<b>━━━ 🚀 PRODUCTION (YC) ━━━</b>
{status_icon(prod_api)} <b>API:</b> {prod_api.get('status')}{latency_str(prod_api)}
{status_icon(prod_fe)} <b>Frontend:</b> {prod_fe.get('status')}{latency_str(prod_fe)}
"""

    # Prod containers
    if prod.get("containers"):
        msg += "\n<b>🐳 Контейнеры:</b>\n"
        for c in prod["containers"][:6]:
            icon = "🟢" if c["status"] == "UP" else "🔴"
            msg += f"  {icon} {c['name']}\n"

    # Итоговый статус
    all_up = all(s.get("status") == "UP" for s in [staging_api, staging_fe, prod_api, prod_fe])
    if all_up:
        msg += "\n✨ <b>Все сервисы работают!</b>"
    else:
        msg += "\n⚠️ <b>Есть проблемы с сервисами!</b>"

    return msg.strip()


def format_load_test_stats(stats: dict, target: str, users: int, duration: int, elapsed: int) -> str:
    """Форматирует статистику нагрузочного теста."""
    target_name = "🧪 STAGING" if target == "staging" else "🚀 PRODUCTION"
    remaining = max(0, duration - elapsed)

    msg = f"""
<b>📊 Статистика нагрузочного теста</b>

<b>Конфигурация:</b>
📍 Цель: {target_name}
👥 Пользователей: {users}
⏱ Прошло: {elapsed // 60}м {elapsed % 60}с / {duration // 60}м

<b>Результаты:</b>
📨 Запросов: {stats.get('total_requests', 0):,}
❌ Ошибок: {stats.get('total_failures', 0):,}
⚡ RPS: {stats.get('current_rps', 0)}
📈 Avg: {stats.get('avg_response_time', 0)}ms
📉 Min: {stats.get('min_response_time', 0)}ms
📊 Max: {stats.get('max_response_time', 0)}ms
"""

    # Вердикт
    error_rate = 0
    if stats.get('total_requests', 0) > 0:
        error_rate = (stats.get('total_failures', 0) / stats.get('total_requests', 1)) * 100

    if error_rate < 1:
        msg += "\n✅ <b>Вердикт:</b> Отлично!"
    elif error_rate < 5:
        msg += "\n⚠️ <b>Вердикт:</b> Норм, но есть ошибки"
    else:
        msg += "\n❌ <b>Вердикт:</b> Много ошибок!"

    return msg.strip()


def format_e2e_report(stats: dict, duration_sec: int) -> str:
    """Форматирует отчёт E2E тестирования."""
    passed = stats.get("passed", 0)
    failed = stats.get("failed", 0)
    broken = stats.get("broken", 0)
    skipped = stats.get("skipped", 0)
    total = stats.get("total", 0)

    duration_min = duration_sec // 60
    duration_s = duration_sec % 60

    # Прогресс-бар
    if total > 0:
        pass_percent = (passed / total) * 100
        bar_filled = int(pass_percent / 10)
        bar_empty = 10 - bar_filled
        progress_bar = "🟩" * bar_filled + "🟥" * bar_empty
    else:
        progress_bar = "⬜" * 10
        pass_percent = 0

    all_passed = failed == 0 and broken == 0
    status_emoji = "✅" if all_passed else "❌"
    verdict = "ВСЁ ЗЕЛЁНОЕ!" if all_passed else "ЕСТЬ ПРОБЛЕМЫ!"

    msg = f"""
<b>🧪 ОТЧЁТ E2E ТЕСТИРОВАНИЯ</b>
<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>

<b>━━━ Результат ━━━</b>
{status_emoji} <b>{verdict}</b>

{progress_bar} {pass_percent:.0f}%

<b>📊 Статистика:</b>
✅ Passed: <b>{passed}</b>
❌ Failed: <b>{failed}</b>
💔 Broken: <b>{broken}</b>
⏭ Skipped: <b>{skipped}</b>
📋 Total: <b>{total}</b>

⏱ <b>Время:</b> {duration_min}м {duration_s}с
"""

    return msg.strip()


# Webhook event emojis
WEBHOOK_EMOJIS = {
    "push": "📦",
    "merge_request": "🔀",
    "pipeline": "⚙️",
    "build": "🔨",
    "deploy": "🚀",
    "success": "✅",
    "failed": "❌",
    "running": "🔄",
    "pending": "⏳",
}


# =============================================================================
# GitLab Webhook Formatters
# =============================================================================

def get_status_emoji(status: str) -> str:
    """Возвращает emoji для статуса."""
    status_map = {
        "success": "✅",
        "failed": "❌",
        "canceled": "🚫",
        "running": "🔄",
        "pending": "⏳",
        "created": "🆕",
        "skipped": "⏭",
        "manual": "👆",
    }
    return status_map.get(status.lower(), "❓")


def get_humor_for_status(status: str, event_type: str) -> str:
    """Возвращает юморную фразу в зависимости от статуса."""
    if status == "success":
        jokes = [
            "Ура! Всё взлетело! 🎉",
            "Зелёненькое! Чудеса случаются! ✨",
            "Работает! Даже странно... 🤔",
            "Успех! Иди налей себе кофе, заслужил! ☕",
        ]
    elif status == "failed":
        jokes = [
            "Упс... Кто-то накосячил! 🙈",
            "ПРОВАЛ! Время смотреть логи... 📜",
            "Красненькое! Классика пятничного деплоя! 🔥",
            "Failed! Но мы не сдаёмся, правда? 💪",
        ]
    elif status == "running":
        jokes = [
            "Поехали! Держитесь! 🚀",
            "Крутим, мутим... ⚙️",
            "В процессе... Пойду кофе попью. ☕",
            "Работаем-работаем! 🔧",
        ]
    elif status == "pending":
        jokes = [
            "Ждём своей очереди... ⏳",
            "В очереди, как в поликлинике. 😴",
            "Pending... Жизнь проходит мимо. ⌛",
        ]
    else:
        jokes = ["Что-то происходит... 🤷"]

    return random.choice(jokes)


def format_pipeline_message(data: dict) -> str:
    """
    Форматирует компактное сообщение о pipeline событии.

    Редизайн WH-120: более компактный и информативный формат.

    Args:
        data: Webhook payload от GitLab
    """
    status = data.get("object_attributes", {}).get("status", "unknown")
    emoji = get_status_emoji(status)

    pipeline = data.get("object_attributes", {})
    project = data.get("project", {})
    user = data.get("user", {})

    project_name = project.get("name", "Unknown")
    ref = pipeline.get("ref", "unknown")
    pipeline_url = pipeline.get("url", "")
    username = user.get("name", "Ghost")

    # Длительность (только для завершённых)
    duration = pipeline.get("duration")
    duration_str = ""
    if duration and status in ["success", "failed", "canceled"]:
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f" • {minutes}м {seconds}с"

    # Компактный статус-бар
    status_text = {
        "success": "PASSED",
        "failed": "FAILED",
        "running": "RUNNING",
        "pending": "PENDING",
        "canceled": "CANCELED"
    }.get(status, status.upper())

    # Краткий формат для running - одна строка
    if status == "running":
        return f"{emoji} <b>{project_name}</b> • <code>{ref}</code> • {username}\n<i>Pipeline запущен...</i>"

    # Для завершённых - полный формат
    humor = get_humor_for_status(status, "pipeline")

    msg = f"""{emoji} <b>{status_text}</b>{duration_str}

<b>{project_name}</b> • <code>{ref}</code>
👤 {username}

{humor}

<a href="{pipeline_url}">→ GitLab</a>"""

    return msg.strip()


def format_job_message(data: dict) -> str:
    """
    Форматирует компактное сообщение о job событии.

    Редизайн WH-120: более компактный формат.
    - Для running: не отправляем (слишком много шума)
    - Для success: только если это deploy job
    - Для failed: полная информация

    Args:
        data: Webhook payload от GitLab
    """
    status = data.get("build_status", "unknown")
    emoji = get_status_emoji(status)

    project = data.get("project_name", "Unknown")
    ref = data.get("ref", "unknown")
    job_name = data.get("build_name", "unknown-job")
    stage = data.get("build_stage", "?")
    username = data.get("user", {}).get("name", "Ghost") if isinstance(data.get("user"), dict) else "Ghost"

    # Длительность (только для завершённых)
    duration = data.get("build_duration")
    duration_str = ""
    if duration and status in ["success", "failed"]:
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f" • {minutes}м {seconds}с"

    # Для running - минимальный формат
    if status == "running":
        return f"{emoji} <code>{job_name}</code> • {stage}\n<i>Выполняется...</i>"

    # Для success
    if status == "success":
        return f"{emoji} <b>{job_name}</b>{duration_str}\n<code>{ref}</code> • {stage}"

    # Для failed - полный формат
    humor = get_humor_for_status(status, "job")

    msg = f"""{emoji} <b>FAILED: {job_name}</b>{duration_str}

<b>{project}</b> • <code>{ref}</code>
🏗 Stage: {stage}
👤 {username}

{humor}"""

    return msg.strip()


def format_job_failed_with_log(data: dict, log: str) -> str:
    """
    Форматирует сообщение о падении job с логом.

    Редизайн WH-120: компактный лог.

    Args:
        data: Webhook payload от GitLab
        log: Последние строки лога
    """
    basic_msg = format_job_message(data)

    # Добавляем лог (ограничиваем и очищаем ANSI коды)
    import re
    clean_log = re.sub(r'\x1b\[[0-9;]*m', '', log)  # Убираем ANSI escape коды
    log_preview = clean_log[-600:] if len(clean_log) > 600 else clean_log  # Последние 600 символов

    msg = f"""{basic_msg}

<pre>{log_preview.strip()}</pre>"""

    return msg.strip()


# =============================================================================
# Robot Formatters
# =============================================================================

ROBOT_JOKES = {
    "started": [
        "Робот поехал! Держите кофе! ☕",
        "Сценарий запущен! Скоро склад оживёт! 🏭",
        "Поехали! Робот на работе! 🤖",
        "Запуск! Товары начинают двигаться! 📦",
    ],
    "stopped": [
        "Робот остановлен. Передохнёт! 😴",
        "Стоп машина! 🛑",
        "Перерыв на обслуживание! 🔧",
    ],
    "error": [
        "Упс! Что-то пошло не так! 🙈",
        "Робот споткнулся... 🤖💥",
        "Ошибочка вышла! 😅",
    ],
}


def format_robot_menu(status: dict) -> str:
    """Форматирует главное меню робота."""
    state = status.get("state", "unknown")
    current_scenario = status.get("current_scenario")

    state_emoji = {
        "idle": "😴",
        "running": "🏃",
        "stopping": "🛑",
        "error": "❌",
    }

    state_text = {
        "idle": "Ожидание",
        "running": "Работает",
        "stopping": "Останавливается",
        "error": "Ошибка",
    }

    emoji = state_emoji.get(state, "❓")
    text = state_text.get(state, state)

    msg = f"""🤖 *Warehouse Robot*

{emoji} *Статус:* {text}
"""

    if current_scenario:
        scenario_names = {
            "receiving": "📦 Приёмка",
            "shipping": "🚚 Отгрузка",
            "inventory": "📋 Инвентаризация",
            "все сценарии": "🎲 Все сценарии",
        }
        msg += f"🎬 *Сценарий:* {scenario_names.get(current_scenario, current_scenario)}\n"

    if status.get("last_scenario"):
        msg += f"\n📜 *Последний:* {status.get('last_scenario')}"

    return msg.strip()


def format_robot_status(status: dict, health: dict) -> str:
    """Форматирует детальный статус робота."""
    state = status.get("state", "unknown")
    api_available = health.get("api_available", False)

    msg = f"""🤖 *Статус Warehouse Robot*

*Робот:*
• Состояние: {state}
• Текущий сценарий: {status.get('current_scenario', '-')}
• Uptime: {status.get('uptime_seconds', 0):.0f}с

*Warehouse API:*
• Доступен: {'✅ Да' if api_available else '❌ Нет'}
"""
    return msg.strip()


def format_robot_stats(stats: dict) -> str:
    """Форматирует статистику робота."""
    total = stats.get("total_runs", 0)
    success = stats.get("successful_runs", 0)
    failed = stats.get("failed_runs", 0)
    last_run = stats.get("last_run", "-")
    last_scenario = stats.get("last_scenario", "-")

    # Последний результат
    last_result = stats.get("last_result", {})
    result_details = ""

    if last_result:
        scenario = last_result.get("scenario", "")
        if scenario == "receiving":
            result_details = f"""
📦 *Последняя приёмка:*
• Создано товаров: {last_result.get('products_created', 0)}
• Всего единиц: {last_result.get('total_quantity', 0):,}
• На сумму: {format_money(last_result.get('total_value', 0))}
"""
        elif scenario == "shipping":
            result_details = f"""
🚚 *Последняя отгрузка:*
• Позиций: {last_result.get('positions', 0)}
• Отгружено: {last_result.get('total_shipped', 0):,} ед.
• На сумму: {format_money(last_result.get('total_value', 0))}
"""
        elif scenario == "inventory":
            result_details = f"""
📋 *Последняя инвентаризация:*
• Корректировок: {last_result.get('adjusted', 0)}
• Излишки: {last_result.get('surplus_count', 0)}
• Недостачи: {last_result.get('shortage_count', 0)}
• Списано: {last_result.get('deleted', 0)}
"""

    msg = f"""📊 *Статистика Warehouse Robot*

*Общая статистика:*
• Всего запусков: {total}
• Успешных: ✅ {success}
• С ошибками: ❌ {failed}

*Последний запуск:*
• Сценарий: {last_scenario}
• Время: {last_run}
{result_details}
"""
    return msg.strip()


def format_robot_started(scenario: str, speed: str, environment: str = "staging", duration: int = 0) -> str:
    """Форматирует сообщение о запуске сценария."""
    import random

    scenario_names = {
        "receiving": "📦 Приёмка товара",
        "shipping": "🚚 Отгрузка",
        "inventory": "📋 Инвентаризация",
        "all": "🎲 Все сценарии (случайный порядок)",
    }

    speed_names = {
        "slow": "🐢 Медленно (пауза 15с)",
        "normal": "🚶 Нормально (пауза 5с)",
        "fast": "🚀 Быстро (пауза 1с)",
    }

    env_names = {
        "staging": "🔧 STAGING (тест)",
        "prod": "🚀 PROD (боевой)",
    }

    duration_names = {
        0: "один раз",
        5: "5 минут",
        30: "30 минут",
        60: "1 час",
    }

    joke = random.choice(ROBOT_JOKES["started"])

    duration_text = duration_names.get(duration, f"{duration} мин")

    return f"""✅ *Сценарий запущен!*

🎬 *Сценарий:* {scenario_names.get(scenario, scenario)}
⏱ *Продолжительность:* {duration_text}
🌍 *Окружение:* {env_names.get(environment, environment)}
⚡ *Скорость:* {speed_names.get(speed, speed)}

{joke}
"""


def format_robot_stopped() -> str:
    """Форматирует сообщение об остановке робота."""
    import random
    joke = random.choice(ROBOT_JOKES["stopped"])
    return f"🛑 *Робот останавливается...*\n\n{joke}"


def format_robot_error(error: str) -> str:
    """Форматирует сообщение об ошибке."""
    import random
    joke = random.choice(ROBOT_JOKES["error"])
    return f"❌ *Ошибка:* {error}\n\n{joke}"


def format_robot_notification(scenario: str, result: dict) -> str:
    """
    Форматирует уведомление о завершении сценария.

    Показывает детали по каждому товару:
    - Приёмка: список добавленных товаров с количеством и суммой
    - Отгрузка: список отгруженных товаров с количеством и остатком
    - Инвентаризация: список корректировок и списаний
    """
    scenario_names = {
        "receiving": "📦 Приёмка",
        "shipping": "🚚 Отгрузка",
        "inventory": "📋 Инвентаризация",
    }

    emoji = "✅" if not result.get("error") else "❌"

    msg = f"""{emoji} *{scenario_names.get(scenario, scenario)} завершена*

"""

    if scenario == "receiving":
        products = result.get("products", [])
        if products:
            msg += "*Добавленные товары:*\n"
            for p in products:
                name = p.get("name", "Товар")
                qty = p.get("quantity", 0)
                price = p.get("price", 0)
                total = qty * price
                msg += f"  • {name}: {qty} шт. × {format_money(price).replace(' ₽', '')} = {format_money(total)}\n"
            msg += "\n"

        msg += f"""*Итого:*
• Создано товаров: {result.get('products_created', 0)}
• Всего единиц: {result.get('total_quantity', 0):,}
• На сумму: {format_money(result.get('total_value', 0))}"""

    elif scenario == "shipping":
        details = result.get("details", [])
        if details:
            msg += "*Отгруженные товары:*\n"
            for d in details:
                name = d.get("product_name", "Товар")
                shipped = d.get("shipped_qty", 0)
                remaining = d.get("remaining_qty", 0)
                price = d.get("unit_price", 0)
                total = shipped * price
                msg += f"  • {name}: -{shipped} шт. (остаток: {remaining}) = {format_money(total)}\n"
            msg += "\n"

        msg += f"""*Итого:*
• Позиций: {result.get('positions', 0)}
• Отгружено: {result.get('total_shipped', 0):,} ед.
• На сумму: {format_money(result.get('total_value', 0))}"""

    elif scenario == "inventory":
        adjustments = result.get("adjustments", [])
        deleted_products = result.get("deleted_products", [])

        if adjustments:
            msg += "*Корректировки:*\n"
            for a in adjustments:
                name = a.get("product_name", "Товар")
                was = a.get("was", 0)
                now = a.get("now", 0)
                diff = a.get("diff", 0)
                sign = "+" if diff > 0 else ""
                emoji_adj = "📈" if diff > 0 else "📉"
                msg += f"  {emoji_adj} {name}: {was} → {now} ({sign}{diff})\n"
            msg += "\n"

        if deleted_products:
            msg += "*Списано:*\n"
            for name in deleted_products:
                msg += f"  🗑️ {name}\n"
            msg += "\n"

        msg += f"""*Итого:*
• Корректировок: {result.get('adjusted', 0)}
• Излишки: {result.get('surplus_count', 0)}, недостачи: {result.get('shortage_count', 0)}
• Списано: {result.get('deleted', 0)}"""

    return msg.strip()
