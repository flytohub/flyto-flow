"""
Schemas Module
Type definitions for data structures used across the backend.
"""

from .canonical_module import (
    CanonicalModule,
    ParamProperty,
    ParamsSchema,
    IconSpec,
    HandleConfig,
    PortConfig,
    UIConfig,
    SourceType,
    NodeType,
    SourceData,
    CostInfo,
    EntrypointConfig,
    DynamicHandlesConfig,
    create_canonical_module,
    add_snake_case_aliases,
    strip_snake_case_aliases,
    convert_snake_to_camel,
    INCLUDE_SNAKE_CASE_ALIASES,
    SNAKE_TO_CAMEL_MAPPING,
)

# Backward compatibility alias
IconObject = IconSpec

__all__ = [
    'CanonicalModule',
    'ParamProperty',
    'ParamsSchema',
    'IconSpec',
    'IconObject',  # Backward compatibility alias
    'HandleConfig',
    'PortConfig',
    'UIConfig',
    'SourceType',
    'NodeType',
    'SourceData',
    'CostInfo',
    'EntrypointConfig',
    'DynamicHandlesConfig',
    'create_canonical_module',
    'add_snake_case_aliases',
    'strip_snake_case_aliases',
    'convert_snake_to_camel',
    'INCLUDE_SNAKE_CASE_ALIASES',
    'SNAKE_TO_CAMEL_MAPPING',
]
