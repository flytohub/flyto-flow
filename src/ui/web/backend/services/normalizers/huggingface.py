"""
HuggingFace Module Adapter

Converts HuggingFace model data to CanonicalModule format.
HuggingFace models can be used as AI modules in workflows.
"""

from typing import Dict, Any

from services.template.schemas.canonical_module import (
    CanonicalModule,
    create_canonical_module,
    add_snake_case_aliases,
    INCLUDE_SNAKE_CASE_ALIASES,
)
from services.node_config import enrich_module_with_node_config
from .base import (
    normalize_icon,
    compute_default_params,
    get_value_with_aliases,
)


def normalize_huggingface(raw: Dict[str, Any]) -> CanonicalModule:
    """
    Convert HuggingFace model data to CanonicalModule format.

    Input comes from: HuggingFace API response

    Args:
        raw: Raw HuggingFace model data

    Returns:
        CanonicalModule with all fields populated
    """
    model_id = get_value_with_aliases(raw, 'modelId', 'id', default='unknown')
    # Extract pipeline task (e.g., text-generation, image-classification)
    pipeline_tag = raw.get('pipeline_tag') or raw.get('pipelineTag') or 'inference'

    # Display properties
    name = raw.get('name') or model_id
    description = raw.get('description') or f"HuggingFace model: {model_id}"

    # Visual properties - HuggingFace brand color
    icon = normalize_icon("Brain", "#FFD21E")
    color = "#FFD21E"

    # Build params_schema for HuggingFace models
    params_schema = {
        "type": "object",
        "properties": {
            "model_id": {
                "type": "string",
                "default": model_id,
                "hidden": True,
                "label": "Model ID",
                "description": "HuggingFace model identifier"
            },
            "input": {
                "type": "string",
                "label": "Input",
                "description": "Input text or data for the model",
                "required": True
            },
            "parameters": {
                "type": "object",
                "label": "Parameters",
                "description": "Model-specific parameters",
                "default": {}
            }
        },
        "required": ["input"]
    }

    default_params = compute_default_params(params_schema)

    # Build input ports
    input_ports = [
        {
            "id": "input",
            "handleId": "target",
            "position": "left",
            "label": "Input",
            "labelKey": f"huggingface.{model_id}.ports.input",
            "dataType": "string",
            "edgeType": "data",
            "maxConnections": 1,
            "required": True,
        }
    ]

    # Build output ports
    output_ports = [
        {
            "id": "output",
            "handleId": "output",
            "position": "right",
            "label": "Output",
            "labelKey": f"huggingface.{model_id}.ports.output",
            "dataType": "object",
            "edgeType": "data",
            "color": "#10B981",
        },
        {
            "id": "error",
            "handleId": "source-error",
            "position": "right",
            "label": "Error",
            "labelKey": "common.ports.error",
            "event": "error",
            "color": "#EF4444",
            "edgeType": "control",
        }
    ]

    # Source data for HuggingFace
    source_data = {
        "modelId": model_id,
        "entrypoint": {
            "type": "huggingface",
            "modelId": model_id,
            "runtime": "huggingface-inference",
        },
    }

    # Create unique module_id with namespace to prevent collisions
    # Format: hf:{repo_id}:{task} (e.g., hf:gpt2:text-generation)
    # Sanitize model_id to replace slashes with underscores for valid module IDs
    sanitized_model_id = model_id.replace('/', '_').replace(' ', '_')
    unique_module_id = f"hf:{sanitized_model_id}:{pipeline_tag}"

    # Create canonical module using factory function
    result = create_canonical_module(
        module_id=unique_module_id,
        label=name,
        category="ai",
        source="huggingface",

        # Display
        description=description,
        icon=icon,
        color=color,
        group="AI Models",
        tier="standard",
        visibility="default",
        tags=raw.get('tags') or ["ai", "huggingface", "model"],
        labelKey=f"huggingface.{model_id}.label",
        descriptionKey=f"huggingface.{model_id}.description",

        # Schema
        paramsSchema=params_schema,
        defaultParams=default_params,
        outputSchema={"type": "object"},

        # Connection
        inputTypes=["string", "object"],
        outputTypes=["object"],
        canReceiveFrom=["*"],
        canConnectTo=["*"],
        inputPorts=input_ports,
        outputPorts=output_ports,

        # Node
        nodeType="ai",

        # AI flags - HuggingFace models are AI models
        isAIModel=True,
        isMemory=False,
        isTool=False,
        isTemplate=False,

        # Execution
        timeout=60.0,  # Default 60s for AI inference
        retryable=True,
        maxRetries=3,
        concurrentSafe=True,
        requiresCredentials=True,  # Needs HuggingFace API token
        requiredPermissions=["network", "ai"],

        # Metadata
        version="1.0.0",
        stability="stable",
        author=raw.get('author'),
        docsUrl=f"https://huggingface.co/{model_id}",
        deprecated=False,
        isVerified=raw.get('verified', False),
        isFeatured=False,

        # Source data
        sourceData=source_data,
    )

    # Enrich with node configuration
    result = enrich_module_with_node_config(result)

    # Add snake_case aliases if enabled for backward compatibility
    if INCLUDE_SNAKE_CASE_ALIASES:
        result = add_snake_case_aliases(result)

    return result
