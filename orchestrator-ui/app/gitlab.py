"""
🦊 GitLab API интеграция
Запуск джоб, получение статусов, логов и всего такого
"""

import httpx
from typing import Optional
from datetime import datetime

from .config import GITLAB_URL, GITLAB_TOKEN, GITLAB_PROJECTS, GITLAB_JOBS


class GitLabService:
    def __init__(self):
        self.base_url = f"{GITLAB_URL}/api/v4"
        self.headers = {"PRIVATE-TOKEN": GITLAB_TOKEN}

    async def get_latest_pipeline(self, project_id: int) -> Optional[dict]:
        """Получить последний пайплайн проекта"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/pipelines",
                headers=self.headers,
                params={"per_page": 1}
            )
            if response.status_code == 200:
                pipelines = response.json()
                return pipelines[0] if pipelines else None
        return None

    async def get_pipeline_jobs(self, project_id: int, pipeline_id: int) -> list:
        """Получить все джобы пайплайна"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/pipelines/{pipeline_id}/jobs",
                headers=self.headers,
                params={"per_page": 100}
            )
            if response.status_code == 200:
                return response.json()
        return []

    async def get_job_by_name(self, project_id: int, pipeline_id: int, job_name: str) -> Optional[dict]:
        """Найти джобу по имени в пайплайне"""
        jobs = await self.get_pipeline_jobs(project_id, pipeline_id)
        for job in jobs:
            if job.get("name") == job_name:
                return job
        return None

    async def play_job(self, project_id: int, job_id: int) -> dict:
        """Запустить manual джобу"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/projects/{project_id}/jobs/{job_id}/play",
                headers=self.headers
            )
            if response.status_code == 200:
                job = response.json()
                return {
                    "success": True,
                    "job_id": job.get("id"),
                    "job_name": job.get("name"),
                    "status": job.get("status"),
                    "web_url": job.get("web_url"),
                    "message": f"🚀 Джоба {job.get('name')} запущена! Job ID: {job.get('id')}"
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ Ошибка запуска: {response.text}"
                }

    async def get_job_status(self, project_id: int, job_id: int) -> Optional[dict]:
        """Получить статус джобы"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/jobs/{job_id}",
                headers=self.headers
            )
            if response.status_code == 200:
                return response.json()
        return None

    async def get_job_log(self, project_id: int, job_id: int, tail: int = 50) -> str:
        """Получить логи джобы"""
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/projects/{project_id}/jobs/{job_id}/trace",
                headers=self.headers
            )
            if response.status_code == 200:
                lines = response.text.split('\n')
                return '\n'.join(lines[-tail:])
        return ""

    async def create_pipeline(self, project_id: int, ref: str = "main") -> dict:
        """Создать новый пайплайн"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/projects/{project_id}/pipeline",
                headers=self.headers,
                params={"ref": ref}
            )
            if response.status_code == 201:
                pipeline = response.json()
                return {
                    "success": True,
                    "pipeline_id": pipeline.get("id"),
                    "web_url": pipeline.get("web_url"),
                    "message": f"🎮 Новый pipeline #{pipeline.get('id')} создан!"
                }
            else:
                return {
                    "success": False,
                    "message": f"❌ Ошибка создания pipeline: {response.text}"
                }

    async def run_job_by_name(self, project_id: int, job_name: str) -> dict:
        """Запустить джобу по имени (найти в последнем пайплайне или создать новый)"""
        # Получаем последний пайплайн
        pipeline = await self.get_latest_pipeline(project_id)

        if not pipeline:
            # Создаём новый пайплайн
            result = await self.create_pipeline(project_id)
            if not result["success"]:
                return result
            pipeline = await self.get_latest_pipeline(project_id)

        # Ищем джобу
        job = await self.get_job_by_name(project_id, pipeline["id"], job_name)

        if not job:
            return {
                "success": False,
                "message": f"❌ Джоба '{job_name}' не найдена в pipeline #{pipeline['id']}"
            }

        # Проверяем статус
        if job.get("status") == "running":
            return {
                "success": False,
                "message": f"⏳ Джоба '{job_name}' уже выполняется!"
            }

        if job.get("status") == "success":
            # Нужен новый пайплайн для перезапуска
            result = await self.create_pipeline(project_id)
            if not result["success"]:
                return result
            # Ждём немного и получаем новый пайплайн
            import asyncio
            await asyncio.sleep(2)
            pipeline = await self.get_latest_pipeline(project_id)
            job = await self.get_job_by_name(project_id, pipeline["id"], job_name)
            if not job:
                return {"success": False, "message": "❌ Не удалось найти джобу в новом пайплайне"}

        # Запускаем
        return await self.play_job(project_id, job["id"])

    async def get_all_jobs_status(self, project_id: int = 4) -> list:
        """Получить статус всех джоб из последнего пайплайна"""
        pipeline = await self.get_latest_pipeline(project_id)
        if not pipeline:
            return []

        jobs = await self.get_pipeline_jobs(project_id, pipeline["id"])

        result = []
        for job in jobs:
            result.append({
                "id": job.get("id"),
                "name": job.get("name"),
                "status": job.get("status"),
                "stage": job.get("stage"),
                "started_at": job.get("started_at"),
                "finished_at": job.get("finished_at"),
                "duration": job.get("duration"),
                "web_url": job.get("web_url"),
            })

        return result

    def get_available_jobs(self, project_id: int = 4) -> list:
        """Получить список доступных для запуска джоб"""
        return GITLAB_JOBS.get(project_id, [])


# Глобальный экземпляр
gitlab_service = GitLabService()
