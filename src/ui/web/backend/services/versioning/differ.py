"""
Workflow Differ

Single responsibility: Compare workflow versions.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from services.versioning.version import WorkflowVersion

logger = logging.getLogger(__name__)


@dataclass
class NodeChange:
    """Represents a change to a workflow node."""

    node_id: str
    change_type: str  # added, removed, modified
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    modified_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "node_id": self.node_id,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "modified_fields": self.modified_fields,
        }


@dataclass
class EdgeChange:
    """Represents a change to a workflow edge."""

    edge_id: str
    change_type: str  # added, removed
    source: Optional[str] = None
    target: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "edge_id": self.edge_id,
            "change_type": self.change_type,
            "source": self.source,
            "target": self.target,
        }


@dataclass
class ConfigChange:
    """Represents a change to workflow configuration."""

    field: str
    change_type: str  # added, removed, modified
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "field": self.field,
            "change_type": self.change_type,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }


@dataclass
class WorkflowDiff:
    """
    Difference between two workflow versions.

    Contains all changes between two versions.
    """

    version_from: str
    version_to: str
    has_changes: bool = False
    added_nodes: List[NodeChange] = field(default_factory=list)
    removed_nodes: List[NodeChange] = field(default_factory=list)
    modified_nodes: List[NodeChange] = field(default_factory=list)
    added_edges: List[EdgeChange] = field(default_factory=list)
    removed_edges: List[EdgeChange] = field(default_factory=list)
    config_changes: List[ConfigChange] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version_from": self.version_from,
            "version_to": self.version_to,
            "has_changes": self.has_changes,
            "added_nodes": [n.to_dict() for n in self.added_nodes],
            "removed_nodes": [n.to_dict() for n in self.removed_nodes],
            "modified_nodes": [n.to_dict() for n in self.modified_nodes],
            "added_edges": [e.to_dict() for e in self.added_edges],
            "removed_edges": [e.to_dict() for e in self.removed_edges],
            "config_changes": [c.to_dict() for c in self.config_changes],
        }

    def get_summary(self) -> str:
        """Get a human-readable summary of changes."""
        parts = []

        if self.added_nodes:
            parts.append(f"{len(self.added_nodes)} node(s) added")
        if self.removed_nodes:
            parts.append(f"{len(self.removed_nodes)} node(s) removed")
        if self.modified_nodes:
            parts.append(f"{len(self.modified_nodes)} node(s) modified")
        if self.added_edges:
            parts.append(f"{len(self.added_edges)} edge(s) added")
        if self.removed_edges:
            parts.append(f"{len(self.removed_edges)} edge(s) removed")
        if self.config_changes:
            parts.append(f"{len(self.config_changes)} config change(s)")

        if not parts:
            return "No changes"

        return "; ".join(parts)


class WorkflowDiffer:
    """
    Compare two workflow versions.

    Analyzes differences in nodes, edges, and configuration.
    """

    @classmethod
    def diff(
        cls,
        v1: WorkflowVersion,
        v2: WorkflowVersion,
    ) -> WorkflowDiff:
        """
        Compare two workflow versions.

        Args:
            v1: First version (older)
            v2: Second version (newer)

        Returns:
            WorkflowDiff with all changes
        """
        result = WorkflowDiff(
            version_from=v1.id,
            version_to=v2.id,
        )

        # Quick check: same hash means no changes
        if v1.content_hash == v2.content_hash:
            return result

        result.has_changes = True

        # Compare nodes
        cls._diff_nodes(v1.definition, v2.definition, result)

        # Compare edges
        cls._diff_edges(v1.definition, v2.definition, result)

        # Compare config
        cls._diff_config(v1.definition, v2.definition, result)

        return result

    @classmethod
    def _diff_nodes(
        cls,
        def1: Dict[str, Any],
        def2: Dict[str, Any],
        result: WorkflowDiff,
    ) -> None:
        """Compare nodes between definitions."""
        nodes1 = cls._get_nodes_map(def1)
        nodes2 = cls._get_nodes_map(def2)

        ids1 = set(nodes1.keys())
        ids2 = set(nodes2.keys())

        # Added nodes
        for node_id in ids2 - ids1:
            result.added_nodes.append(NodeChange(
                node_id=node_id,
                change_type="added",
                new_value=nodes2[node_id],
            ))

        # Removed nodes
        for node_id in ids1 - ids2:
            result.removed_nodes.append(NodeChange(
                node_id=node_id,
                change_type="removed",
                old_value=nodes1[node_id],
            ))

        # Modified nodes
        for node_id in ids1 & ids2:
            old_node = nodes1[node_id]
            new_node = nodes2[node_id]

            if old_node != new_node:
                modified_fields = cls._find_modified_fields(old_node, new_node)
                result.modified_nodes.append(NodeChange(
                    node_id=node_id,
                    change_type="modified",
                    old_value=old_node,
                    new_value=new_node,
                    modified_fields=modified_fields,
                ))

    @classmethod
    def _diff_edges(
        cls,
        def1: Dict[str, Any],
        def2: Dict[str, Any],
        result: WorkflowDiff,
    ) -> None:
        """Compare edges between definitions."""
        edges1 = cls._get_edges_map(def1)
        edges2 = cls._get_edges_map(def2)

        ids1 = set(edges1.keys())
        ids2 = set(edges2.keys())

        # Added edges
        for edge_id in ids2 - ids1:
            edge = edges2[edge_id]
            result.added_edges.append(EdgeChange(
                edge_id=edge_id,
                change_type="added",
                source=edge.get("source"),
                target=edge.get("target"),
            ))

        # Removed edges
        for edge_id in ids1 - ids2:
            edge = edges1[edge_id]
            result.removed_edges.append(EdgeChange(
                edge_id=edge_id,
                change_type="removed",
                source=edge.get("source"),
                target=edge.get("target"),
            ))

    @classmethod
    def _diff_config(
        cls,
        def1: Dict[str, Any],
        def2: Dict[str, Any],
        result: WorkflowDiff,
    ) -> None:
        """Compare configuration between definitions."""
        # Fields to compare (excluding nodes and edges)
        config_fields = {"name", "description", "version", "settings", "metadata"}

        for field_name in config_fields:
            val1 = def1.get(field_name)
            val2 = def2.get(field_name)

            if val1 is None and val2 is not None:
                result.config_changes.append(ConfigChange(
                    field=field_name,
                    change_type="added",
                    new_value=val2,
                ))
            elif val1 is not None and val2 is None:
                result.config_changes.append(ConfigChange(
                    field=field_name,
                    change_type="removed",
                    old_value=val1,
                ))
            elif val1 != val2:
                result.config_changes.append(ConfigChange(
                    field=field_name,
                    change_type="modified",
                    old_value=val1,
                    new_value=val2,
                ))

    @classmethod
    def _get_nodes_map(cls, definition: Dict[str, Any]) -> Dict[str, Dict]:
        """Extract nodes as a map of id -> node."""
        nodes = definition.get("nodes", [])
        if isinstance(nodes, list):
            return {n.get("id", ""): n for n in nodes if isinstance(n, dict)}
        return {}

    @classmethod
    def _get_edges_map(cls, definition: Dict[str, Any]) -> Dict[str, Dict]:
        """Extract edges as a map of id -> edge."""
        edges = definition.get("edges", [])
        if isinstance(edges, list):
            result = {}
            for e in edges:
                if isinstance(e, dict):
                    edge_id = e.get("id") or f"{e.get('source')}-{e.get('target')}"
                    result[edge_id] = e
            return result
        return {}

    @classmethod
    def _find_modified_fields(
        cls,
        old: Dict[str, Any],
        new: Dict[str, Any],
    ) -> List[str]:
        """Find which fields differ between two dictionaries."""
        modified = []
        all_keys = set(old.keys()) | set(new.keys())

        for key in all_keys:
            if old.get(key) != new.get(key):
                modified.append(key)

        return modified
