"""
Shared billing constants.

Used by gateway/auth.py (trial guard) and api/auth/deps.py (Pro status computation).
"""

PRO_PLANS = frozenset(["pro", "team", "enterprise", "offline"])
ACTIVE_STATUSES = frozenset(["active", "trialing"])
