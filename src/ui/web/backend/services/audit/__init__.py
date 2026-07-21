"""
Audit Service

Provides immutable audit logging with hash chain integrity,
plus a lightweight CRUD audit logger for fire-and-forget use.
"""

# Lightweight CRUD logger — always available (no heavy deps)
from services.audit.crud_logger import log_crud

# Full audit service — requires gateway.storage (SQLite), may not be
# available in all environments (e.g. unit tests without DB setup).
try:
    from services.audit.entry import AuditEntry, AuditAction, ActorType
    from services.audit.hasher import AuditHasher
    from services.audit.repository import ImmutableAuditRepository
    from services.audit.verifier import AuditVerifier, VerificationResult
    from services.audit.service import AuditService
    from services.audit.archiver import AuditArchiver
except ImportError:
    pass

__all__ = [
    "log_crud",
    "AuditEntry",
    "AuditAction",
    "ActorType",
    "AuditHasher",
    "ImmutableAuditRepository",
    "AuditVerifier",
    "VerificationResult",
    "AuditService",
    "AuditArchiver",
]
