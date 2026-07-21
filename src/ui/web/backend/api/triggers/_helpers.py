"""
Shared helpers for trigger routes — provider accessors, ownership checks, utilities.
"""

import logging
from typing import Any, Dict

from api.errors import not_found
from services.infra.scheduler.cron_parser import CronParser

logger = logging.getLogger(__name__)


# ============================================================================
# Provider Access
# ============================================================================


def _get_webhook_provider():
    from gateway.providers.hub import get_webhook_provider
    return get_webhook_provider()


def _get_schedule_provider():
    from gateway.providers.hub import get_schedule_provider
    return get_schedule_provider()


# ============================================================================
# Helper Functions
# ============================================================================


def _build_workflow_yaml(workflow) -> str:
    """Convert workflow model to YAML for execution."""
    import yaml
    from api.workflows.utils import normalize_template_module

    steps = []
    for node in sorted(workflow.nodes or [], key=lambda n: n.order_index):
        module_id, node_params = normalize_template_module(node.module_id, node.params)
        step = {"id": node.id, "module": module_id, "label": node.label, **node_params}
        node_dict = node.dict() if hasattr(node, 'dict') else node.__dict__
        if node_dict.get("connections"):
            step["connections"] = node_dict["connections"]
        steps.append(step)

    workflow_data = {"name": workflow.name, "steps": steps}
    return yaml.dump(workflow_data, allow_unicode=True)


def get_webhook_url(webhook_id: str) -> str:
    """Generate the webhook trigger URL."""
    return f"/api/triggers/webhooks/{webhook_id}/trigger"


def _verify_schedule_owner(schedule_data: Dict[str, Any], user_id: str) -> None:
    """Verify the current user owns this schedule."""
    if schedule_data.get("user_id") and schedule_data["user_id"] != user_id:
        not_found("Schedule not found")


def _verify_webhook_owner(webhook_data: Dict[str, Any], user_id: str) -> None:
    """Verify the current user owns this webhook."""
    if webhook_data.get("user_id") and webhook_data["user_id"] != user_id:
        not_found("Webhook not found")


def _calculate_next_run(schedule_data: Dict[str, Any]):
    """Calculate next run time for a schedule."""
    from datetime import datetime, timezone, timedelta
    cron = schedule_data.get("cron_expression")
    interval = schedule_data.get("interval_seconds")
    tz = schedule_data.get("timezone", "UTC")
    if cron:
        return CronParser.get_next_run(cron, timezone_str=tz)
    elif interval:
        return datetime.now(timezone.utc) + timedelta(seconds=interval)
    return None
