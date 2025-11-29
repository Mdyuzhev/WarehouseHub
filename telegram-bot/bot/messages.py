"""
Сообщения и юмор бота.
Все шутки, форматирование и мемы живут здесь! 🎭
"""

import random
from datetime import datetime

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
    Форматирует сообщение о pipeline событии.

    Args:
        data: Webhook payload от GitLab
    """
    status = data.get("object_attributes", {}).get("status", "unknown")
    emoji = get_status_emoji(status)
    humor = get_humor_for_status(status, "pipeline")

    pipeline = data.get("object_attributes", {})
    project = data.get("project", {})
    user = data.get("user", {})

    project_name = project.get("name", "Unknown")
    ref = pipeline.get("ref", "unknown")
    pipeline_id = pipeline.get("id", "?")
    pipeline_url = pipeline.get("url", "")
    username = user.get("name", "Ghost")

    # Длительность
    duration = pipeline.get("duration")
    duration_str = ""
    if duration:
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f"\n⏱ Время: {minutes}м {seconds}с"

    msg = f"""
{emoji} <b>Pipeline {status.upper()}</b>

📦 <b>Проект:</b> {project_name}
🌿 <b>Ветка:</b> {ref}
🆔 <b>Pipeline:</b> #{pipeline_id}
👤 <b>Автор:</b> {username}{duration_str}

{humor}

<a href="{pipeline_url}">🔗 Открыть в GitLab</a>
"""
    return msg.strip()


def format_job_message(data: dict) -> str:
    """
    Форматирует сообщение о job событии.

    Args:
        data: Webhook payload от GitLab
    """
    status = data.get("build_status", "unknown")
    emoji = get_status_emoji(status)

    build = data
    project = data.get("project_name", "Unknown")
    ref = data.get("ref", "unknown")
    job_name = data.get("build_name", "unknown-job")
    job_id = data.get("build_id", "?")
    stage = data.get("build_stage", "?")
    username = data.get("user", {}).get("name", "Ghost") if isinstance(data.get("user"), dict) else "Ghost"

    # Длительность
    duration = data.get("build_duration")
    duration_str = ""
    if duration:
        minutes = int(duration) // 60
        seconds = int(duration) % 60
        duration_str = f"\n⏱ Время: {minutes}м {seconds}с"

    # Для running показываем другой текст
    if status == "running":
        humor = get_humor_for_status(status, "job")
        msg = f"""
{emoji} <b>Job Started: {job_name}</b>

📦 <b>Проект:</b> {project}
🌿 <b>Ветка:</b> {ref}
🏗 <b>Stage:</b> {stage}
🆔 <b>Job ID:</b> #{job_id}
👤 <b>Автор:</b> {username}

{humor}
"""
        return msg.strip()

    # Для завершённых jobs
    humor = get_humor_for_status(status, "job")

    msg = f"""
{emoji} <b>Job {status.upper()}: {job_name}</b>

📦 <b>Проект:</b> {project}
🌿 <b>Ветка:</b> {ref}
🏗 <b>Stage:</b> {stage}
🆔 <b>Job ID:</b> #{job_id}
👤 <b>Автор:</b> {username}{duration_str}

{humor}
"""

    return msg.strip()


def format_job_failed_with_log(data: dict, log: str) -> str:
    """
    Форматирует сообщение о падении job с логом.

    Args:
        data: Webhook payload от GitLab
        log: Последние строки лога
    """
    basic_msg = format_job_message(data)

    # Добавляем лог
    log_preview = log[:800] if len(log) > 800 else log  # Ограничиваем размер
    msg = f"""
{basic_msg}

<b>📜 Лог (последние строки):</b>
<code>{log_preview}</code>

<i>Время дебажить! 🔍</i>
"""
    return msg.strip()
