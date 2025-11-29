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
)

from .deploy import (
    handle_deploy_menu,
    handle_deploy_command,
)

from .testing import (
    handle_e2e_menu,
    handle_e2e_run,
    handle_e2e_report,
    handle_load_menu,
    handle_load_target,
    handle_load_users,
    handle_load_duration,
    request_password,
    handle_password_input,
    handle_stop_load_test,
    handle_load_status,
    is_pending_password,
    is_pending_wizard,
)

from .claude import (
    handle_claude_menu,
    handle_claude_input,
    is_pending_claude,
)

from .gitlab_webhook import (
    handle_gitlab_webhook,
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
    # Deploy
    "handle_deploy_menu",
    "handle_deploy_command",
    # Testing
    "handle_e2e_menu",
    "handle_e2e_run",
    "handle_e2e_report",
    "handle_load_menu",
    "handle_load_target",
    "handle_load_users",
    "handle_load_duration",
    "request_password",
    "handle_password_input",
    "handle_stop_load_test",
    "handle_load_status",
    "is_pending_password",
    "is_pending_wizard",
    # Claude
    "handle_claude_menu",
    "handle_claude_input",
    "is_pending_claude",
    # GitLab Webhooks
    "handle_gitlab_webhook",
]
