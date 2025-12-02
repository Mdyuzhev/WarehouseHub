"""
Services module.
Все интеграции живут здесь! 🔌
WH-223: добавлен cleanup
"""

from .gitlab import trigger_gitlab_job, get_job_status
from .health import check_service_health, check_all_health, get_k8s_resources, get_prod_resources
from .locust import start_load_test, stop_load_test, get_load_test_stats, calculate_spawn_rate
from .allure import get_allure_report_stats, get_allure_report_details, get_allure_report_url
from .youtrack import get_open_stories, get_issue_by_id, get_activity_report, parse_issue_id
from .robot import robot_service, RobotService
from .k6 import start_k6_test, stop_k6_test, get_k6_status, get_k6_logs
from .cleanup import cleanup_redis, cleanup_kafka, cleanup_postgres, cleanup_all  # WH-223

__all__ = [
    # GitLab
    "trigger_gitlab_job",
    "get_job_status",
    # Health
    "check_service_health",
    "check_all_health",
    "get_k8s_resources",
    "get_prod_resources",
    # Locust
    "start_load_test",
    "stop_load_test",
    "get_load_test_stats",
    "calculate_spawn_rate",
    # Allure
    "get_allure_report_stats",
    "get_allure_report_details",
    "get_allure_report_url",
    # YouTrack
    "get_open_stories",
    "get_issue_by_id",
    "get_activity_report",
    "parse_issue_id",
    # Robot
    "robot_service",
    "RobotService",
    # k6 Kafka
    "start_k6_test",
    "stop_k6_test",
    "get_k6_status",
    "get_k6_logs",
    # Cleanup (WH-223)
    "cleanup_redis",
    "cleanup_kafka",
    "cleanup_postgres",
    "cleanup_all",
]
