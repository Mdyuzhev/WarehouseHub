"""
Сервис очистки данных перед нагрузочным тестированием.
Чистим Redis, Kafka, PostgreSQL до блеска! 🧹
WH-221
"""

import logging
import asyncio
from typing import Dict, Any

from config import (
    REDIS_STAGING_HOST, REDIS_STAGING_PORT,
    REDIS_PROD_HOST, REDIS_PROD_PORT,
    KAFKA_STAGING_BROKERS, KAFKA_PROD_BROKERS,
    POSTGRES_STAGING_URL, POSTGRES_PROD_URL,
)

logger = logging.getLogger(__name__)


async def _run_kubectl(cmd: str, timeout: int = 30) -> tuple[bool, str]:
    """
    Выполняет kubectl команду и возвращает результат.

    Returns:
        tuple[bool, str]: (success, output/error)
    """
    try:
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        if process.returncode == 0:
            return True, stdout.decode().strip()
        else:
            return False, stderr.decode().strip()[:200]

    except asyncio.TimeoutError:
        return False, "Timeout"
    except Exception as e:
        return False, str(e)[:200]


async def cleanup_redis(environment: str) -> Dict[str, Any]:
    """
    Очистка Redis перед НТ.

    Args:
        environment: 'staging' или 'prod'

    Returns:
        dict: {success: bool, keys_deleted: int, error: str}
    """
    try:
        if environment == "staging":
            # Через kubectl exec в redis pod
            cmd = (
                "kubectl exec -n warehouse deploy/redis -- "
                "redis-cli FLUSHDB"
            )
            count_cmd = (
                "kubectl exec -n warehouse deploy/redis -- "
                "redis-cli DBSIZE"
            )
        else:
            # Для prod - через SSH + docker exec
            ssh_prefix = "ssh -i /root/.ssh/yc_prod_key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@130.193.44.34"
            cmd = f"{ssh_prefix} 'docker exec warehouse-redis redis-cli FLUSHDB'"
            count_cmd = f"{ssh_prefix} 'docker exec warehouse-redis redis-cli DBSIZE'"

        success, output = await _run_kubectl(count_cmd)
        keys_before = 0
        if success and ":" in output:
            try:
                keys_before = int(output.split(":")[-1].strip())
            except ValueError:
                pass

        # Очищаем
        success, output = await _run_kubectl(cmd)

        if success:
            logger.info(f"Redis cleanup ({environment}): {keys_before} keys deleted")
            return {
                "success": True,
                "keys_deleted": keys_before,
                "message": f"Очищено {keys_before} ключей"
            }
        else:
            logger.error(f"Redis cleanup error ({environment}): {output}")
            return {"success": False, "keys_deleted": 0, "error": output}

    except Exception as e:
        logger.error(f"Redis cleanup exception ({environment}): {e}")
        return {"success": False, "keys_deleted": 0, "error": str(e)[:100]}


async def cleanup_kafka(environment: str) -> Dict[str, Any]:
    """
    Очистка Kafka topics перед НТ.
    Удаляет consumer groups для чистого старта.

    Args:
        environment: 'staging' или 'prod'

    Returns:
        dict: {success: bool, topics_cleared: list, error: str}
    """
    try:
        ssh_prefix = "ssh -i /root/.ssh/yc_prod_key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@130.193.44.34"

        if environment == "staging":
            # Staging: kubectl exec
            list_cmd = (
                "kubectl exec -n warehouse deploy/kafka -- "
                "/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list"
            )
        else:
            # Prod: SSH + docker exec
            list_cmd = (
                f"{ssh_prefix} 'docker exec warehouse-kafka "
                f"/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list'"
            )

        success, output = await _run_kubectl(list_cmd)
        if not success:
            return {"success": False, "topics_cleared": [], "error": f"Failed to list groups: {output}"}

        groups = [g.strip() for g in output.split("\n") if g.strip()]
        cleared_groups = []

        # Удаляем каждый consumer group (кроме системных)
        for group in groups:
            if group.startswith("_") or group.startswith("console-"):
                continue

            if environment == "staging":
                delete_cmd = (
                    "kubectl exec -n warehouse deploy/kafka -- "
                    f"/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 "
                    f"--delete --group {group}"
                )
            else:
                delete_cmd = (
                    f"{ssh_prefix} 'docker exec warehouse-kafka "
                    f"/opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092 "
                    f"--delete --group {group}'"
                )

            success, _ = await _run_kubectl(delete_cmd)
            if success:
                cleared_groups.append(group)

        logger.info(f"Kafka cleanup ({environment}): cleared {len(cleared_groups)} consumer groups")
        return {
            "success": True,
            "topics_cleared": cleared_groups,
            "message": f"Удалено {len(cleared_groups)} consumer groups"
        }

    except Exception as e:
        logger.error(f"Kafka cleanup exception ({environment}): {e}")
        return {"success": False, "topics_cleared": [], "error": str(e)[:100]}


async def cleanup_postgres(environment: str) -> Dict[str, Any]:
    """
    Очистка тестовых данных в PostgreSQL.
    Удаляет только данные созданные нагрузочным тестированием.

    Args:
        environment: 'staging' или 'prod'

    Returns:
        dict: {success: bool, rows_deleted: int, error: str}
    """
    try:
        ssh_prefix = "ssh -i /root/.ssh/yc_prod_key -o StrictHostKeyChecking=no -o ConnectTimeout=10 ubuntu@130.193.44.34"

        # SQL команды для удаления тестовых данных
        sql_commands = [
            "DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE notes LIKE '%LoadTest%');",
            "DELETE FROM orders WHERE notes LIKE '%LoadTest%';",
            "DELETE FROM products WHERE name LIKE '%LoadTest%' OR name LIKE '%k6%';",
        ]

        total_deleted = 0
        errors = []

        for sql in sql_commands:
            if environment == "staging":
                cmd = (
                    f"kubectl exec -n warehouse deploy/postgresql -- "
                    f'psql -U warehouse -d warehouse -c "{sql}"'
                )
            else:
                # Prod: SSH + docker exec
                cmd = (
                    f'{ssh_prefix} \'docker exec warehouse-db '
                    f'psql -U warehouse -d warehouse -c "{sql}"\''
                )

            success, output = await _run_kubectl(cmd, timeout=60)

            if success:
                # Парсим количество удалённых строк из вывода "DELETE X"
                if "DELETE" in output:
                    try:
                        count = int(output.split()[-1])
                        total_deleted += count
                    except (ValueError, IndexError):
                        pass
            else:
                errors.append(output)

        if errors:
            logger.warning(f"PostgreSQL cleanup ({environment}): {total_deleted} rows, errors: {errors}")
            return {
                "success": True,  # Частичный успех
                "rows_deleted": total_deleted,
                "warnings": errors
            }

        logger.info(f"PostgreSQL cleanup ({environment}): {total_deleted} rows deleted")
        return {
            "success": True,
            "rows_deleted": total_deleted,
            "message": f"Удалено {total_deleted} строк"
        }

    except Exception as e:
        logger.error(f"PostgreSQL cleanup exception ({environment}): {e}")
        return {"success": False, "rows_deleted": 0, "error": str(e)[:100]}


async def cleanup_all(environment: str) -> Dict[str, Any]:
    """
    Полная очистка всех систем.

    Args:
        environment: 'staging' или 'prod'

    Returns:
        dict: Сводка по каждому компоненту
    """
    logger.info(f"Starting full cleanup for {environment}")

    # Запускаем все очистки параллельно
    redis_task = asyncio.create_task(cleanup_redis(environment))
    kafka_task = asyncio.create_task(cleanup_kafka(environment))
    postgres_task = asyncio.create_task(cleanup_postgres(environment))

    redis_result, kafka_result, postgres_result = await asyncio.gather(
        redis_task, kafka_task, postgres_task
    )

    result = {
        "redis": redis_result,
        "kafka": kafka_result,
        "postgres": postgres_result,
        "environment": environment,
    }

    # Общий статус
    all_success = all([
        redis_result.get("success", False),
        kafka_result.get("success", False),
        postgres_result.get("success", False),
    ])

    result["all_success"] = all_success

    if all_success:
        logger.info(f"Full cleanup ({environment}): SUCCESS")
    else:
        logger.warning(f"Full cleanup ({environment}): PARTIAL")

    return result
