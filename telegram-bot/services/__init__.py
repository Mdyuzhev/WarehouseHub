"""
Services module.
Все интеграции живут здесь! 🔌
"""

from .gitlab import trigger_gitlab_job, get_job_status
from .health import check_service_health, check_all_health, get_k8s_resources, get_prod_resources
from .locust import start_load_test, stop_load_test, get_load_test_stats, calculate_spawn_rate
from .allure import get_allure_report_stats, get_allure_report_details, get_allure_report_url
from .youtrack import get_open_stories, get_issue_by_id, get_activity_report, parse_issue_id
from .robot import robot_service, RobotService

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
]
