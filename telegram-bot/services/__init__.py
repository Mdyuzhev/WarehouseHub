"""
Services module.
A5 8=B53@0F88 682CB 745AL! =
"""

from .gitlab import trigger_gitlab_job, get_job_status
from .health import check_service_health, check_all_health, get_k8s_resources, get_prod_resources
from .locust import start_load_test, stop_load_test, get_load_test_stats, calculate_spawn_rate
from .allure import get_allure_report_stats, get_allure_report_details, get_allure_report_url

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
]
