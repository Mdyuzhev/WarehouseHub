"""
GitLab CI/CD интеграция.
Триггерим jobs, мониторим статусы, всё как у взрослых! 🎯
"""

import logging
import httpx
from config import GITLAB_URL, GITLAB_TOKEN, GITLAB_PROJECTS

logger = logging.getLogger(__name__)


async def trigger_gitlab_job(project_name: str, job_name: str, ref: str = "main") -> dict:
    """
    Триггерит manual job в GitLab CI.

    Returns:
        dict с полями: success, job_id, web_url, error
    """
    project_id = GITLAB_PROJECTS.get(project_name)
    if not project_id:
        return {"success": False, "error": f"Unknown project: {project_name}"}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 1. Получаем последний pipeline
            pipelines_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/pipelines"
            resp = await client.get(
                pipelines_url,
                headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
                params={"ref": ref, "per_page": 1}
            )

            if resp.status_code != 200:
                # Создаём новый pipeline если нет
                create_resp = await client.post(
                    pipelines_url,
                    headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
                    json={"ref": ref}
                )
                if create_resp.status_code not in [200, 201]:
                    return {"success": False, "error": f"Failed to create pipeline: {create_resp.status_code}"}
                pipeline = create_resp.json()
            else:
                pipelines = resp.json()
                if not pipelines:
                    # Создаём новый pipeline
                    create_resp = await client.post(
                        pipelines_url,
                        headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
                        json={"ref": ref}
                    )
                    if create_resp.status_code not in [200, 201]:
                        return {"success": False, "error": f"Failed to create pipeline: {create_resp.status_code}"}
                    pipeline = create_resp.json()
                else:
                    pipeline = pipelines[0]

            pipeline_id = pipeline["id"]

            # 2. Получаем jobs этого pipeline
            jobs_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/pipelines/{pipeline_id}/jobs"
            jobs_resp = await client.get(
                jobs_url,
                headers={"PRIVATE-TOKEN": GITLAB_TOKEN},
                params={"per_page": 100}
            )

            if jobs_resp.status_code != 200:
                return {"success": False, "error": f"Failed to get jobs: {jobs_resp.status_code}"}

            jobs = jobs_resp.json()

            # 3. Находим нужный job
            target_job = None
            for job in jobs:
                if job["name"] == job_name:
                    target_job = job
                    break

            if not target_job:
                return {"success": False, "error": f"Job '{job_name}' not found in pipeline {pipeline_id}"}

            job_id = target_job["id"]
            job_status = target_job["status"]

            # 4. Запускаем job (play для manual jobs)
            if job_status == "manual":
                play_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/jobs/{job_id}/play"
                play_resp = await client.post(
                    play_url,
                    headers={"PRIVATE-TOKEN": GITLAB_TOKEN}
                )

                if play_resp.status_code not in [200, 201]:
                    return {"success": False, "error": f"Failed to play job: {play_resp.status_code}"}

                job_data = play_resp.json()
                return {
                    "success": True,
                    "job_id": job_data["id"],
                    "web_url": job_data.get("web_url", f"{GITLAB_URL}/root/{project_name}/-/jobs/{job_id}"),
                    "status": job_data.get("status", "pending")
                }

            elif job_status in ["pending", "running"]:
                return {
                    "success": True,
                    "job_id": job_id,
                    "web_url": target_job.get("web_url", f"{GITLAB_URL}/root/{project_name}/-/jobs/{job_id}"),
                    "status": job_status,
                    "message": "Job already running"
                }

            elif job_status == "success":
                # Job уже выполнен, retry
                retry_url = f"{GITLAB_URL}/api/v4/projects/{project_id}/jobs/{job_id}/retry"
                retry_resp = await client.post(
                    retry_url,
                    headers={"PRIVATE-TOKEN": GITLAB_TOKEN}
                )

                if retry_resp.status_code not in [200, 201]:
                    return {"success": False, "error": f"Failed to retry job: {retry_resp.status_code}"}

                job_data = retry_resp.json()
                return {
                    "success": True,
                    "job_id": job_data["id"],
                    "web_url": job_data.get("web_url", f"{GITLAB_URL}/root/{project_name}/-/jobs/{job_data['id']}"),
                    "status": job_data.get("status", "pending")
                }

            else:
                return {"success": False, "error": f"Job status is '{job_status}', cannot trigger"}

    except Exception as e:
        logger.error(f"GitLab trigger error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def get_job_status(project_name: str, job_id: int) -> dict:
    """Получает статус job."""
    project_id = GITLAB_PROJECTS.get(project_name)
    if not project_id:
        return {"success": False, "error": f"Unknown project: {project_name}"}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{GITLAB_URL}/api/v4/projects/{project_id}/jobs/{job_id}"
            resp = await client.get(
                url,
                headers={"PRIVATE-TOKEN": GITLAB_TOKEN}
            )

            if resp.status_code == 200:
                job = resp.json()
                return {
                    "success": True,
                    "status": job.get("status"),
                    "duration": job.get("duration"),
                    "web_url": job.get("web_url"),
                    "finished_at": job.get("finished_at")
                }
            return {"success": False, "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)[:100]}
