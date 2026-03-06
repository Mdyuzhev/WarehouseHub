# -*- coding: utf-8 -*-
"""
Handlers module.
Minimal: status, metrics, robot, help.
"""

from .commands import (
    handle_start,
    handle_help,
    handle_menu,
    handle_health,
    handle_metrics,
    handle_pods,
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
    "handle_start", "handle_help", "handle_menu",
    "handle_health", "handle_metrics", "handle_pods",
    "handle_robot_menu", "handle_robot_status", "handle_robot_stats",
    "handle_robot_scenarios", "handle_robot_duration_select",
    "handle_robot_start", "handle_robot_stop",
    "handle_robot_speed_select", "handle_robot_environment_select",
    "handle_robot_schedule_menu", "handle_robot_schedule_env", "handle_robot_schedule_time",
    "handle_robot_schedule_create", "handle_robot_scheduled_list", "handle_robot_cancel_scheduled",
    "request_schedule_time_input", "handle_schedule_time_input", "is_pending_schedule_time",
]
