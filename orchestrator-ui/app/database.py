"""
🗃️ База данных для истории чата с агентом
SQLite - просто и надёжно, как дискета
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

from .config import SQLITE_DB


async def init_db():
    """Инициализация базы данных - создаём таблицы если их нет"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        # Таблица сессий
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                title TEXT,
                is_active BOOLEAN DEFAULT 1
            )
        """)

        # Таблица сообщений
        await db.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                role TEXT NOT NULL,  -- 'user' или 'agent'
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,  -- JSON с доп. данными
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # Таблица логов операций
        await db.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation TEXT NOT NULL,  -- deploy, tests, status, etc.
                status TEXT NOT NULL,  -- running, success, error
                output TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finished_at TIMESTAMP
            )
        """)

        await db.commit()
        print("🎮 База данных готова к бою!")


async def create_session(title: Optional[str] = None) -> int:
    """Создать новую сессию чата"""
    if not title:
        title = f"Сессия {datetime.now().strftime('%d.%m.%Y %H:%M')}"

    async with aiosqlite.connect(SQLITE_DB) as db:
        cursor = await db.execute(
            "INSERT INTO sessions (title) VALUES (?)",
            (title,)
        )
        await db.commit()
        return cursor.lastrowid


async def get_active_session() -> Optional[dict]:
    """Получить активную сессию или None"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM sessions WHERE is_active = 1 ORDER BY id DESC LIMIT 1"
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_or_create_session() -> int:
    """Получить активную сессию или создать новую"""
    session = await get_active_session()
    if session:
        return session['id']
    return await create_session()


async def add_message(session_id: int, role: str, content: str, metadata: dict = None) -> int:
    """Добавить сообщение в историю"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        cursor = await db.execute(
            "INSERT INTO messages (session_id, role, content, metadata) VALUES (?, ?, ?, ?)",
            (session_id, role, content, json.dumps(metadata) if metadata else None)
        )
        await db.commit()
        return cursor.lastrowid


async def get_session_messages(session_id: int, limit: int = 50) -> list:
    """Получить историю сообщений сессии"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT * FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ?
            """,
            (session_id, limit)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_all_sessions(limit: int = 20) -> list:
    """Получить список всех сессий"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """
            SELECT s.*, COUNT(m.id) as message_count
            FROM sessions s
            LEFT JOIN messages m ON s.id = m.session_id
            GROUP BY s.id
            ORDER BY s.created_at DESC
            LIMIT ?
            """,
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def close_session(session_id: int):
    """Закрыть сессию"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        await db.execute(
            "UPDATE sessions SET is_active = 0 WHERE id = ?",
            (session_id,)
        )
        await db.commit()


async def log_operation(operation: str, status: str, output: str = None) -> int:
    """Залогировать операцию"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        cursor = await db.execute(
            "INSERT INTO operation_logs (operation, status, output) VALUES (?, ?, ?)",
            (operation, status, output)
        )
        await db.commit()
        return cursor.lastrowid


async def update_operation(operation_id: int, status: str, output: str = None):
    """Обновить статус операции"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        await db.execute(
            """
            UPDATE operation_logs
            SET status = ?, output = ?, finished_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, output, operation_id)
        )
        await db.commit()


async def get_recent_operations(limit: int = 10) -> list:
    """Получить последние операции"""
    async with aiosqlite.connect(SQLITE_DB) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM operation_logs ORDER BY started_at DESC LIMIT ?",
            (limit,)
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
