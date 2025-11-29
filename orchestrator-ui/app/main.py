"""
🎮 WAREHOUSE ORCHESTRATOR UI - 8-BIT EDITION
Главный файл приложения

Запуск: uvicorn app.main:app --reload --port 8088
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import json
from datetime import datetime
from pathlib import Path

from .database import init_db, get_recent_operations, get_all_sessions
from .services import (
    get_all_services_status,
    deploy_service,
    run_tests,
    get_logs,
    restart_service,
    stream_script,
    get_random_message
)
from .agent import agent_service
from .gitlab import gitlab_service
from .config import GITLAB_JOBS

# Пути
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup и shutdown события"""
    # Startup
    await init_db()
    print("""
    ╔═══════════════════════════════════════════════╗
    ║  🎮 WAREHOUSE ORCHESTRATOR UI                 ║
    ║  ─────────────────────────────────────────── ║
    ║  8-bit edition is ready!                     ║
    ║  Press START to begin...                     ║
    ║                                              ║
    ║  http://localhost:8000                       ║
    ╚═══════════════════════════════════════════════╝
    """)
    yield
    # Shutdown
    print("👋 Game Over! See you next time!")


app = FastAPI(
    title="Warehouse Orchestrator UI",
    description="8-bit консоль управления складом 🎮",
    version="1.0.0",
    lifespan=lifespan
)

# Статика и шаблоны
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# ═══════════════════════════════════════════════════════════
# PAGES - Страницы
# ═══════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница - 8-битная консоль управления"""
    services = await get_all_services_status()
    operations = await get_recent_operations(5)
    sessions = await get_all_sessions(5)
    jobs = gitlab_service.get_available_jobs(4)
    jobs_status = await gitlab_service.get_all_jobs_status(4)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services,
        "operations": operations,
        "sessions": sessions,
        "jobs": jobs,
        "jobs_status": {j["name"]: j for j in jobs_status},
        "current_time": datetime.now().strftime("%H:%M:%S")
    })


@app.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    """Страница уведомлений - fullscreen live view"""
    return templates.TemplateResponse("notifications.html", {
        "request": request,
        "current_time": datetime.now().strftime("%H:%M:%S")
    })


# ═══════════════════════════════════════════════════════════
# API - Эндпоинты для HTMX
# ═══════════════════════════════════════════════════════════

@app.get("/api/status")
async def api_status():
    """Получить статус всех сервисов"""
    return await get_all_services_status()


@app.post("/api/deploy/{service}")
async def api_deploy(service: str, environment: str = "staging"):
    """Деплой сервиса"""
    return await deploy_service(service, environment)


@app.post("/api/tests/{test_type}")
async def api_tests(test_type: str = "e2e"):
    """Запуск тестов"""
    return await run_tests(test_type)


@app.get("/api/logs/{service}")
async def api_logs(service: str, lines: int = 100):
    """Получить логи сервиса"""
    logs = await get_logs(service, lines)
    return {"logs": logs}


@app.post("/api/restart/{service}")
async def api_restart(service: str):
    """Рестарт сервиса"""
    return await restart_service(service)


@app.get("/api/operations")
async def api_operations(limit: int = 10):
    """История операций"""
    return await get_recent_operations(limit)


# ═══════════════════════════════════════════════════════════
# GITLAB API - Запуск джоб
# ═══════════════════════════════════════════════════════════

@app.get("/api/gitlab/jobs")
async def api_gitlab_jobs(project_id: int = 4):
    """Получить список доступных джоб"""
    jobs = gitlab_service.get_available_jobs(project_id)
    status = await gitlab_service.get_all_jobs_status(project_id)
    return {"jobs": jobs, "status": {j["name"]: j for j in status}}


@app.get("/api/gitlab/jobs/status")
async def api_gitlab_jobs_status(project_id: int = 4):
    """Получить статус всех джоб"""
    status = await gitlab_service.get_all_jobs_status(project_id)
    return {"status": {j["name"]: j for j in status}}


@app.post("/api/gitlab/jobs/{job_name}/run")
async def api_gitlab_run_job(job_name: str, project_id: int = 4):
    """Запустить джобу по имени"""
    result = await gitlab_service.run_job_by_name(project_id, job_name)

    # Уведомляем всех подключённых клиентов
    if result.get("success"):
        await notifications_manager.broadcast({
            "type": "job_started",
            "job_name": job_name,
            "job_id": result.get("job_id"),
            "message": result.get("message"),
            "timestamp": datetime.now().isoformat()
        })

    return result


@app.get("/api/gitlab/jobs/{job_id}/log")
async def api_gitlab_job_log(job_id: int, project_id: int = 4, tail: int = 50):
    """Получить логи джобы"""
    log = await gitlab_service.get_job_log(project_id, job_id, tail)
    return {"log": log}


@app.get("/api/gitlab/jobs/{job_id}/status")
async def api_gitlab_job_status(job_id: int, project_id: int = 4):
    """Получить статус конкретной джобы"""
    status = await gitlab_service.get_job_status(project_id, job_id)
    return status


# ═══════════════════════════════════════════════════════════
# AGENT API - Чат с агентом
# ═══════════════════════════════════════════════════════════

@app.post("/api/agent/chat")
async def api_agent_chat(request: Request):
    """Отправить сообщение агенту"""
    data = await request.json()
    message = data.get("message", "")

    if not message:
        return {"error": "Сообщение пустое! Напиши что-нибудь 🎮"}

    response = await agent_service.chat(message)
    return {"response": response}


@app.get("/api/agent/history")
async def api_agent_history(limit: int = 50):
    """История чата с агентом"""
    history = await agent_service.get_history(limit)
    return {"messages": history}


@app.post("/api/agent/analyze-logs")
async def api_agent_analyze(request: Request):
    """Попросить агента проанализировать логи"""
    data = await request.json()
    service = data.get("service", "api")

    # Получаем логи
    logs = await get_logs(service, 200)

    # Анализируем
    analysis = await agent_service.analyze_logs(logs)
    return {"analysis": analysis, "logs": logs}


# ═══════════════════════════════════════════════════════════
# HTMX PARTIALS - Частичные обновления страницы
# ═══════════════════════════════════════════════════════════

@app.get("/partials/services", response_class=HTMLResponse)
async def partial_services(request: Request):
    """Обновить карточки сервисов"""
    services = await get_all_services_status()
    return templates.TemplateResponse("partials/services.html", {
        "request": request,
        "services": services
    })


@app.get("/partials/terminal", response_class=HTMLResponse)
async def partial_terminal(request: Request, operation: str = None):
    """Обновить терминал"""
    operations = await get_recent_operations(10)
    return templates.TemplateResponse("partials/terminal.html", {
        "request": request,
        "operations": operations
    })


# ═══════════════════════════════════════════════════════════
# WEBSOCKET - Для live вывода логов
# ═══════════════════════════════════════════════════════════

class ConnectionManager:
    """Менеджер WebSocket соединений"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message):
        """Отправить сообщение всем подключённым"""
        if isinstance(message, dict):
            message = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()
notifications_manager = ConnectionManager()  # Отдельный для уведомлений


@app.websocket("/ws/terminal")
async def websocket_terminal(websocket: WebSocket):
    """WebSocket для live терминала"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")
            params = message.get("params", {})

            if action == "deploy":
                service = params.get("service", "all")
                env = params.get("environment", "staging")
                await websocket.send_text(f"🚀 {get_random_message('deploy_start')}")
                async for line in stream_script(f"deploy-{service}.sh", env):
                    await websocket.send_text(line)

            elif action == "tests":
                test_type = params.get("type", "e2e")
                await websocket.send_text(f"🧪 {get_random_message('tests_start')}")
                async for line in stream_script(f"run-{test_type}-tests.sh"):
                    await websocket.send_text(line)

            elif action == "logs":
                service = params.get("service", "api")
                logs = await get_logs(service, params.get("lines", 50))
                await websocket.send_text(logs)

    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/agent")
async def websocket_agent(websocket: WebSocket):
    """WebSocket для чата с агентом"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            user_msg = message.get("message", "")
            if user_msg:
                # Отправляем "печатает..."
                await websocket.send_json({"type": "typing"})

                # Получаем ответ
                response = await agent_service.chat(user_msg)

                # Отправляем ответ
                await websocket.send_json({
                    "type": "response",
                    "message": response
                })

    except WebSocketDisconnect:
        pass


# ═══════════════════════════════════════════════════════════
# WEBSOCKET - Для уведомлений о джобах
# ═══════════════════════════════════════════════════════════

@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    """WebSocket для получения уведомлений о статусе джоб"""
    await notifications_manager.connect(websocket)
    try:
        # Отправляем приветствие
        await websocket.send_json({
            "type": "connected",
            "message": "🎮 Подключено к уведомлениям!",
            "timestamp": datetime.now().isoformat()
        })

        while True:
            # Просто держим соединение открытым
            data = await websocket.receive_text()
            # Можно обрабатывать команды от клиента если нужно

    except WebSocketDisconnect:
        notifications_manager.disconnect(websocket)


# ═══════════════════════════════════════════════════════════
# WEBHOOK - Получение событий от GitLab
# ═══════════════════════════════════════════════════════════

@app.post("/webhook/gitlab")
async def gitlab_webhook(request: Request):
    """
    Webhook для получения событий от GitLab.
    Принимает Pipeline и Job события и рассылает их через WebSocket.
    """
    try:
        data = await request.json()
        event_type = data.get("object_kind", "unknown")

        notification = None

        if event_type == "pipeline":
            status = data.get("object_attributes", {}).get("status")
            pipeline_id = data.get("object_attributes", {}).get("id")
            project_name = data.get("project", {}).get("name", "unknown")

            emoji = {"success": "✅", "failed": "❌", "running": "🔄", "pending": "⏳"}.get(status, "❓")

            notification = {
                "type": "pipeline",
                "status": status,
                "pipeline_id": pipeline_id,
                "project": project_name,
                "message": f"{emoji} Pipeline #{pipeline_id} ({project_name}): {status}",
                "timestamp": datetime.now().isoformat()
            }

        elif event_type == "build":  # Job события
            status = data.get("build_status")
            job_name = data.get("build_name")
            job_id = data.get("build_id")
            project_name = data.get("project_name", "unknown")
            duration = data.get("build_duration")

            emoji = {"success": "✅", "failed": "❌", "running": "🔄", "pending": "⏳", "created": "📝"}.get(status, "❓")

            message = f"{emoji} Job '{job_name}' ({project_name}): {status}"
            if duration:
                message += f" ({int(duration)}s)"

            notification = {
                "type": "job",
                "status": status,
                "job_name": job_name,
                "job_id": job_id,
                "project": project_name,
                "duration": duration,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }

            # Если джоба упала - добавляем логи
            if status == "failed":
                try:
                    log = await gitlab_service.get_job_log(4, job_id, tail=20)
                    notification["log"] = log
                except Exception:
                    pass

        if notification:
            await notifications_manager.broadcast(notification)

        return {"status": "ok", "event": event_type}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ═══════════════════════════════════════════════════════════
# HEALTH CHECK
# ═══════════════════════════════════════════════════════════

@app.get("/health")
async def health():
    """Health check для самого UI"""
    return {
        "status": "ok",
        "message": "8-bit console is alive! 🎮",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
