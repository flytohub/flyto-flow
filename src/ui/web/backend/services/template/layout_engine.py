"""
Backward-compatibility shim — the layout engine has moved to services/layout/.

All imports of ``from services.template.layout_engine import compute_layout_positions``
continue to work unchanged.
"""

from services.template.layout.engine import compute_layout_positions  # noqa: F401

__all__ = ["compute_layout_positions"]
