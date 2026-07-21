"""
Collaboration Notifications Helper

Sends notifications for PR and Issue collaboration events.
Uses the existing notification_provider.create_notification() pattern.
"""

import logging
from typing import Optional

from gateway.providers.data.models.notification import NotificationType, NotificationCreateDTO

logger = logging.getLogger(__name__)


async def _send(provider, dto: NotificationCreateDTO):
    """Send a notification, swallowing errors to avoid breaking the main flow."""
    try:
        await provider.create_notification(dto)
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")


async def notify_pr_created(
    notification_provider,
    template_owner_id: str,
    pr_author_id: str,
    pr_author_name: str,
    pr_title: str,
    template_id: str,
    pr_id: str,
):
    """Notify template owner when a new PR is created."""
    if template_owner_id == pr_author_id:
        return  # Don't notify yourself

    await _send(notification_provider, NotificationCreateDTO(
        user_id=template_owner_id,
        notification_type=NotificationType.PR_CREATED,
        title="New Pull Request",
        message=f"{pr_author_name} submitted a pull request: {pr_title}",
        reference_id=pr_id,
        reference_type="pull_request",
        actor_id=pr_author_id,
    ))


async def notify_pr_reviewed(
    notification_provider,
    pr_author_id: str,
    reviewer_id: str,
    reviewer_name: str,
    action: str,
    pr_title: str,
    template_id: str,
    pr_id: str,
):
    """Notify PR author when their PR is reviewed."""
    if pr_author_id == reviewer_id:
        return

    verb = "approved" if action == "approve" else "requested changes on"
    await _send(notification_provider, NotificationCreateDTO(
        user_id=pr_author_id,
        notification_type=NotificationType.PR_REVIEWED,
        title=f"PR {action.capitalize()}d",
        message=f"{reviewer_name} {verb} your pull request: {pr_title}",
        reference_id=pr_id,
        reference_type="pull_request",
        actor_id=reviewer_id,
    ))


async def notify_pr_merged(
    notification_provider,
    pr_author_id: str,
    merger_id: str,
    merger_name: str,
    pr_title: str,
    template_id: str,
    pr_id: str,
):
    """Notify PR author when their PR is merged."""
    if pr_author_id == merger_id:
        return

    await _send(notification_provider, NotificationCreateDTO(
        user_id=pr_author_id,
        notification_type=NotificationType.PR_MERGED,
        title="PR Merged",
        message=f"{merger_name} merged your pull request: {pr_title}",
        reference_id=pr_id,
        reference_type="pull_request",
        actor_id=merger_id,
    ))


async def notify_pr_commented(
    notification_provider,
    pr_author_id: str,
    commenter_id: str,
    commenter_name: str,
    pr_title: str,
    template_id: str,
    pr_id: str,
):
    """Notify PR author when someone comments on their PR."""
    if pr_author_id == commenter_id:
        return

    await _send(notification_provider, NotificationCreateDTO(
        user_id=pr_author_id,
        notification_type=NotificationType.PR_COMMENTED,
        title="New Comment on PR",
        message=f"{commenter_name} commented on your pull request: {pr_title}",
        reference_id=pr_id,
        reference_type="pull_request",
        actor_id=commenter_id,
    ))


async def notify_issue_commented(
    notification_provider,
    issue_author_id: str,
    commenter_id: str,
    commenter_name: str,
    issue_title: str,
    template_id: str,
    issue_id: str,
):
    """Notify issue author when someone comments on their issue."""
    if issue_author_id == commenter_id:
        return

    await _send(notification_provider, NotificationCreateDTO(
        user_id=issue_author_id,
        notification_type=NotificationType.ISSUE_COMMENTED,
        title="New Comment on Issue",
        message=f"{commenter_name} commented on your issue: {issue_title}",
        reference_id=issue_id,
        reference_type="template_issue",
        actor_id=commenter_id,
    ))


async def notify_collab_requested(
    notification_provider,
    template_owner_id: str,
    requester_id: str,
    requester_name: str,
    template_name: str,
    template_id: str,
    request_id: str,
    message: str = "",
):
    """Notify template owner when someone requests collaboration access."""
    if template_owner_id == requester_id:
        return

    body = f"{requester_name} requested collaboration access to {template_name}"
    if message:
        body += f": \"{message}\""

    await _send(notification_provider, NotificationCreateDTO(
        user_id=template_owner_id,
        notification_type=NotificationType.COLLAB_REQUESTED,
        title="Collaboration Request",
        message=body,
        reference_id=request_id,
        reference_type="collab_request",
        actor_id=requester_id,
    ))


async def notify_collab_resolved(
    notification_provider,
    requester_id: str,
    resolver_id: str,
    resolver_name: str,
    template_name: str,
    template_id: str,
    request_id: str,
    approved: bool,
):
    """Notify requester when their collaboration request is approved or rejected."""
    if requester_id == resolver_id:
        return

    if approved:
        ntype = NotificationType.COLLAB_APPROVED
        title = "Collaboration Approved"
        body = f"{resolver_name} approved your collaboration request for {template_name}"
    else:
        ntype = NotificationType.COLLAB_REJECTED
        title = "Collaboration Declined"
        body = f"{resolver_name} declined your collaboration request for {template_name}"

    await _send(notification_provider, NotificationCreateDTO(
        user_id=requester_id,
        notification_type=ntype,
        title=title,
        message=body,
        reference_id=template_id,
        reference_type="template",
        actor_id=resolver_id,
    ))


async def notify_issue_closed(
    notification_provider,
    issue_author_id: str,
    closer_id: str,
    closer_name: str,
    issue_title: str,
    template_id: str,
    issue_id: str,
):
    """Notify issue author when their issue is closed."""
    if issue_author_id == closer_id:
        return

    await _send(notification_provider, NotificationCreateDTO(
        user_id=issue_author_id,
        notification_type=NotificationType.ISSUE_CLOSED,
        title="Issue Closed",
        message=f"{closer_name} closed your issue: {issue_title}",
        reference_id=issue_id,
        reference_type="template_issue",
        actor_id=closer_id,
    ))
