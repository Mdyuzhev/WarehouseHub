"""
k6 Kafka нагрузочное тестирование.
Гоняем Kafka до посинения! 🔥
WH-215, WH-222
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional

from config import KAFKA_STAGING_BROKERS, KAFKA_PROD_BROKERS

logger = logging.getLogger(__name__)

# Константы
NAMESPACE = "loadtest"
CONFIGMAP_NAME = "k6-scripts"
JOB_BASE_NAME = "k6-kafka-test"

# WH-222: Разные Kafka brokers для сред
KAFKA_BROKERS = {
    "staging": KAFKA_STAGING_BROKERS or "kafka.warehouse.svc.cluster.local:9092",
    "prod": KAFKA_PROD_BROKERS or "kafka-prod.warehouse.svc.cluster.local:9092",
}


async def start_k6_test(
    scenario: str = "producer",
    vus: int = 10,
    duration: str = "2m",
    environment: str = "staging"  # WH-222: NEW
) -> Dict[str, Any]:
    """
    Запускает k6 Kafka тест через kubectl.

    Args:
        scenario: "producer" или "consumer"
        vus: количество виртуальных пользователей
        duration: длительность теста (например "2m", "30m")
        environment: "staging" или "prod" (WH-222)

    Returns:
        dict с полями: success, job_name, error
    """
    try:
        script = "producer-test.js" if scenario == "producer" else "consumer-test.js"
        job_name = f"{JOB_BASE_NAME}-{scenario}-{environment}"  # WH-222: environment в имени

        # WH-222: Получаем brokers для среды
        kafka_brokers = KAFKA_BROKERS.get(environment, KAFKA_BROKERS["staging"])

        # Удалить предыдущий job если есть
        delete_cmd = f"kubectl delete job {job_name} -n {NAMESPACE} --ignore-not-found"
        await asyncio.create_subprocess_shell(
            delete_cmd,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await asyncio.sleep(2)

        # Создать Job YAML (WH-222: добавлены environment лейблы и env vars)
        job_yaml = f"""apiVersion: batch/v1
kind: Job
metadata:
  name: {job_name}
  namespace: {NAMESPACE}
  labels:
    app: k6
    test-type: kafka
    scenario: {scenario}
    environment: {environment}
spec:
  backoffLimit: 0
  ttlSecondsAfterFinished: 3600
  template:
    metadata:
      labels:
        app: k6
        scenario: {scenario}
        environment: {environment}
    spec:
      serviceAccountName: k6-runner
      restartPolicy: Never
      containers:
        - name: k6
          image: k6-kafka:latest
          imagePullPolicy: Never
          args:
            - run
            - --out
            - experimental-prometheus-rw
            - /scripts/{script}
          env:
            - name: K6_PROMETHEUS_RW_SERVER_URL
              value: "http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090/api/v1/write"
            - name: K6_PROMETHEUS_RW_TREND_AS_NATIVE_HISTOGRAM
              value: "true"
            - name: KAFKA_BROKERS
              value: "{kafka_brokers}"
            - name: K6_VUS
              value: "{vus}"
            - name: K6_DURATION
              value: "{duration}"
            - name: K6_ENVIRONMENT
              value: "{environment}"
          volumeMounts:
            - name: scripts
              mountPath: /scripts
          resources:
            requests:
              memory: "256Mi"
              cpu: "200m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
      volumes:
        - name: scripts
          configMap:
            name: {CONFIGMAP_NAME}
"""
        # Применить Job
        process = await asyncio.create_subprocess_shell(
            f"echo '{job_yaml}' | kubectl apply -f -",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            logger.info(f"K6 test started: {job_name}, VUs: {vus}, Duration: {duration}, Env: {environment}")
            return {
                "success": True,
                "job_name": job_name,
                "vus": vus,
                "duration": duration,
                "scenario": scenario,
                "environment": environment  # WH-222
            }
        else:
            error = stderr.decode().strip()[:200]
            logger.error(f"K6 start error: {error}")
            return {"success": False, "error": error}

    except Exception as e:
        logger.error(f"K6 start exception: {e}")
        return {"success": False, "error": str(e)[:100]}


async def stop_k6_test(job_name: Optional[str] = None) -> Dict[str, Any]:
    """Останавливает k6 тест (удаляет Job)."""
    try:
        if job_name:
            cmd = f"kubectl delete job {job_name} -n {NAMESPACE} --ignore-not-found"
        else:
            cmd = f"kubectl delete job -n {NAMESPACE} -l app=k6 --ignore-not-found"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        return {"success": True}

    except Exception as e:
        logger.error(f"K6 stop error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def get_k6_status(job_name: Optional[str] = None, environment: Optional[str] = None) -> Dict[str, Any]:
    """
    Получает статус k6 теста.

    Args:
        job_name: конкретный job (опционально)
        environment: фильтр по среде 'staging' или 'prod' (WH-222)
    """
    try:
        if job_name:
            cmd = f"kubectl get job {job_name} -n {NAMESPACE} -o json"
        elif environment:
            # WH-222: фильтрация по environment
            cmd = f"kubectl get jobs -n {NAMESPACE} -l app=k6,environment={environment} -o json"
        else:
            cmd = f"kubectl get jobs -n {NAMESPACE} -l app=k6 -o json"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            return {"success": False, "status": "not_found"}

        data = json.loads(stdout.decode())

        # Если получаем список
        if "items" in data:
            if not data["items"]:
                return {"success": True, "status": "no_tests", "jobs": []}
            jobs = data["items"]
        else:
            jobs = [data]

        results = []
        for job in jobs:
            name = job.get("metadata", {}).get("name", "unknown")
            status = job.get("status", {})

            if status.get("succeeded", 0) > 0:
                job_status = "completed"
            elif status.get("failed", 0) > 0:
                job_status = "failed"
            elif status.get("active", 0) > 0:
                job_status = "running"
            else:
                job_status = "pending"

            results.append({
                "name": name,
                "status": job_status,
                "start_time": status.get("startTime", "N/A"),
                "completion_time": status.get("completionTime", "N/A")
            })

        return {"success": True, "jobs": results}

    except Exception as e:
        logger.error(f"K6 status error: {e}")
        return {"success": False, "error": str(e)[:100]}


async def get_k6_logs(job_name: str, tail: int = 50) -> Dict[str, Any]:
    """Получает логи k6 теста."""
    try:
        cmd = f"kubectl logs -n {NAMESPACE} job/{job_name} --tail={tail}"

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return {"success": True, "logs": stdout.decode()[-2000:]}  # Последние 2000 символов
        else:
            return {"success": False, "error": stderr.decode()[:200]}

    except Exception as e:
        return {"success": False, "error": str(e)[:100]}
