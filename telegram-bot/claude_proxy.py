#!/usr/bin/env python3
"""
Claude Proxy Service - HTTP API для вызова Claude CLI.
Запускается на хосте, чтобы иметь доступ к credentials.
"""

import asyncio
import subprocess
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import threading

# Путь к файлу контекста проекта (в warehouse-master)
CONTEXT_FILE = "/home/flomaster/warehouse-master/.claude/project-context.md"

def load_context():
    """Загружает контекст проекта из файла."""
    try:
        if os.path.exists(CONTEXT_FILE):
            with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
                return f.read()
    except Exception as e:
        print(f"[ClaudeProxy] Failed to load context: {e}")
    return ""

def build_prompt(task: str, context: str) -> str:
    """Формирует полный промпт с контекстом."""
    if context:
        return f"""Прочитай контекст проекта и выполни задачу.

<project_context>
{context}
</project_context>

<task>
{task}
</task>

Выполни задачу, используя информацию из контекста. Отвечай кратко и по делу, с юмором."""
    return task


class ClaudeProxyHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/execute":
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')

            try:
                data = json.loads(post_data)
                task = data.get("task", "")
                cwd = data.get("cwd", "/home/flomaster/warehouse-api")
                timeout = data.get("timeout", 300)
                use_context = data.get("use_context", True)  # По умолчанию с контекстом

                if not task:
                    self.send_error(400, "task is required")
                    return

                # Загружаем контекст и формируем промпт
                context = load_context() if use_context else ""
                full_prompt = build_prompt(task, context)

                print(f"[ClaudeProxy] Executing task: {task[:100]}...")

                # Запускаем Claude CLI
                try:
                    result = subprocess.run(
                        ["claude", "-p", full_prompt],
                        capture_output=True,
                        text=True,
                        timeout=timeout,
                        cwd=cwd
                    )

                    response = {
                        "success": result.returncode == 0,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "returncode": result.returncode
                    }
                    print(f"[ClaudeProxy] Task completed, returncode: {result.returncode}")
                except subprocess.TimeoutExpired:
                    response = {
                        "success": False,
                        "stdout": "",
                        "stderr": f"Timeout after {timeout} seconds",
                        "returncode": -1
                    }
                    print(f"[ClaudeProxy] Task timeout after {timeout}s")
                except Exception as e:
                    response = {
                        "success": False,
                        "stdout": "",
                        "stderr": str(e),
                        "returncode": -1
                    }
                    print(f"[ClaudeProxy] Task error: {e}")

                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(404, "Not found")

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "claude-proxy"}).encode())
        else:
            self.send_error(404, "Not found")

    def log_message(self, format, *args):
        print(f"[ClaudeProxy] {args[0]}")


def run_server(port=8765):
    server = HTTPServer(('0.0.0.0', port), ClaudeProxyHandler)
    print(f"Claude Proxy running on port {port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
