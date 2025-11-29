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

    return templates.TemplateResponse("index.html", {
        "request": request,
        "services": services,
        "operations": operations,
        "sessions": sessions,
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
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


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
