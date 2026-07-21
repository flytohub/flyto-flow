"""
Audit Verifier

Single responsibility: Verify audit log integrity.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from services.audit.entry import AuditEntry
from services.audit.hasher import AuditHasher
from services.audit.repository import ImmutableAuditRepository

logger = logging.getLogger(__name__)


@dataclass
class TamperingReport:
    """Report of detected tampering."""

    sequence_number: int
    entry_id: str
    issue_type: str  # hash_mismatch, chain_break, sequence_gap
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    description: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "sequence_number": self.sequence_number,
            "entry_id": self.entry_id,
            "issue_type": self.issue_type,
            "expected_value": self.expected_value,
            "actual_value": self.actual_value,
            "description": self.description,
        }


@dataclass
class VerificationResult:
    """Result of integrity verification."""

    organization_id: str
    verified_at: str
    is_valid: bool = True
    entries_checked: int = 0
    start_sequence: int = 0
    end_sequence: int = 0
    tampering_reports: List[TamperingReport] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "organization_id": self.organization_id,
            "verified_at": self.verified_at,
            "is_valid": self.is_valid,
            "entries_checked": self.entries_checked,
            "start_sequence": self.start_sequence,
            "end_sequence": self.end_sequence,
            "tampering_reports": [r.to_dict() for r in self.tampering_reports],
            "error": self.error,
        }


class AuditVerifier:
    """
    Verify audit log integrity.

    Checks:
    - Hash chain continuity
    - Entry hash validity
    - Sequence number continuity
    """

    @classmethod
    def verify_chain(
        cls,
        organization_id: str,
        start_seq: Optional[int] = None,
        end_seq: Optional[int] = None,
    ) -> VerificationResult:
        """
        Verify audit chain integrity.

        Args:
            organization_id: Organization ID
            start_seq: Start sequence (default: 1)
            end_seq: End sequence (default: latest)

        Returns:
            Verification result
        """
        result = VerificationResult(
            organization_id=organization_id,
            verified_at=datetime.now(timezone.utc).isoformat(),
        )

        try:
            # Get the range to verify
            last_entry = ImmutableAuditRepository.get_last_entry(organization_id)
            if not last_entry:
                result.entries_checked = 0
                return result

            if start_seq is None:
                start_seq = 1
            if end_seq is None:
                end_seq = last_entry.sequence_number

            result.start_sequence = start_seq
            result.end_sequence = end_seq

            # Get all entries in range
            entries = ImmutableAuditRepository.get_range(
                organization_id, start_seq, end_seq
            )

            if not entries:
                result.entries_checked = 0
                return result

            result.entries_checked = len(entries)

            # Verify the chain
            prev_entry: Optional[AuditEntry] = None

            # For first entry, get the actual previous if not starting from 1
            if start_seq > 1:
                prev_entry = ImmutableAuditRepository.get_by_sequence(
                    organization_id, start_seq - 1
                )

            for entry in entries:
                # Check sequence continuity
                if prev_entry:
                    expected_seq = prev_entry.sequence_number + 1
                    if entry.sequence_number != expected_seq:
                        result.is_valid = False
                        result.tampering_reports.append(TamperingReport(
                            sequence_number=entry.sequence_number,
                            entry_id=entry.id,
                            issue_type="sequence_gap",
                            expected_value=str(expected_seq),
                            actual_value=str(entry.sequence_number),
                            description=f"Gap in sequence: expected {expected_seq}, got {entry.sequence_number}",
                        ))

                # Verify entry hash
                if not AuditHasher.verify_entry_hash(entry):
                    result.is_valid = False
                    expected_hash = AuditHasher.compute_entry_hash(
                        entry, entry.prev_entry_hash
                    )
                    result.tampering_reports.append(TamperingReport(
                        sequence_number=entry.sequence_number,
                        entry_id=entry.id,
                        issue_type="hash_mismatch",
                        expected_value=expected_hash,
                        actual_value=entry.entry_hash,
                        description="Entry hash does not match computed hash",
                    ))

                # Verify chain link
                if prev_entry:
                    if entry.prev_entry_hash != prev_entry.entry_hash:
                        result.is_valid = False
                        result.tampering_reports.append(TamperingReport(
                            sequence_number=entry.sequence_number,
                            entry_id=entry.id,
                            issue_type="chain_break",
                            expected_value=prev_entry.entry_hash,
                            actual_value=entry.prev_entry_hash,
                            description="Chain link broken: prev_entry_hash does not match previous entry",
                        ))
                else:
                    # First entry should have genesis hash or previous entry hash
                    if entry.sequence_number == 1:
                        if entry.prev_entry_hash != AuditHasher.get_genesis_hash():
                            result.is_valid = False
                            result.tampering_reports.append(TamperingReport(
                                sequence_number=entry.sequence_number,
                                entry_id=entry.id,
                                issue_type="chain_break",
                                expected_value=AuditHasher.get_genesis_hash(),
                                actual_value=entry.prev_entry_hash,
                                description="First entry does not have genesis hash",
                            ))

                prev_entry = entry

        except Exception as e:
            result.is_valid = False
            result.error = str(e)
            logger.error(f"Verification failed: {e}")

        return result

    @classmethod
    def verify_entry(cls, entry: AuditEntry) -> bool:
        """
        Verify a single entry's hash.

        Args:
            entry: Entry to verify

        Returns:
            True if valid
        """
        return AuditHasher.verify_entry_hash(entry)

    @classmethod
    def find_tampering(cls, organization_id: str) -> List[TamperingReport]:
        """
        Find all tampering in an organization's audit log.

        Args:
            organization_id: Organization ID

        Returns:
            List of tampering reports
        """
        result = cls.verify_chain(organization_id)
        return result.tampering_reports

    @classmethod
    def quick_check(cls, organization_id: str) -> bool:
        """
        Quick integrity check (last N entries).

        Args:
            organization_id: Organization ID

        Returns:
            True if recent entries are valid
        """
        last_entry = ImmutableAuditRepository.get_last_entry(organization_id)
        if not last_entry:
            return True

        # Check last 10 entries
        start_seq = max(1, last_entry.sequence_number - 9)
        result = cls.verify_chain(organization_id, start_seq)

        return result.is_valid
