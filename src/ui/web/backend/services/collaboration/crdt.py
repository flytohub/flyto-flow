"""
CRDT Implementation

Conflict-free Replicated Data Types for real-time collaboration.
Implements a JSON CRDT for workflow document synchronization.

Features:
- Operation-based CRDT
- Vector clocks for causality
- Automatic conflict resolution
- Undo/redo support
"""

import copy
import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Types of CRDT operations."""
    INSERT = "insert"
    DELETE = "delete"
    UPDATE = "update"
    MOVE = "move"
    SET = "set"


@dataclass
class VectorClock:
    """
    Vector clock for tracking causality.

    Each participant has a logical clock that increments with each operation.
    """
    clocks: Dict[str, int] = field(default_factory=dict)

    def increment(self, participant_id: str) -> "VectorClock":
        """Increment clock for participant."""
        new_clocks = self.clocks.copy()
        new_clocks[participant_id] = new_clocks.get(participant_id, 0) + 1
        return VectorClock(clocks=new_clocks)

    def get(self, participant_id: str) -> int:
        """Get clock value for participant."""
        return self.clocks.get(participant_id, 0)

    def merge(self, other: "VectorClock") -> "VectorClock":
        """Merge two vector clocks (take max of each)."""
        all_keys = set(self.clocks.keys()) | set(other.clocks.keys())
        merged = {
            k: max(self.clocks.get(k, 0), other.clocks.get(k, 0))
            for k in all_keys
        }
        return VectorClock(clocks=merged)

    def happens_before(self, other: "VectorClock") -> bool:
        """Check if this clock happens before another."""
        if not self.clocks:
            return bool(other.clocks)

        all_keys = set(self.clocks.keys()) | set(other.clocks.keys())
        at_least_one_less = False

        for k in all_keys:
            self_val = self.clocks.get(k, 0)
            other_val = other.clocks.get(k, 0)

            if self_val > other_val:
                return False
            if self_val < other_val:
                at_least_one_less = True

        return at_least_one_less

    def concurrent_with(self, other: "VectorClock") -> bool:
        """Check if two clocks are concurrent (neither happens before the other)."""
        return not self.happens_before(other) and not other.happens_before(self)

    def to_dict(self) -> Dict[str, int]:
        """Serialize vector clock to dictionary."""
        return self.clocks.copy()

    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> "VectorClock":
        """Deserialize vector clock from dictionary."""
        return cls(clocks=data.copy())


@dataclass
class CRDTOperation:
    """
    A single CRDT operation.

    Operations are immutable and identified by their unique ID.
    """
    operation_id: str
    operation_type: OperationType
    path: List[Union[str, int]]  # JSON path to target
    value: Any = None
    old_value: Any = None  # For undo
    participant_id: str = ""
    timestamp: str = ""
    vector_clock: VectorClock = field(default_factory=VectorClock)
    dependencies: List[str] = field(default_factory=list)  # Operation IDs this depends on

    def __post_init__(self):
        """Set default timestamp and generate operation ID if missing."""
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if not self.operation_id:
            self.operation_id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate unique operation ID."""
        content = f"{self.participant_id}:{self.timestamp}:{self.operation_type}:{self.path}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize operation to dictionary."""
        return {
            "operation_id": self.operation_id,
            "operation_type": self.operation_type.value,
            "path": self.path,
            "value": self.value,
            "old_value": self.old_value,
            "participant_id": self.participant_id,
            "timestamp": self.timestamp,
            "vector_clock": self.vector_clock.to_dict(),
            "dependencies": self.dependencies,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CRDTOperation":
        """Deserialize operation from dictionary."""
        return cls(
            operation_id=data["operation_id"],
            operation_type=OperationType(data["operation_type"]),
            path=data["path"],
            value=data.get("value"),
            old_value=data.get("old_value"),
            participant_id=data.get("participant_id", ""),
            timestamp=data.get("timestamp", ""),
            vector_clock=VectorClock.from_dict(data.get("vector_clock", {})),
            dependencies=data.get("dependencies", []),
        )

    def inverse(self) -> "CRDTOperation":
        """Create inverse operation for undo."""
        if self.operation_type == OperationType.INSERT:
            return CRDTOperation(
                operation_id="",
                operation_type=OperationType.DELETE,
                path=self.path,
                value=self.value,
                participant_id=self.participant_id,
            )
        elif self.operation_type == OperationType.DELETE:
            return CRDTOperation(
                operation_id="",
                operation_type=OperationType.INSERT,
                path=self.path,
                value=self.old_value,
                participant_id=self.participant_id,
            )
        elif self.operation_type in [OperationType.UPDATE, OperationType.SET]:
            return CRDTOperation(
                operation_id="",
                operation_type=self.operation_type,
                path=self.path,
                value=self.old_value,
                old_value=self.value,
                participant_id=self.participant_id,
            )
        return self


class CRDTDocument:
    """
    CRDT document for collaborative editing.

    Implements an operation-based JSON CRDT with:
    - Ordered operation log
    - Vector clock causality tracking
    - Automatic conflict resolution
    - Undo/redo support

    Usage:
        doc = CRDTDocument(document_id="workflow_123")

        # Apply operation
        op = doc.create_operation(
            operation_type=OperationType.SET,
            path=["steps", 0, "name"],
            value="New Step Name",
            participant_id="user_1",
        )
        doc.apply_operation(op)

        # Get current state
        state = doc.get_state()

        # Merge remote operations
        doc.merge_operations(remote_ops)
    """

    def __init__(
        self,
        document_id: str,
        initial_state: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize CRDT document.

        Args:
            document_id: Unique document identifier
            initial_state: Initial document state
        """
        self.document_id = document_id
        self._state = initial_state or {}
        self._operations: List[CRDTOperation] = []
        self._applied_ids: Set[str] = set()
        self._vector_clock = VectorClock()
        self._undo_stack: List[CRDTOperation] = []
        self._redo_stack: List[CRDTOperation] = []
        self._tombstones: Dict[str, Any] = {}  # Deleted items for conflict resolution

    def get_state(self) -> Dict[str, Any]:
        """Get current document state."""
        return copy.deepcopy(self._state)

    def get_vector_clock(self) -> VectorClock:
        """Get current vector clock."""
        return VectorClock(clocks=self._vector_clock.clocks.copy())

    def get_operations(
        self,
        since_clock: Optional[VectorClock] = None,
    ) -> List[CRDTOperation]:
        """
        Get operations, optionally filtered by vector clock.

        Args:
            since_clock: Only return operations after this clock

        Returns:
            List of operations
        """
        if since_clock is None:
            return self._operations.copy()

        return [
            op for op in self._operations
            if since_clock.happens_before(op.vector_clock)
        ]

    def create_operation(
        self,
        operation_type: OperationType,
        path: List[Union[str, int]],
        value: Any = None,
        participant_id: str = "",
    ) -> CRDTOperation:
        """
        Create a new operation.

        Args:
            operation_type: Type of operation
            path: JSON path to target
            value: New value
            participant_id: ID of participant creating operation

        Returns:
            New CRDTOperation
        """
        # Get old value for undo
        old_value = self._get_value_at_path(path)

        # Increment vector clock
        new_clock = self._vector_clock.increment(participant_id)

        # Create operation
        op = CRDTOperation(
            operation_id="",
            operation_type=operation_type,
            path=path,
            value=value,
            old_value=old_value,
            participant_id=participant_id,
            vector_clock=new_clock,
            dependencies=[self._operations[-1].operation_id] if self._operations else [],
        )

        return op

    def apply_operation(
        self,
        operation: CRDTOperation,
        track_undo: bool = True,
    ) -> bool:
        """
        Apply an operation to the document.

        Args:
            operation: Operation to apply
            track_undo: Whether to track for undo

        Returns:
            True if applied successfully
        """
        # Check if already applied
        if operation.operation_id in self._applied_ids:
            return False

        # Apply based on type
        try:
            if operation.operation_type == OperationType.SET:
                self._apply_set(operation.path, operation.value)
            elif operation.operation_type == OperationType.INSERT:
                self._apply_insert(operation.path, operation.value)
            elif operation.operation_type == OperationType.DELETE:
                self._apply_delete(operation.path)
            elif operation.operation_type == OperationType.UPDATE:
                self._apply_update(operation.path, operation.value)
            elif operation.operation_type == OperationType.MOVE:
                self._apply_move(operation.path, operation.value)
        except Exception as e:
            logger.error(f"Failed to apply operation {operation.operation_id}: {e}")
            return False

        # Track operation
        self._operations.append(operation)
        self._applied_ids.add(operation.operation_id)
        self._vector_clock = self._vector_clock.merge(operation.vector_clock)

        # Track for undo
        if track_undo:
            self._undo_stack.append(operation)
            self._redo_stack.clear()

        return True

    def merge_operations(
        self,
        operations: List[CRDTOperation],
    ) -> List[CRDTOperation]:
        """
        Merge remote operations.

        Args:
            operations: Operations from remote

        Returns:
            List of newly applied operations
        """
        applied = []

        # Sort by vector clock to maintain causality
        sorted_ops = sorted(
            operations,
            key=lambda op: (sum(op.vector_clock.clocks.values()), op.timestamp),
        )

        for op in sorted_ops:
            if op.operation_id not in self._applied_ids:
                # Handle conflicts
                self._resolve_conflicts(op)

                if self.apply_operation(op, track_undo=False):
                    applied.append(op)

        return applied

    def _resolve_conflicts(self, incoming: CRDTOperation) -> None:
        """
        Resolve conflicts with concurrent operations.

        Uses Last-Writer-Wins (LWW) with participant ID as tiebreaker.
        """
        # Find concurrent operations on same path
        for existing in reversed(self._operations):
            if (existing.path == incoming.path and
                existing.vector_clock.concurrent_with(incoming.vector_clock)):

                # LWW: Compare timestamps, then participant IDs
                if existing.timestamp > incoming.timestamp:
                    # Existing wins, skip incoming
                    return
                elif existing.timestamp == incoming.timestamp:
                    # Tiebreaker: higher participant ID wins
                    if existing.participant_id > incoming.participant_id:
                        return

    def _get_value_at_path(self, path: List[Union[str, int]]) -> Any:
        """Get value at JSON path."""
        current = self._state
        for key in path:
            if isinstance(current, dict):
                current = current.get(str(key))
            elif isinstance(current, list) and isinstance(key, int):
                if 0 <= key < len(current):
                    current = current[key]
                else:
                    return None
            else:
                return None
        return current

    def _set_value_at_path(
        self,
        path: List[Union[str, int]],
        value: Any,
    ) -> None:
        """Set value at JSON path, creating intermediate objects as needed."""
        if not path:
            self._state = value
            return

        current = self._state
        for i, key in enumerate(path[:-1]):
            if isinstance(current, dict):
                if str(key) not in current:
                    # Create intermediate object
                    next_key = path[i + 1]
                    current[str(key)] = [] if isinstance(next_key, int) else {}
                current = current[str(key)]
            elif isinstance(current, list) and isinstance(key, int):
                while len(current) <= key:
                    current.append({})
                current = current[key]

        # Set final value
        final_key = path[-1]
        if isinstance(current, dict):
            current[str(final_key)] = value
        elif isinstance(current, list) and isinstance(final_key, int):
            while len(current) <= final_key:
                current.append(None)
            current[final_key] = value

    def _apply_set(self, path: List[Union[str, int]], value: Any) -> None:
        """Apply SET operation."""
        self._set_value_at_path(path, value)

    def _apply_insert(self, path: List[Union[str, int]], value: Any) -> None:
        """Apply INSERT operation (for arrays)."""
        if not path:
            return

        parent_path = path[:-1]
        index = path[-1]

        parent = self._get_value_at_path(parent_path) if parent_path else self._state
        if isinstance(parent, list) and isinstance(index, int):
            parent.insert(index, value)
        elif isinstance(parent, dict):
            parent[str(index)] = value

    def _apply_delete(self, path: List[Union[str, int]]) -> None:
        """Apply DELETE operation."""
        if not path:
            return

        parent_path = path[:-1]
        key = path[-1]

        parent = self._get_value_at_path(parent_path) if parent_path else self._state
        if isinstance(parent, list) and isinstance(key, int):
            if 0 <= key < len(parent):
                # Store tombstone for conflict resolution
                self._tombstones[str(path)] = parent[key]
                parent.pop(key)
        elif isinstance(parent, dict):
            if str(key) in parent:
                self._tombstones[str(path)] = parent[str(key)]
                del parent[str(key)]

    def _apply_update(self, path: List[Union[str, int]], value: Any) -> None:
        """Apply UPDATE operation (partial update for objects)."""
        current = self._get_value_at_path(path)
        if isinstance(current, dict) and isinstance(value, dict):
            current.update(value)
        else:
            self._set_value_at_path(path, value)

    def _apply_move(self, path: List[Union[str, int]], new_path: Any) -> None:
        """Apply MOVE operation."""
        value = self._get_value_at_path(path)
        if value is not None:
            self._apply_delete(path)
            self._set_value_at_path(new_path, value)

    def undo(self, participant_id: str) -> Optional[CRDTOperation]:
        """
        Undo last operation by participant.

        Args:
            participant_id: Participant to undo for

        Returns:
            Inverse operation if undone, None otherwise
        """
        # Find last operation by participant
        for i in range(len(self._undo_stack) - 1, -1, -1):
            op = self._undo_stack[i]
            if op.participant_id == participant_id:
                inverse = op.inverse()
                inverse.participant_id = participant_id
                inverse.vector_clock = self._vector_clock.increment(participant_id)

                self._undo_stack.pop(i)
                self._redo_stack.append(op)

                self.apply_operation(inverse, track_undo=False)
                return inverse

        return None

    def redo(self, participant_id: str) -> Optional[CRDTOperation]:
        """
        Redo last undone operation by participant.

        Args:
            participant_id: Participant to redo for

        Returns:
            Redone operation if successful, None otherwise
        """
        for i in range(len(self._redo_stack) - 1, -1, -1):
            op = self._redo_stack[i]
            if op.participant_id == participant_id:
                self._redo_stack.pop(i)

                # Create new operation with updated clock
                new_op = CRDTOperation(
                    operation_id="",
                    operation_type=op.operation_type,
                    path=op.path,
                    value=op.value,
                    old_value=op.old_value,
                    participant_id=participant_id,
                    vector_clock=self._vector_clock.increment(participant_id),
                )

                self.apply_operation(new_op)
                return new_op

        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize document to dictionary."""
        return {
            "document_id": self.document_id,
            "state": self._state,
            "vector_clock": self._vector_clock.to_dict(),
            "operations": [op.to_dict() for op in self._operations],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CRDTDocument":
        """Deserialize document from dictionary."""
        doc = cls(
            document_id=data["document_id"],
            initial_state=data.get("state", {}),
        )
        doc._vector_clock = VectorClock.from_dict(data.get("vector_clock", {}))

        for op_data in data.get("operations", []):
            op = CRDTOperation.from_dict(op_data)
            doc._operations.append(op)
            doc._applied_ids.add(op.operation_id)

        return doc
