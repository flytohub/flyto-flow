"""
Smart Layout Engine - Sugiyama-style layered graph layout.

Split into phase-based modules:
  - constants.py   — Shared helpers and key-access utilities
  - engine.py      — Main entry point + Phase 0 (parse input)
  - layers.py      — Phase 1 (layer assignment) + Phase 2 (subtree estimation)
  - positioning.py — Phase 4 (type-aware BFS positioning)
  - merge.py       — Phase 3 (merge detection) + Phase 5 (merge positioning)
  - crossing.py    — Phase 6 (crossing minimization)
  - overlap.py     — Phase 7 (overlap resolution)
  - resources.py   — Phase 8 (resource nodes) + Phase 9 (orphans) + Phase 10 (flip)
"""

from services.template.layout.engine import compute_layout_positions

__all__ = ["compute_layout_positions"]
