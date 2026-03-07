"""
Robot API — FastAPI приложение для управления роботом-симулятором.

Endpoints:
- GET / — информация о сервисе
- GET /health — health check
- POST /start — запуск сценария
- POST /schedule — запуск по расписанию
- POST /stop — остановка робота
- GET /status — текущий статус
- GET /stats — статистика выполнения
- GET /scheduled — список запланированных задач
- DELETE /scheduled/{task_id} — отмена запланированной задачи
"""
import asyncio
import logging
import random
import threading
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from api_client import WarehouseAPIClient
from config import settings, get_api_url
from scenarios import SCENARIOS


class Environment(str, Enum):
    """Окружение для выполнения сценария."""
    HOME = "home"
    PROD = "prod"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI приложение
app = FastAPI(
    title="Warehouse Robot API",
    description="API для управления роботом-симулятором складских операций",
    version="1.0.0",
)


class RobotState(str, Enum):
    """Состояния робота."""
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ScenarioSpeed(str, Enum):
    """Скорость выполнения сценария."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


# Глобальное состояние робота
class RobotContext:
    """Контекст робота с thread-safe доступом."""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = RobotState.IDLE
        self._current_scenario: Optional[str] = None
        self._current_task: Optional[threading.Thread] = None
        self._stop_requested = False
        self._stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "last_run": None,
            "last_scenario": None,
            "last_result": None,
            "history": [],
        }
        self._start_time: Optional[datetime] = None

    @property
    def state(self) -> RobotState:
        with self._lock:
            return self._state

    @state.setter
    def state(self, value: RobotState):
        with self._lock:
            self._state = value

    @property
    def stop_requested(self) -> bool:
        with self._lock:
            return self._stop_requested

    @stop_requested.setter
    def stop_requested(self, value: bool):
        with self._lock:
            self._stop_requested = value

    def get_status(self) -> Dict[str, Any]:
        """Получить текущий статус робота."""
        with self._lock:
            uptime = None
            if self._start_time:
                uptime = (datetime.now() - self._start_time).total_seconds()

            return {
                "state": self._state.value,
                "current_scenario": self._current_scenario,
                "stop_requested": self._stop_requested,
                "uptime_seconds": uptime,
                "last_run": self._stats["last_run"],
                "last_scenario": self._stats["last_scenario"],
            }

    def get_stats(self) -> Dict[str, Any]:
        """Получить статистику выполнения."""
        with self._lock:
            return {
                **self._stats,
                "current_state": self._state.value,
            }

    def start_run(self, scenario_name: str):
        """Начать выполнение сценария."""
        with self._lock:
            self._state = RobotState.RUNNING
            self._current_scenario = scenario_name
            self._stop_requested = False
            self._start_time = datetime.now()

    def finish_run(self, success: bool, result: Optional[Dict[str, Any]] = None):
        """Завершить выполнение сценария."""
        with self._lock:
            self._stats["total_runs"] += 1
            if success:
                self._stats["successful_runs"] += 1
            else:
                self._stats["failed_runs"] += 1

            self._stats["last_run"] = datetime.now().isoformat()
            self._stats["last_scenario"] = self._current_scenario
            self._stats["last_result"] = result

            # Сохраняем в историю (последние 20 записей)
            history_entry = {
                "scenario": self._current_scenario,
                "timestamp": self._stats["last_run"],
                "success": success,
                "result": result,
            }
            self._stats["history"].insert(0, history_entry)
            self._stats["history"] = self._stats["history"][:20]

            self._state = RobotState.IDLE
            self._current_scenario = None
            self._start_time = None


# Создаём глобальный контекст
robot = RobotContext()

# Хранилище запланированных задач
scheduled_tasks: Dict[str, Dict[str, Any]] = {}
scheduled_timers: Dict[str, threading.Timer] = {}


# Pydantic модели
class StartRequest(BaseModel):
    """Запрос на запуск сценария."""
    scenario: str = Field(
        ...,
        description="Название сценария: receiving, shipping, inventory, all",
        examples=["receiving", "shipping", "inventory", "all"],
    )
    speed: ScenarioSpeed = Field(
        default=ScenarioSpeed.NORMAL,
        description="Скорость выполнения (slow=15с, normal=5с, fast=1с пауза)",
    )
    environment: Environment = Field(
        default=Environment.HOME,
        description="Окружение: home или prod",
    )
    duration: int = Field(
        default=0,
        description="Продолжительность повторения в минутах (0 = один раз)",
        ge=0,
        le=120,
    )


class StartResponse(BaseModel):
    """Ответ на запуск сценария."""
    status: str
    message: str
    scenario: str


class ScheduleRequest(BaseModel):
    """Запрос на запуск по расписанию."""
    scenario: str = Field(
        ...,
        description="Название сценария: receiving, shipping, inventory",
        examples=["receiving", "shipping", "inventory"],
    )
    speed: ScenarioSpeed = Field(
        default=ScenarioSpeed.NORMAL,
        description="Скорость выполнения",
    )
    environment: Environment = Field(
        default=Environment.HOME,
        description="Окружение: home или prod",
    )
    scheduled_time: str = Field(
        ...,
        description="Время запуска в формате HH:MM или ISO datetime",
        examples=["14:30", "2025-12-01T14:30:00"],
    )


class ScheduleResponse(BaseModel):
    """Ответ на запрос расписания."""
    status: str
    message: str
    task_id: str
    scenario: str
    scheduled_time: str
    seconds_until_start: float


class ScheduledTaskInfo(BaseModel):
    """Информация о запланированной задаче."""
    task_id: str
    scenario: str
    speed: str
    environment: str
    scheduled_time: str
    created_at: str
    seconds_until_start: float


class StatusResponse(BaseModel):
    """Ответ на запрос статуса."""
    state: str
    current_scenario: Optional[str]
    stop_requested: bool
    uptime_seconds: Optional[float]
    last_run: Optional[str]
    last_scenario: Optional[str]


class StopResponse(BaseModel):
    """Ответ на запрос остановки."""
    status: str
    message: str


class HealthResponse(BaseModel):
    """Ответ health check."""
    status: str
    api_available: bool
    robot_state: str


class InfoResponse(BaseModel):
    """Информация о сервисе."""
    name: str
    version: str
    description: str
    available_scenarios: List[str]
    api_url: str


def get_pause_seconds(speed: str) -> int:
    """
    Получить паузу между повторениями в секундах.

    - slow: 15 секунд
    - normal: 5 секунд
    - fast: 1 секунда
    """
    return {"slow": 15, "normal": 5, "fast": 1}.get(speed, 5)


def run_scenario_task(scenario_name: str, speed: str, environment: str = "home", duration: int = 0):
    """
    Выполнение сценария в фоновом потоке.

    Args:
        scenario_name: Название сценария (или "all" для всех сценариев)
        speed: Скорость выполнения (slow=15с, normal=5с, fast=1с пауза)
        environment: Окружение (home или prod)
        duration: Продолжительность повторения в минутах (0 = один раз)
    """
    # Для "all" запускаем все сценарии по очереди
    if scenario_name == "all":
        run_all_scenarios_task(speed, environment, duration)
        return

    api_url = get_api_url(environment)
    pause_seconds = get_pause_seconds(speed)

    if duration > 0:
        logger.info(f"🤖 Запуск сценария: {scenario_name} (duration={duration}мин, pause={pause_seconds}с, env={environment}, url={api_url})")
    else:
        logger.info(f"🤖 Запуск сценария: {scenario_name} (однократно, speed={speed}, env={environment}, url={api_url})")

    start_time = time.time()
    end_time = start_time + (duration * 60) if duration > 0 else start_time + 1  # +1с для однократного
    iteration = 0
    all_results = []

    try:
        # Создаём клиент API с URL для выбранного окружения
        with WarehouseAPIClient(base_url=api_url) as client:
            # Авторизуемся
            if not client.login():
                logger.error("❌ Ошибка авторизации в Warehouse API")
                robot.finish_run(False, {"error": "Ошибка авторизации"})
                return

            # Цикл повторения сценария
            while time.time() < end_time and not robot.stop_requested:
                iteration += 1
                logger.info(f"🔄 Итерация {iteration} сценария {scenario_name}")

                # Создаём сценарий
                scenario_class = SCENARIOS.get(scenario_name)
                if not scenario_class:
                    logger.error(f"❌ Сценарий не найден: {scenario_name}")
                    robot.finish_run(False, {"error": f"Сценарий не найден: {scenario_name}"})
                    return

                scenario = scenario_class(client, speed=speed)

                # Выполняем сценарий
                result = scenario.run()
                result["iteration"] = iteration
                all_results.append(result)

                logger.info(f"✅ Итерация {iteration} завершена")

                # Отправляем уведомление после каждой итерации
                send_telegram_notification(scenario_name, result, environment)

                # Пауза между повторениями (если ещё есть время)
                if duration > 0 and time.time() < end_time and not robot.stop_requested:
                    remaining = end_time - time.time()
                    actual_pause = min(pause_seconds, remaining)
                    if actual_pause > 0:
                        logger.info(f"⏸️ Пауза {actual_pause:.0f}с перед следующей итерацией...")
                        time.sleep(actual_pause)
                else:
                    break  # Однократный запуск — выходим

            # Итоговый результат
            if robot.stop_requested:
                logger.info(f"🛑 Сценарий прерван после {iteration} итераций")
                robot.finish_run(False, {
                    "error": "Сценарий прерван",
                    "iterations": iteration,
                    "results": all_results,
                })
            else:
                elapsed = time.time() - start_time
                logger.info(f"✅ Сценарий завершён: {iteration} итераций за {elapsed:.0f}с")

                # Агрегируем результаты
                final_result = aggregate_results(scenario_name, all_results)
                robot.finish_run(True, final_result)

    except Exception as e:
        logger.exception(f"❌ Ошибка выполнения сценария: {e}")
        robot.finish_run(False, {"error": str(e), "iterations": iteration, "results": all_results})


def run_all_scenarios_task(speed: str, environment: str = "home", duration: int = 0):
    """
    Запуск всех сценариев по очереди в случайном порядке.

    Args:
        speed: Скорость выполнения (slow=15с, normal=5с, fast=1с пауза)
        environment: Окружение (home или prod)
        duration: Продолжительность повторения в минутах (0 = один раз)
    """
    api_url = get_api_url(environment)
    pause_seconds = get_pause_seconds(speed)

    # Получаем список всех сценариев и перемешиваем
    scenario_names = list(SCENARIOS.keys())
    random.shuffle(scenario_names)

    logger.info(f"🎲 Запуск ВСЕХ сценариев в порядке: {scenario_names}")

    if duration > 0:
        logger.info(f"🤖 Режим: duration={duration}мин, pause={pause_seconds}с, env={environment}")
    else:
        logger.info(f"🤖 Режим: однократно, speed={speed}, env={environment}")

    start_time = time.time()
    end_time = start_time + (duration * 60) if duration > 0 else start_time + 86400  # +24ч для однократного
    iteration = 0
    all_results = []

    try:
        # Создаём клиент API с URL для выбранного окружения
        with WarehouseAPIClient(base_url=api_url) as client:
            # Авторизуемся
            if not client.login():
                logger.error("❌ Ошибка авторизации в Warehouse API")
                robot.finish_run(False, {"error": "Ошибка авторизации"})
                return

            # Основной цикл
            first_round = True
            while time.time() < end_time and not robot.stop_requested:
                # Для duration > 0 — повторяем раунды сценариев
                # Для duration == 0 — один раунд

                for scenario_name in scenario_names:
                    if robot.stop_requested:
                        break
                    if time.time() >= end_time:
                        break

                    iteration += 1
                    logger.info(f"🔄 Итерация {iteration}: сценарий {scenario_name}")

                    # Создаём и запускаем сценарий
                    scenario_class = SCENARIOS.get(scenario_name)
                    scenario = scenario_class(client, speed=speed)
                    result = scenario.run()
                    result["iteration"] = iteration
                    result["scenario"] = scenario_name
                    all_results.append(result)

                    logger.info(f"✅ Сценарий {scenario_name} завершён")

                    # Отправляем уведомление
                    send_telegram_notification(scenario_name, result, environment)

                    # Пауза между сценариями
                    if time.time() < end_time and not robot.stop_requested:
                        remaining = end_time - time.time()
                        actual_pause = min(pause_seconds, remaining)
                        if actual_pause > 0:
                            logger.info(f"⏸️ Пауза {actual_pause:.0f}с перед следующим сценарием...")
                            time.sleep(actual_pause)

                # После первого раунда — выходим если duration == 0
                if duration == 0:
                    break

                # Перемешиваем для следующего раунда
                random.shuffle(scenario_names)
                logger.info(f"🔀 Следующий раунд в порядке: {scenario_names}")

            # Итоговый результат
            if robot.stop_requested:
                logger.info(f"🛑 Все сценарии прерваны после {iteration} итераций")
                robot.finish_run(False, {
                    "error": "Сценарии прерваны",
                    "iterations": iteration,
                    "results": all_results,
                })
            else:
                elapsed = time.time() - start_time
                logger.info(f"✅ Все сценарии завершены: {iteration} итераций за {elapsed:.0f}с")

                # Финальный результат
                final_result = {
                    "scenario": "all",
                    "description": "Все сценарии",
                    "total_iterations": iteration,
                    "elapsed_seconds": round(elapsed, 1),
                    "scenarios_executed": [r.get("scenario") for r in all_results],
                    "results": all_results,
                }
                robot.finish_run(True, final_result)

    except Exception as e:
        logger.exception(f"❌ Ошибка выполнения всех сценариев: {e}")
        robot.finish_run(False, {"error": str(e), "iterations": iteration, "results": all_results})


def aggregate_results(scenario_name: str, results: list) -> dict:
    """Агрегировать результаты нескольких итераций."""
    if not results:
        return {"scenario": scenario_name, "iterations": 0}

    # Возвращаем последний результат, но с общим количеством итераций
    final = results[-1].copy()
    final["total_iterations"] = len(results)

    # Для приёмки суммируем товары из всех итераций
    if scenario_name == "receiving":
        all_products = []
        total_qty = 0
        total_value = 0
        for r in results:
            all_products.extend(r.get("products", []))
            total_qty += r.get("total_quantity", 0)
            total_value += r.get("total_value", 0)
        final["products"] = all_products
        final["products_created"] = len(all_products)
        final["total_quantity"] = total_qty
        final["total_value"] = round(total_value, 2)

    # Для отгрузки суммируем детали
    elif scenario_name == "shipping":
        all_details = []
        total_shipped = 0
        total_value = 0
        for r in results:
            all_details.extend(r.get("details", []))
            total_shipped += r.get("total_shipped", 0)
            total_value += r.get("total_value", 0)
        final["details"] = all_details
        final["positions"] = len(all_details)
        final["total_shipped"] = total_shipped
        final["total_value"] = round(total_value, 2)

    # Для инвентаризации суммируем корректировки
    elif scenario_name == "inventory":
        all_adjustments = []
        all_deleted = []
        surplus = 0
        shortage = 0
        for r in results:
            all_adjustments.extend(r.get("adjustments", []))
            all_deleted.extend(r.get("deleted_products", []))
            surplus += r.get("surplus_count", 0)
            shortage += r.get("shortage_count", 0)
        final["adjustments"] = all_adjustments
        final["deleted_products"] = all_deleted
        final["adjusted"] = len(all_adjustments)
        final["deleted"] = len(all_deleted)
        final["surplus_count"] = surplus
        final["shortage_count"] = shortage

    return final


def send_telegram_notification(scenario_name: str, result: Dict[str, Any], environment: str = "home"):
    """
    Отправить уведомление в Telegram Bot и Uplink Bot.

    Args:
        scenario_name: Название сценария
        result: Результат выполнения
        environment: Окружение (home или prod)
    """
    import httpx

    message = format_notification_message(scenario_name, result)
    payload = {"message": message, "scenario": scenario_name, "result": result, "environment": environment}

    # Telegram Bot
    if settings.telegram_bot_url:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    f"{settings.telegram_bot_url}/robot/notify",
                    json=payload,
                )
                if response.status_code == 200:
                    logger.info("Уведомление отправлено в Telegram")
                else:
                    logger.warning(f"Telegram уведомление не отправлено: {response.status_code}")
        except Exception as e:
            logger.warning(f"Ошибка отправки в Telegram: {e}")

    # Uplink Bot (Matrix)
    if settings.uplink_bot_url:
        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    f"{settings.uplink_bot_url}/robot/notify",
                    json=payload,
                )
                if response.status_code == 200:
                    logger.info("Уведомление отправлено в Uplink")
                else:
                    logger.warning(f"Uplink уведомление не отправлено: {response.status_code}")
        except Exception as e:
            logger.warning(f"Ошибка отправки в Uplink: {e}")


def format_notification_message(scenario_name: str, result: Dict[str, Any]) -> str:
    """Форматирование сообщения уведомления с наименованиями товаров."""
    emoji_map = {
        "receiving": "📦",
        "shipping": "🚚",
        "inventory": "📋",
    }
    emoji = emoji_map.get(scenario_name, "🤖")

    # Формируем список товаров (максимум 10)
    products = result.get("products", [])
    products_list = ""
    if products:
        items = products[:10]  # Ограничиваем 10 товарами
        for p in items:
            name = p.get("name", "Без названия")
            qty = p.get("quantity", 0)
            products_list += f"  • {name} ({qty} шт)\n"
        if len(products) > 10:
            products_list += f"  ... и ещё {len(products) - 10} позиций\n"

    if scenario_name == "receiving":
        msg = (
            f"{emoji} *Приёмка завершена*\n\n"
            f"Создано товаров: {result.get('products_created', 0)}\n"
            f"Всего единиц: {result.get('total_quantity', 0)}\n"
            f"На сумму: {result.get('total_value', 0):.2f} ₽\n"
        )
        if products_list:
            msg += f"\n*Товары:*\n{products_list}"
        return msg
    elif scenario_name == "shipping":
        msg = (
            f"{emoji} *Отгрузка завершена*\n\n"
            f"Позиций: {result.get('positions', 0)}\n"
            f"Отгружено: {result.get('total_shipped', 0)} ед.\n"
            f"На сумму: {result.get('total_value', 0):.2f} ₽\n"
        )
        if products_list:
            msg += f"\n*Товары:*\n{products_list}"
        return msg
    elif scenario_name == "inventory":
        msg = (
            f"{emoji} *Инвентаризация завершена*\n\n"
            f"Корректировок: {result.get('adjusted', 0)}\n"
            f"(излишки: {result.get('surplus_count', 0)}, недостачи: {result.get('shortage_count', 0)})\n"
            f"Списано: {result.get('deleted', 0)}\n"
        )
        if products_list:
            msg += f"\n*Товары:*\n{products_list}"
        return msg
    else:
        return f"{emoji} Сценарий {scenario_name} завершён"


def parse_scheduled_time(time_str: str) -> datetime:
    """
    Парсинг времени запуска.

    Поддерживает форматы:
    - HH:MM — время сегодня (или завтра, если уже прошло)
    - YYYY-MM-DDTHH:MM:SS — полная дата и время
    """
    now = datetime.now()

    # Пробуем формат HH:MM
    if len(time_str) == 5 and ":" in time_str:
        try:
            hour, minute = map(int, time_str.split(":"))
            scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            # Если время уже прошло — переносим на завтра
            if scheduled <= now:
                scheduled += timedelta(days=1)
            return scheduled
        except ValueError:
            pass

    # Пробуем ISO формат
    try:
        scheduled = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        if scheduled <= now:
            raise HTTPException(
                status_code=400,
                detail=f"Указанное время уже прошло: {time_str}"
            )
        return scheduled
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Неверный формат времени: {time_str}. Используйте HH:MM или YYYY-MM-DDTHH:MM:SS"
        )


def run_scheduled_task(task_id: str, scenario_name: str, speed: str, environment: str = "home"):
    """Запуск запланированной задачи."""
    logger.info(f"⏰ Запуск запланированной задачи {task_id}: {scenario_name} (env={environment})")

    # Удаляем из списка запланированных
    scheduled_tasks.pop(task_id, None)
    scheduled_timers.pop(task_id, None)

    # Проверяем, что робот свободен
    if robot.state == RobotState.RUNNING:
        logger.warning(f"⚠️ Робот занят, задача {task_id} отменена")
        return

    # Запускаем сценарий
    robot.start_run(scenario_name)
    run_scenario_task(scenario_name, speed, environment)


# === Endpoints ===

@app.get("/", response_model=InfoResponse)
async def get_info():
    """Информация о сервисе."""
    return InfoResponse(
        name="Warehouse Robot",
        version="1.0.0",
        description="Робот-симулятор складских операций",
        available_scenarios=list(SCENARIOS.keys()),
        api_url=settings.api_url,
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check — проверка работоспособности."""
    api_available = False

    try:
        with WarehouseAPIClient() as client:
            api_available = client.health_check()
    except Exception:
        pass

    return HealthResponse(
        status="ok" if robot.state != RobotState.ERROR else "error",
        api_available=api_available,
        robot_state=robot.state.value,
    )


@app.post("/start", response_model=StartResponse)
async def start_scenario(request: StartRequest, background_tasks: BackgroundTasks):
    """
    Запуск сценария в фоновом режиме.

    - **scenario**: Название сценария (receiving, shipping, inventory)
    - **speed**: Скорость выполнения (slow=15с, normal=5с, fast=1с пауза)
    - **duration**: Продолжительность повторения в минутах (0 = один раз)
    """
    # Проверяем, что робот свободен
    if robot.state == RobotState.RUNNING:
        raise HTTPException(
            status_code=409,
            detail=f"Робот занят выполнением сценария: {robot.get_status()['current_scenario']}",
        )

    # Проверяем сценарий (разрешаем "all" для запуска всех)
    valid_scenarios = list(SCENARIOS.keys()) + ["all"]
    if request.scenario not in valid_scenarios:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный сценарий: {request.scenario}. Доступны: {valid_scenarios}",
        )

    # Запускаем в фоновом потоке
    scenario_label = "все сценарии" if request.scenario == "all" else request.scenario
    robot.start_run(scenario_label)

    thread = threading.Thread(
        target=run_scenario_task,
        args=(request.scenario, request.speed.value, request.environment.value, request.duration),
        daemon=True,
    )
    thread.start()

    env_label = "🏠 home" if request.environment == Environment.HOME else "🚀 prod"
    duration_label = f"duration={request.duration}мин" if request.duration > 0 else "однократно"
    pause_seconds = get_pause_seconds(request.speed.value)

    return StartResponse(
        status="started",
        message=f"Сценарий '{request.scenario}' запущен ({env_label}, {duration_label}, пауза={pause_seconds}с)",
        scenario=request.scenario,
    )


@app.post("/schedule", response_model=ScheduleResponse)
async def schedule_scenario(request: ScheduleRequest):
    """
    Запланировать запуск сценария на указанное время.

    - **scenario**: Название сценария (receiving, shipping, inventory)
    - **speed**: Скорость выполнения (slow, normal, fast)
    - **scheduled_time**: Время запуска (HH:MM или YYYY-MM-DDTHH:MM:SS)
    """
    # Проверяем сценарий
    if request.scenario not in SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный сценарий: {request.scenario}. Доступны: {list(SCENARIOS.keys())}",
        )

    # Парсим время
    scheduled_dt = parse_scheduled_time(request.scheduled_time)
    now = datetime.now()
    seconds_until_start = (scheduled_dt - now).total_seconds()

    # Создаём задачу
    task_id = str(uuid.uuid4())[:8]

    # Создаём таймер
    timer = threading.Timer(
        seconds_until_start,
        run_scheduled_task,
        args=(task_id, request.scenario, request.speed.value, request.environment.value),
    )
    timer.daemon = True
    timer.start()

    # Сохраняем информацию о задаче
    scheduled_tasks[task_id] = {
        "task_id": task_id,
        "scenario": request.scenario,
        "speed": request.speed.value,
        "environment": request.environment.value,
        "scheduled_time": scheduled_dt.isoformat(),
        "created_at": now.isoformat(),
    }
    scheduled_timers[task_id] = timer

    env_label = "🏠 home" if request.environment == Environment.HOME else "🚀 prod"
    logger.info(f"📅 Запланирован сценарий {request.scenario} на {scheduled_dt} ({env_label}, task_id={task_id})")

    return ScheduleResponse(
        status="scheduled",
        message=f"Сценарий '{request.scenario}' запланирован на {scheduled_dt.strftime('%H:%M %d.%m.%Y')}",
        task_id=task_id,
        scenario=request.scenario,
        scheduled_time=scheduled_dt.isoformat(),
        seconds_until_start=seconds_until_start,
    )


@app.get("/scheduled")
async def get_scheduled_tasks():
    """Получить список запланированных задач."""
    now = datetime.now()
    tasks = []
    for task_id, task_info in scheduled_tasks.items():
        scheduled_dt = datetime.fromisoformat(task_info["scheduled_time"])
        seconds_until = (scheduled_dt - now).total_seconds()
        tasks.append({
            **task_info,
            "seconds_until_start": max(0, seconds_until),
        })
    return {"scheduled_tasks": tasks, "count": len(tasks)}


@app.delete("/scheduled/{task_id}")
async def cancel_scheduled_task(task_id: str):
    """Отменить запланированную задачу."""
    if task_id not in scheduled_tasks:
        raise HTTPException(
            status_code=404,
            detail=f"Задача не найдена: {task_id}",
        )

    # Отменяем таймер
    timer = scheduled_timers.pop(task_id, None)
    if timer:
        timer.cancel()

    # Удаляем задачу
    task_info = scheduled_tasks.pop(task_id)

    logger.info(f"🚫 Отменена запланированная задача {task_id}: {task_info['scenario']}")

    return {
        "status": "cancelled",
        "message": f"Задача {task_id} отменена",
        "task": task_info,
    }


@app.post("/stop", response_model=StopResponse)
async def stop_robot():
    """
    Запрос на остановку робота.

    Сценарий будет остановлен после завершения текущего действия.
    """
    if robot.state != RobotState.RUNNING:
        raise HTTPException(
            status_code=400,
            detail="Робот не запущен",
        )

    robot.stop_requested = True
    robot.state = RobotState.STOPPING

    return StopResponse(
        status="stopping",
        message="Запрос на остановку отправлен. Сценарий будет остановлен после текущего действия.",
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Получить текущий статус робота."""
    status = robot.get_status()
    return StatusResponse(**status)


@app.get("/stats")
async def get_stats():
    """Получить статистику выполнения сценариев."""
    return robot.get_stats()


@app.get("/scenarios")
async def get_scenarios():
    """Получить список доступных сценариев."""
    scenarios_info = []
    for name, scenario_class in SCENARIOS.items():
        scenarios_info.append({
            "name": name,
            "description": scenario_class.description,
        })
    return {"scenarios": scenarios_info}


# Запуск при прямом вызове
if __name__ == "__main__":
    import uvicorn

    logger.info(f"🤖 Запуск Warehouse Robot API на порту {settings.api_port}")
    uvicorn.run(app, host="0.0.0.0", port=settings.api_port)
