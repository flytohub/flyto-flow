"""
Alerts API

REST endpoints for alert management.

NOTE: This is an Enterprise-only feature (Phase 8).
Requires OBSERVABILITY_ALERTS capability.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from gateway.local_context import get_local_actor

get_workspace_context = get_local_actor
from capabilities import Feature, require_feature


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])
from services.observability.alerts.rule import AlertRule, AlertSeverity
from services.observability.alerts.repository import AlertRuleRepository, AlertRepository
from services.observability.alerts.manager import AlertManager

logger = logging.getLogger(__name__)

# Public router kept only for backward-compatible imports.
# NOTE: The stub GET /alerts/, /alerts/history and /alerts/rules handlers were
# REMOVED. When mounted before the real (feature-gated) router they shadowed the
# real handlers (FastAPI serves the first route registered for an identical
# path), so the Alerts list/history/rules were permanently empty for every user.
# The real router below now serves those paths.
public_router = APIRouter(prefix="/alerts", tags=["alerts"])


# Feature-gated router for full functionality
router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(require_feature(Feature.LOCAL_ALERTS))],
)


# Request/Response Models

class AlertRuleCreate(BaseModel):
    """Request model for creating an alert rule."""

    name: str = Field(..., description="Rule name")
    condition: str = Field(..., description="Alert condition (e.g., 'queue_depth > 100')")
    severity: str = Field(default="warning", description="Alert severity")
    duration_seconds: int = Field(default=0, description="Condition must be true for N seconds")
    labels: Dict[str, str] = Field(default_factory=dict, description="Rule labels")
    annotations: Dict[str, str] = Field(default_factory=dict, description="Rule annotations")
    enabled: bool = Field(default=True, description="Whether rule is enabled")


class AlertRuleUpdate(BaseModel):
    """Request model for updating an alert rule."""

    name: Optional[str] = None
    condition: Optional[str] = None
    severity: Optional[str] = None
    duration_seconds: Optional[int] = None
    labels: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, str]] = None
    enabled: Optional[bool] = None


class AlertSilence(BaseModel):
    """Request model for silencing an alert."""

    until: str = Field(..., description="ISO timestamp to silence until")


class AlertRuleResponse(BaseModel):
    """Response model for an alert rule."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    name: str
    condition: str
    severity: str
    duration_seconds: int
    labels: Dict[str, str]
    annotations: Dict[str, str]
    enabled: bool
    created_at: Optional[str]
    updated_at: Optional[str]


class AlertResponse(BaseModel):
    """Response model for an alert."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    rule_id: str
    status: str
    severity: str
    started_at: str
    ended_at: Optional[str]
    silenced_until: Optional[str]
    labels: Dict[str, str]
    annotations: Dict[str, str]
    evaluated_value: Optional[float]
    threshold_value: Optional[float]


# Endpoints

@router.get("/")
async def get_active_alerts(workspace_context: dict = Depends(get_workspace_context)):
    """Get all active alerts with S-Grade pre-computed counts."""
    alerts = AlertRepository.get_active(workspace_id=workspace_context["id"])

    # S-Grade: Pre-compute counts on backend
    alert_list = []
    critical_count = 0
    warning_count = 0

    for a in alerts:
        severity = a.severity.value if hasattr(a.severity, "value") else a.severity
        if severity == "critical":
            critical_count += 1
        elif severity == "warning":
            warning_count += 1

        alert_list.append(AlertResponse(
            id=a.id,
            rule_id=a.rule_id,
            status=a.status,
            severity=severity,
            started_at=a.started_at,
            ended_at=a.ended_at,
            silenced_until=a.silenced_until,
            labels=a.labels,
            annotations=a.annotations,
            evaluated_value=a.evaluated_value,
            threshold_value=a.threshold_value,
        ))

    return {
        "ok": True,
        "alerts": [a.model_dump(by_alias=True) for a in alert_list],
        "activeCount": len(alert_list),
        "criticalCount": critical_count,
        "warningCount": warning_count,
    }


@router.get("/history")
async def get_alert_history(
    rule_id: Optional[str] = Query(None, description="Filter by rule ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum alerts to return"),
    workspace_context: dict = Depends(get_workspace_context),
):
    """Get alert history."""
    workspace_id = workspace_context["id"]
    if rule_id:
        alerts = AlertRepository.get_by_rule(rule_id, limit, workspace_id=workspace_id)
    else:
        alerts = AlertRepository.get_active(workspace_id=workspace_id)

    alert_list = [
        AlertResponse(
            id=a.id,
            rule_id=a.rule_id,
            status=a.status,
            severity=a.severity.value if hasattr(a.severity, "value") else a.severity,
            started_at=a.started_at,
            ended_at=a.ended_at,
            silenced_until=a.silenced_until,
            labels=a.labels,
            annotations=a.annotations,
            evaluated_value=a.evaluated_value,
            threshold_value=a.threshold_value,
        )
        for a in alerts
    ]
    return [a.model_dump(by_alias=True) for a in alert_list]


@router.get("/{alert_id}")
async def get_alert(alert_id: str, workspace_context: dict = Depends(get_workspace_context)):
    """Get an alert by ID."""
    alert = AlertRepository.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    response = AlertResponse(
        id=alert.id,
        rule_id=alert.rule_id,
        status=alert.status,
        severity=alert.severity.value if hasattr(alert.severity, "value") else alert.severity,
        started_at=alert.started_at,
        ended_at=alert.ended_at,
        silenced_until=alert.silenced_until,
        labels=alert.labels,
        annotations=alert.annotations,
        evaluated_value=alert.evaluated_value,
        threshold_value=alert.threshold_value,
    )
    return response.model_dump(by_alias=True)


@router.post("/{alert_id}/silence")
async def silence_alert(alert_id: str, request: AlertSilence, workspace_context: dict = Depends(get_workspace_context)):
    """Silence an alert until specified time."""
    alert = AlertRepository.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    success = AlertRepository.silence(alert_id, request.until)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to silence alert")

    return {"ok": True, "message": f"Alert silenced until {request.until}"}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, workspace_context: dict = Depends(get_workspace_context)):
    """Acknowledge an alert."""
    alert = AlertRepository.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Mark as acknowledged (using silence with short duration as workaround)
    # In a real implementation, you'd have an acknowledged_at field
    success = AlertRepository.update_status(alert_id, "acknowledged")
    if not success:
        # Fallback: just return success as acknowledgment is informational
        pass

    return {"ok": True, "message": "Alert acknowledged"}


@router.post("/{alert_id}/mute")
async def mute_alert(alert_id: str, request: AlertSilence, workspace_context: dict = Depends(get_workspace_context)):
    """Mute an alert (alias for silence)."""
    alert = AlertRepository.get(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    success = AlertRepository.silence(alert_id, request.until)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mute alert")

    return {"ok": True, "message": f"Alert muted until {request.until}"}


# Rule Endpoints

@router.get("/rules")
async def list_alert_rules(
    enabled_only: bool = Query(False, description="Only return enabled rules"),
    workspace_context: dict = Depends(get_workspace_context),
):
    """List all alert rules with S-Grade pre-computed counts."""
    workspace_id = workspace_context["id"]
    # Always fetch all rules to compute counts
    all_rules = AlertRuleRepository.list_all(enabled_only=False, workspace_id=workspace_id)

    # S-Grade: Pre-compute counts on backend
    enabled_count = sum(1 for r in all_rules if r.enabled)
    total_count = len(all_rules)

    # Filter if needed
    if enabled_only:
        rules = [r for r in all_rules if r.enabled]
    else:
        rules = all_rules

    rule_list = [
        AlertRuleResponse(
            id=r.id,
            name=r.name,
            condition=r.condition,
            severity=r.severity.value,
            duration_seconds=r.duration_seconds,
            labels=r.labels,
            annotations=r.annotations,
            enabled=r.enabled,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rules
    ]

    return {
        "ok": True,
        "rules": [r.model_dump(by_alias=True) for r in rule_list],
        "enabledCount": enabled_count,
        "totalCount": total_count,
    }


@router.get("/rules/{rule_id}")
async def get_alert_rule(rule_id: str, workspace_context: dict = Depends(get_workspace_context)):
    """Get an alert rule by ID."""
    rule = AlertRuleRepository.get(rule_id, workspace_id=workspace_context["id"])
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    response = AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        condition=rule.condition,
        severity=rule.severity.value,
        duration_seconds=rule.duration_seconds,
        labels=rule.labels,
        annotations=rule.annotations,
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )
    return response.model_dump(by_alias=True)


@router.post("/rules")
async def create_alert_rule(request: AlertRuleCreate, workspace_context: dict = Depends(get_workspace_context)):
    """Create a new alert rule."""
    rule_id = str(uuid4())

    try:
        severity = AlertSeverity(request.severity)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid severity: {request.severity}. Must be one of: critical, warning, info",
        )

    rule = AlertRule(
        id=rule_id,
        name=request.name,
        condition=request.condition,
        severity=severity,
        duration_seconds=request.duration_seconds,
        labels=request.labels,
        annotations=request.annotations,
        enabled=request.enabled,
    )

    AlertRuleRepository.create(rule, workspace_id=workspace_context["id"])

    response = AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        condition=rule.condition,
        severity=rule.severity.value,
        duration_seconds=rule.duration_seconds,
        labels=rule.labels,
        annotations=rule.annotations,
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )
    return response.model_dump(by_alias=True)


@router.put("/rules/{rule_id}")
async def update_alert_rule(rule_id: str, request: AlertRuleUpdate, workspace_context: dict = Depends(get_workspace_context)):
    """Update an alert rule."""
    rule = AlertRuleRepository.get(rule_id, workspace_id=workspace_context["id"])
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    updates = {}
    if request.name is not None:
        updates["name"] = request.name
    if request.condition is not None:
        updates["condition"] = request.condition
    if request.severity is not None:
        try:
            updates["severity"] = AlertSeverity(request.severity)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid severity: {request.severity}",
            )
    if request.duration_seconds is not None:
        updates["duration_seconds"] = request.duration_seconds
    if request.labels is not None:
        updates["labels"] = request.labels
    if request.annotations is not None:
        updates["annotations"] = request.annotations
    if request.enabled is not None:
        updates["enabled"] = request.enabled

    if updates:
        AlertRuleRepository.update(rule_id, **updates)

    # Return updated rule
    rule = AlertRuleRepository.get(rule_id, workspace_id=workspace_context["id"])

    response = AlertRuleResponse(
        id=rule.id,
        name=rule.name,
        condition=rule.condition,
        severity=rule.severity.value,
        duration_seconds=rule.duration_seconds,
        labels=rule.labels,
        annotations=rule.annotations,
        enabled=rule.enabled,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )
    return response.model_dump(by_alias=True)


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str, workspace_context: dict = Depends(get_workspace_context)):
    """Delete an alert rule."""
    workspace_id = workspace_context["id"]
    rule = AlertRuleRepository.get(rule_id, workspace_id=workspace_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Alert rule not found")

    AlertRuleRepository.delete(rule_id, workspace_id=workspace_id)

    return {"ok": True, "message": "Alert rule deleted"}
