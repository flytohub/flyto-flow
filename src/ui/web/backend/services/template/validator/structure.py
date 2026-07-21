"""
Structure Validation

Workflow structure, graph, and limits validation.
"""

from typing import Any, Dict, List

from services.template.validator.models import ValidationIssue, ValidationSeverity, ValidatorConfig


def validate_basic_structure(workflow: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate basic workflow structure.

    Args:
        workflow: Workflow dictionary

    Returns:
        List of structural issues
    """
    issues = []

    if not isinstance(workflow, dict):
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path="$",
            message="Workflow must be an object",
            code="INVALID_TYPE",
        ))
        return issues

    # Required fields
    for field in ["id", "name", "nodes"]:
        if field not in workflow:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=f"$.{field}",
                message=f"Missing required field: {field}",
                code="MISSING_FIELD",
            ))

    return issues


def validate_graph(workflow: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate workflow graph structure.

    Checks:
    - Edge references valid nodes
    - No self-loops
    - No duplicate node IDs

    Args:
        workflow: Workflow dictionary

    Returns:
        List of graph issues
    """
    issues = []

    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    # Build node ID set
    node_ids = {node.get("id") for node in nodes if node.get("id")}

    # Check edge references
    for i, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")

        if source not in node_ids:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=f"$.edges[{i}].source",
                message=f"Edge references unknown source node: {source}",
                code="INVALID_EDGE_SOURCE",
            ))

        if target not in node_ids:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=f"$.edges[{i}].target",
                message=f"Edge references unknown target node: {target}",
                code="INVALID_EDGE_TARGET",
            ))

        # Check for self-loops
        if source == target:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                path=f"$.edges[{i}]",
                message="Edge creates a self-loop",
                code="SELF_LOOP",
            ))

    # Check for duplicate node IDs
    seen_ids = set()
    for i, node in enumerate(nodes):
        node_id = node.get("id")
        if node_id in seen_ids:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=f"$.nodes[{i}].id",
                message=f"Duplicate node ID: {node_id}",
                code="DUPLICATE_NODE_ID",
            ))
        seen_ids.add(node_id)

    return issues


def validate_limits(
    workflow: Dict[str, Any],
    config: ValidatorConfig,
) -> List[ValidationIssue]:
    """
    Validate size and depth limits.

    Args:
        workflow: Workflow dictionary
        config: Validator configuration

    Returns:
        List of limit violations
    """
    issues = []

    # Check node count
    nodes = workflow.get("nodes", [])
    if len(nodes) > config.max_nodes:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path="$.nodes",
            message=f"Too many nodes ({len(nodes)} > {config.max_nodes})",
            code="TOO_MANY_NODES",
        ))

    # Check edge count
    edges = workflow.get("edges", [])
    if len(edges) > config.max_edges:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path="$.edges",
            message=f"Too many edges ({len(edges)} > {config.max_edges})",
            code="TOO_MANY_EDGES",
        ))

    # Check depth
    depth = get_depth(workflow, config.max_depth)
    if depth > config.max_depth:
        issues.append(ValidationIssue(
            severity=ValidationSeverity.ERROR,
            path="$",
            message=f"Workflow structure too deep ({depth} > {config.max_depth})",
            code="TOO_DEEP",
        ))

    # Check string lengths
    issues.extend(validate_string_lengths(workflow, "$", config.max_string_length))

    return issues


def validate_string_lengths(
    obj: Any,
    path: str,
    max_length: int,
) -> List[ValidationIssue]:
    """
    Validate string lengths recursively.

    .. deprecated::
        For parameter validation, use
        :func:`services.template.validator.params.validate_params_against_schema`
        instead, which performs schema-aware checks (minLength, maxLength, pattern,
        etc.) per field. This function applies a single blanket max_length to all
        strings and is only kept for backward compatibility with
        :func:`validate_limits`.

    Args:
        obj: Object to check
        path: JSON path
        max_length: Maximum allowed string length

    Returns:
        List of issues for strings exceeding limit
    """
    issues = []

    if isinstance(obj, str):
        if len(obj) > max_length:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                path=path,
                message=f"String too long ({len(obj)} > {max_length})",
                code="STRING_TOO_LONG",
            ))
    elif isinstance(obj, dict):
        for key, value in obj.items():
            issues.extend(validate_string_lengths(value, f"{path}.{key}", max_length))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            issues.extend(validate_string_lengths(item, f"{path}[{i}]", max_length))

    return issues


def validate_resource_edges(workflow: Dict[str, Any]) -> List[ValidationIssue]:
    """
    Validate resource edge semantics for AI Agent sub-nodes.

    Checks that resource edges connect the correct sub-node types:
    - target-model → ai.model
    - target-memory → ai.memory
    - target-tools → any module (as tool)
    """
    issues = []

    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    node_map = {n.get("id"): n for n in nodes if n.get("id")}

    PORT_EXPECTED_MODULES = {
        "target-model": {"ai.model"},
        "target-memory": {"ai.memory"},
    }

    for i, edge in enumerate(edges):
        target_handle = edge.get("targetHandle", "")
        if target_handle not in PORT_EXPECTED_MODULES:
            continue

        source_node = node_map.get(edge.get("source"))
        if not source_node:
            continue

        source_module = (source_node.get("data", {}).get("module", "")
                         or source_node.get("module", ""))
        expected = PORT_EXPECTED_MODULES[target_handle]

        if source_module and source_module not in expected:
            issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                path=f"$.edges[{i}]",
                message=f"Module '{source_module}' connected to '{target_handle}' port, expected {expected}",
                code="RESOURCE_TYPE_MISMATCH",
            ))

    return issues


def get_depth(obj: Any, max_depth: int, current_depth: int = 0) -> int:
    """
    Get maximum nesting depth of object.

    Args:
        obj: Object to measure
        max_depth: Short-circuit after this depth
        current_depth: Current depth level

    Returns:
        Maximum depth found
    """
    if current_depth > max_depth:
        return current_depth  # Short circuit

    if isinstance(obj, dict):
        if not obj:
            return current_depth
        return max(
            get_depth(v, max_depth, current_depth + 1)
            for v in obj.values()
        )
    elif isinstance(obj, list):
        if not obj:
            return current_depth
        return max(
            get_depth(item, max_depth, current_depth + 1)
            for item in obj
        )
    return current_depth


def sanitize_workflow(
    workflow: Dict[str, Any],
    max_string_length: int,
) -> Dict[str, Any]:
    """
    Sanitize workflow by truncating long strings.

    Note: Only call on already-validated workflows.

    Args:
        workflow: Workflow to sanitize
        max_string_length: Maximum string length

    Returns:
        Sanitized workflow copy
    """
    import copy
    sanitized = copy.deepcopy(workflow)

    def truncate_strings(obj: Any) -> Any:
        if isinstance(obj, str):
            if len(obj) > max_string_length:
                return obj[:max_string_length] + "...[truncated]"
            return obj
        elif isinstance(obj, dict):
            return {k: truncate_strings(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [truncate_strings(item) for item in obj]
        return obj

    return truncate_strings(sanitized)
