"""
Audit Service

Single responsibility: High-level audit API.
Integrates with log streaming for SIEM export.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from services.audit.entry import ActorType, AuditAction, AuditEntry, AuditQuery
from services.audit.hasher import AuditHasher
from services.audit.repository import ImmutableAuditRepository
from services.audit.verifier import AuditVerifier, VerificationResult

logger = logging.getLogger(__name__)

# Log streaming integration (lazy import to avoid circular deps)
_log_stream_manager = None


def _get_log_stream_manager():
    """Get log stream manager lazily."""
    global _log_stream_manager
    if _log_stream_manager is None:
        try:
            from services.observability.log_streaming import get_log_stream_manager
            _log_stream_manager = get_log_stream_manager()
        except ImportError:
            logger.debug("Log streaming not available")
    return _log_stream_manager


def _audit_entry_to_log_event(entry: AuditEntry):
    """Convert AuditEntry to LogEvent for streaming."""
    try:
        from services.observability.log_streaming import LogEvent, LogLevel, LogCategory

        # Map audit action to log level
        level = LogLevel.INFO
        if entry.action in (AuditAction.DELETE, AuditAction.REVOKE):
            level = LogLevel.WARNING
        elif entry.action == AuditAction.LOGIN_FAILED:
            level = LogLevel.WARNING

        return LogEvent(
            timestamp=entry.timestamp,
            level=level,
            category=LogCategory.AUDIT,
            message=f"{entry.action.value} on {entry.resource_type}/{entry.resource_id}",
            event_id=entry.id,
            event_type="audit",
            event_action=entry.action.value,
            source_component="audit",
            actor_id=entry.actor_id,
            actor_type=entry.actor_type.value if hasattr(entry.actor_type, "value") else str(entry.actor_type),
            actor_ip=entry.actor_ip,
            actor_user_agent=entry.actor_user_agent,
            resource_type=entry.resource_type,
            resource_id=entry.resource_id,
            org_id=entry.organization_id,
            execution_id=entry.trace_id,
            trace_id=entry.trace_id,
            outcome="success",
            metadata={
                "sequence_number": entry.sequence_number,
                "entry_hash": entry.entry_hash,
                "change_summary": entry.change_summary,
                **entry.metadata,
            },
            tags=["audit", entry.action.value, entry.resource_type],
        )
    except ImportError:
        return None


class AuditService:
    """
    High-level audit logging operations.

    Provides a simple interface for creating audit entries
    and querying the audit log.
    """

    @staticmethod
    def log(
        action: AuditAction,
        resource_type: str,
        resource_id: str,
        actor_id: str,
        organization_id: str,
        actor_type: ActorType = ActorType.USER,
        old_value: Optional[Dict[str, Any]] = None,
        new_value: Optional[Dict[str, Any]] = None,
        change_summary: Optional[str] = None,
        actor_ip: Optional[str] = None,
        actor_user_agent: Optional[str] = None,
        trace_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create an audit log entry.

        Args:
            action: Action performed
            resource_type: Type of resource
            resource_id: ID of resource
            actor_id: ID of actor
            organization_id: Organization ID
            actor_type: Type of actor
            old_value: Previous state (optional)
            new_value: New state (optional)
            change_summary: Summary of changes
            actor_ip: Actor's IP address
            actor_user_agent: Actor's user agent
            trace_id: Trace ID for distributed tracing
            metadata: Additional metadata

        Returns:
            Entry ID
        """
        # Get sequence number and previous hash
        last_entry = ImmutableAuditRepository.get_last_entry(organization_id)

        if last_entry:
            sequence_number = last_entry.sequence_number + 1
            prev_hash = last_entry.entry_hash
        else:
            sequence_number = 1
            prev_hash = AuditHasher.get_genesis_hash()

        # Compute value hashes
        old_value_hash = None
        new_value_hash = None

        if old_value:
            old_value_hash = AuditHasher.compute_value_hash(old_value)
        if new_value:
            new_value_hash = AuditHasher.compute_value_hash(new_value)

        # Create entry
        entry = AuditEntry(
            id=str(uuid4()),
            sequence_number=sequence_number,
            organization_id=organization_id,
            actor_id=actor_id,
            actor_type=actor_type,
            actor_ip=actor_ip,
            actor_user_agent=actor_user_agent,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            old_value_hash=old_value_hash,
            new_value_hash=new_value_hash,
            change_summary=change_summary,
            prev_entry_hash=prev_hash,
            trace_id=trace_id,
            metadata=metadata or {},
        )

        # Compute entry hash
        entry.entry_hash = AuditHasher.compute_entry_hash(entry, prev_hash)

        # Store entry
        ImmutableAuditRepository.append(entry)

        logger.info(
            f"Audit: {action.value} on {resource_type}/{resource_id} "
            f"by {actor_id} (seq={sequence_number})"
        )

        # Push to log stream (non-blocking)
        AuditService._push_to_stream(entry)

        return entry.id

    @staticmethod
    def _push_to_stream(entry: AuditEntry) -> None:
        """
        Push audit entry to log stream (non-blocking).

        Args:
            entry: Audit entry to stream
        """
        try:
            manager = _get_log_stream_manager()
            if manager is None:
                return

            log_event = _audit_entry_to_log_event(entry)
            if log_event is None:
                return

            # Schedule async push without blocking
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(manager.push_buffered(log_event))
            except RuntimeError:
                # No running loop - skip streaming
                pass

        except Exception as e:
            # Log streaming should never break audit logging
            logger.warning(f"Failed to stream audit event: {e}")

    @staticmethod
    def get(entry_id: str) -> Optional[AuditEntry]:
        """Get an entry by ID."""
        return ImmutableAuditRepository.get(entry_id)

    @staticmethod
    def query(
        organization_id: str,
        actor_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """
        Query audit log entries.

        Args:
            organization_id: Organization ID
            actor_id: Filter by actor
            action: Filter by action
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum entries
            offset: Offset for pagination

        Returns:
            List of matching entries
        """
        query = AuditQuery(
            organization_id=organization_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset,
        )

        return ImmutableAuditRepository.query(query)

    @staticmethod
    def verify_integrity(
        organization_id: str,
        start_seq: Optional[int] = None,
        end_seq: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify audit log integrity.

        Args:
            organization_id: Organization ID
            start_seq: Start sequence (optional)
            end_seq: End sequence (optional)

        Returns:
            Verification result
        """
        return AuditVerifier.verify_chain(organization_id, start_seq, end_seq)

    @staticmethod
    def get_resource_history(
        organization_id: str,
        resource_type: str,
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """
        Get audit history for a specific resource.

        Args:
            organization_id: Organization ID
            resource_type: Resource type
            resource_id: Resource ID
            limit: Maximum entries

        Returns:
            List of entries for the resource
        """
        return AuditService.query(
            organization_id=organization_id,
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )

    @staticmethod
    def get_actor_activity(
        organization_id: str,
        actor_id: str,
        limit: int = 100,
    ) -> List[AuditEntry]:
        """
        Get activity for a specific actor.

        Args:
            organization_id: Organization ID
            actor_id: Actor ID
            limit: Maximum entries

        Returns:
            List of entries for the actor
        """
        return AuditService.query(
            organization_id=organization_id,
            actor_id=actor_id,
            limit=limit,
        )

    @staticmethod
    def count(organization_id: str) -> int:
        """Count entries for an organization."""
        return ImmutableAuditRepository.count(organization_id)
