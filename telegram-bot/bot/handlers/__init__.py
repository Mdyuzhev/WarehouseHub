# -*- coding: utf-8 -*-
"""
Handlers module.
All command and callback handlers!
"""

from .commands import (
    handle_start,
    handle_help,
    handle_menu,
    handle_health,
    handle_joke,
    handle_metrics,
    handle_pods,
    handle_release,
)

from .deploy import (
    handle_deploy_menu,
    handle_deploy_command,
    request_deploy_password,
    handle_deploy_password_input,
    is_pending_deploy_password,
)

from .testing import (
    # QA Menu
    handle_qa_menu,
    handle_qa_env,
    handle_qa_test_type,
    handle_qa_run,
    handle_qa_report,
    # Load Testing
    handle_load_menu,
    handle_load_target,
    handle_load_users,
    handle_load_duration,
    request_password,
    handle_password_input,
    handle_stop_load_test,
    handle_load_status,
    is_pending_password,
)

from .claude import (
    handle_claude_menu,
    handle_claude_input,
    is_pending_claude,
)

from .pm import (
    handle_pm_menu,
    handle_in_progress,
    handle_stories_audit,
    handle_daily_report,
    handle_weekly_report,
    handle_issue_lookup,
)

from .gitlab_webhook import (
    handle_gitlab_webhook,
)

from .robot import (
    handle_robot_menu,
    handle_robot_status,
    handle_robot_stats,
    handle_robot_scenarios,
    handle_robot_duration_select,
    handle_robot_start,
    handle_robot_stop,
    handle_robot_speed_select,
    handle_robot_environment_select,
    request_robot_password,
    handle_robot_password_input,
    is_pending_robot_password,
    # Расписание
    handle_robot_schedule_menu,
    handle_robot_schedule_env,
    handle_robot_schedule_time,
    handle_robot_schedule_create,
    handle_robot_scheduled_list,
    handle_robot_cancel_scheduled,
    request_schedule_time_input,
    handle_schedule_time_input,
    is_pending_schedule_time,
)

__all__ = [
    # Commands
    "handle_start",
    "handle_help",
    "handle_menu",
    "handle_health",
    "handle_joke",
    "handle_metrics",
    "handle_pods",
    "handle_release",
    # Deploy
    "handle_deploy_menu",
    "handle_deploy_command",
    "request_deploy_password",
    "handle_deploy_password_input",
    "is_pending_deploy_password",
    # QA / Testing
    "handle_qa_menu",
    "handle_qa_env",
    "handle_qa_test_type",
    "handle_qa_run",
    "handle_qa_report",
    "handle_load_menu",
    "handle_load_target",
    "handle_load_users",
    "handle_load_duration",
    "request_password",
    "handle_password_input",
    "handle_stop_load_test",
    "handle_load_status",
    "is_pending_password",
    # Claude
    "handle_claude_menu",
    "handle_claude_input",
    "is_pending_claude",
    # PM
    "handle_pm_menu",
    "handle_in_progress",
    "handle_stories_audit",
    "handle_daily_report",
    "handle_weekly_report",
    "handle_issue_lookup",
    # GitLab Webhooks
    "handle_gitlab_webhook",
    # Robot
    "handle_robot_menu",
    "handle_robot_status",
    "handle_robot_stats",
    "handle_robot_scenarios",
    "handle_robot_duration_select",
    "handle_robot_start",
    "handle_robot_stop",
    "handle_robot_speed_select",
    "handle_robot_environment_select",
    "request_robot_password",
    "handle_robot_password_input",
    "is_pending_robot_password",
    # Robot Schedule
    "handle_robot_schedule_menu",
    "handle_robot_schedule_env",
    "handle_robot_schedule_time",
    "handle_robot_schedule_create",
    "handle_robot_scheduled_list",
    "handle_robot_cancel_scheduled",
    "request_schedule_time_input",
    "handle_schedule_time_input",
    "is_pending_schedule_time",
]
