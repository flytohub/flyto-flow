"""
Security Checker

Single responsibility: Analyze audit logs for security issues.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List

from services.audit.entry import AuditAction, AuditEntry, AuditQuery
from services.audit.repository import ImmutableAuditRepository
from services.audit.verifier import AuditVerifier, VerificationResult

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FindingType(Enum):
    """Type of security finding"""
    TAMPERING_DETECTED = "tampering_detected"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    PERMISSION_VIOLATION = "permission_violation"
    CREDENTIAL_EXPOSURE = "credential_exposure"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    UNUSUAL_ACCESS_PATTERN = "unusual_access_pattern"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"


@dataclass
class SecurityFinding:
    """A security finding from analysis"""
    finding_type: FindingType
    risk_level: RiskLevel
    title: str
    description: str
    affected_entries: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    detected_at: str = ""

    def __post_init__(self):
        """Set detected_at to current UTC time if not provided."""
        if not self.detected_at:
            self.detected_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "finding_type": self.finding_type.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "affected_entries": self.affected_entries,
            "recommendations": self.recommendations,
            "metadata": self.metadata,
            "detected_at": self.detected_at,
        }


class SecurityChecker:
    """
    Analyze audit logs for security issues.

    Checks:
    - Hash chain integrity (tampering)
    - Suspicious activity patterns
    - Permission violations
    - Credential usage
    - Unusual access patterns
    """

    # Thresholds for anomaly detection
    FAILED_LOGIN_THRESHOLD = 5  # Failed logins in window
    FAILED_LOGIN_WINDOW_MINUTES = 15
    BULK_DELETE_THRESHOLD = 10  # Bulk deletions
    AFTER_HOURS_START = 22  # 10 PM
    AFTER_HOURS_END = 6  # 6 AM
    UNUSUAL_VOLUME_MULTIPLIER = 3  # 3x normal activity

    @classmethod
    def check_integrity(cls, organization_id: str) -> VerificationResult:
        """
        Check audit log integrity.

        Args:
            organization_id: Organization to check

        Returns:
            VerificationResult with integrity status
        """
        return AuditVerifier.verify_chain(organization_id)

    @classmethod
    def check_suspicious_activity(
        cls,
        organization_id: str,
        hours_back: int = 24,
    ) -> List[SecurityFinding]:
        """
        Check for suspicious activity patterns.

        Patterns:
        - Failed login attempts (brute force)
        - Bulk deletions
        - After-hours access
        - Unusual activity volume

        Args:
            organization_id: Organization to check
            hours_back: Hours of history to analyze

        Returns:
            List of security findings
        """
        findings = []
        start_time = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()

        # Get relevant entries
        query = AuditQuery(
            organization_id=organization_id,
            start_time=start_time,
            limit=10000,
        )
        entries = ImmutableAuditRepository.query(query)

        if not entries:
            return findings

        # Check for failed logins (brute force)
        failed_logins = cls._find_brute_force_attempts(entries)
        findings.extend(failed_logins)

        # Check for bulk deletions
        bulk_deletes = cls._find_bulk_deletions(entries)
        findings.extend(bulk_deletes)

        # Check for after-hours access
        after_hours = cls._find_after_hours_access(entries)
        findings.extend(after_hours)

        return findings

    @classmethod
    def _find_brute_force_attempts(
        cls,
        entries: List[AuditEntry],
    ) -> List[SecurityFinding]:
        """Find potential brute force login attempts."""
        findings = []

        # Group by actor and time window
        login_failures: Dict[str, List[AuditEntry]] = {}

        for entry in entries:
            if entry.action == AuditAction.LOGIN_FAILED:
                key = entry.actor_id
                if key not in login_failures:
                    login_failures[key] = []
                login_failures[key].append(entry)

        # Check each actor for threshold violation
        for actor_id, failed_entries in login_failures.items():
            if len(failed_entries) >= cls.FAILED_LOGIN_THRESHOLD:
                findings.append(SecurityFinding(
                    finding_type=FindingType.BRUTE_FORCE_ATTEMPT,
                    risk_level=RiskLevel.HIGH,
                    title=f"Brute Force Attempt Detected - {actor_id}",
                    description=f"{len(failed_entries)} failed login attempts detected",
                    affected_entries=[e.id for e in failed_entries],
                    recommendations=[
                        "Block the source IP temporarily",
                        "Require password reset if account exists",
                        "Enable 2FA for the account",
                        "Review IP reputation",
                    ],
                    metadata={
                        "actor_id": actor_id,
                        "attempt_count": len(failed_entries),
                        "ips": list(set(e.actor_ip for e in failed_entries if e.actor_ip)),
                    },
                ))

        return findings

    @classmethod
    def _find_bulk_deletions(
        cls,
        entries: List[AuditEntry],
    ) -> List[SecurityFinding]:
        """Find bulk deletion activity."""
        findings = []

        # Group deletions by actor
        deletions: Dict[str, List[AuditEntry]] = {}

        for entry in entries:
            if entry.action == AuditAction.DELETE:
                key = entry.actor_id
                if key not in deletions:
                    deletions[key] = []
                deletions[key].append(entry)

        # Check each actor for threshold violation
        for actor_id, del_entries in deletions.items():
            if len(del_entries) >= cls.BULK_DELETE_THRESHOLD:
                findings.append(SecurityFinding(
                    finding_type=FindingType.DATA_EXFILTRATION,
                    risk_level=RiskLevel.HIGH,
                    title=f"Bulk Deletion Detected - {actor_id}",
                    description=f"{len(del_entries)} deletions by single actor",
                    affected_entries=[e.id for e in del_entries],
                    recommendations=[
                        "Review if deletions were authorized",
                        "Check for data backup availability",
                        "Interview the user if legitimate",
                    ],
                    metadata={
                        "actor_id": actor_id,
                        "deletion_count": len(del_entries),
                        "resource_types": list(set(e.resource_type for e in del_entries)),
                    },
                ))

        return findings

    @classmethod
    def _find_after_hours_access(
        cls,
        entries: List[AuditEntry],
    ) -> List[SecurityFinding]:
        """Find after-hours access patterns."""
        findings = []
        after_hours_entries: List[AuditEntry] = []

        for entry in entries:
            if entry.timestamp:
                try:
                    ts = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
                    hour = ts.hour
                    if hour >= cls.AFTER_HOURS_START or hour < cls.AFTER_HOURS_END:
                        after_hours_entries.append(entry)
                except Exception:
                    pass

        # Only flag if there's significant after-hours activity
        if len(after_hours_entries) >= 10:
            actors = list(set(e.actor_id for e in after_hours_entries))
            findings.append(SecurityFinding(
                finding_type=FindingType.UNUSUAL_ACCESS_PATTERN,
                risk_level=RiskLevel.MEDIUM,
                title="After-Hours Access Detected",
                description=f"{len(after_hours_entries)} actions performed after normal hours",
                affected_entries=[e.id for e in after_hours_entries[:20]],  # Limit
                recommendations=[
                    "Verify if after-hours access is expected",
                    "Review the specific actions performed",
                    "Consider time-based access controls",
                ],
                metadata={
                    "entry_count": len(after_hours_entries),
                    "actors": actors[:10],
                },
            ))

        return findings

    @classmethod
    def check_permission_violations(
        cls,
        organization_id: str,
        hours_back: int = 24,
    ) -> List[SecurityFinding]:
        """
        Check for permission violations.

        Args:
            organization_id: Organization to check
            hours_back: Hours of history to analyze

        Returns:
            List of security findings
        """
        findings = []
        start_time = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()

        # Look for permission denied events
        query = AuditQuery(
            organization_id=organization_id,
            action=AuditAction.ACCESS_DENIED,
            start_time=start_time,
            limit=1000,
        )
        denied_entries = ImmutableAuditRepository.query(query)

        if len(denied_entries) >= 5:
            # Group by actor
            by_actor: Dict[str, int] = {}
            for entry in denied_entries:
                by_actor[entry.actor_id] = by_actor.get(entry.actor_id, 0) + 1

            # Find actors with multiple denials
            for actor_id, count in by_actor.items():
                if count >= 3:
                    findings.append(SecurityFinding(
                        finding_type=FindingType.PERMISSION_VIOLATION,
                        risk_level=RiskLevel.MEDIUM,
                        title=f"Multiple Permission Denials - {actor_id}",
                        description=f"User attempted {count} unauthorized actions",
                        affected_entries=[e.id for e in denied_entries if e.actor_id == actor_id],
                        recommendations=[
                            "Review if user needs additional permissions",
                            "Verify this is the correct user account",
                            "Check for credential compromise",
                        ],
                        metadata={
                            "actor_id": actor_id,
                            "denial_count": count,
                        },
                    ))

        return findings

    @classmethod
    def check_credentials(
        cls,
        organization_id: str,
        hours_back: int = 24,
    ) -> List[SecurityFinding]:
        """
        Analyze credential usage.

        Args:
            organization_id: Organization to check
            hours_back: Hours of history to analyze

        Returns:
            List of security findings
        """
        findings = []
        start_time = (datetime.now(timezone.utc) - timedelta(hours=hours_back)).isoformat()

        # Look for credential-related events
        query = AuditQuery(
            organization_id=organization_id,
            resource_type="credential",
            start_time=start_time,
            limit=1000,
        )
        cred_entries = ImmutableAuditRepository.query(query)

        # Check for credential access patterns
        read_count = sum(1 for e in cred_entries if e.action == AuditAction.READ)
        if read_count >= 20:
            findings.append(SecurityFinding(
                finding_type=FindingType.CREDENTIAL_EXPOSURE,
                risk_level=RiskLevel.MEDIUM,
                title="High Credential Access Volume",
                description=f"{read_count} credential read operations detected",
                recommendations=[
                    "Review if credential access is expected",
                    "Audit which credentials were accessed",
                    "Consider rotating sensitive credentials",
                ],
                metadata={"read_count": read_count},
            ))

        return findings

    @classmethod
    def quick_check(cls, organization_id: str) -> Dict[str, Any]:
        """
        Quick security health check.

        Args:
            organization_id: Organization to check

        Returns:
            Quick health status
        """
        # Quick integrity check
        is_valid = AuditVerifier.quick_check(organization_id)

        # Recent entry count
        entry_count = ImmutableAuditRepository.count(organization_id)

        # Last entry timestamp
        last_entry = ImmutableAuditRepository.get_last_entry(organization_id)
        last_timestamp = last_entry.timestamp if last_entry else None

        return {
            "organization_id": organization_id,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "integrity_valid": is_valid,
            "total_entries": entry_count,
            "last_entry_at": last_timestamp,
            "status": "healthy" if is_valid else "compromised",
        }
