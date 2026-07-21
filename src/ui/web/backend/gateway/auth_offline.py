"""
Desktop-only offline-mode admin bypass.

This module is intentionally excluded from cloud Docker images (see Dockerfile,
Dockerfile.web, Dockerfile.worker — they `rm -f` this file during the build).
It must only be importable on desktop builds where a local user has full,
single-tenant access to their own machine.

Any presence of this module in a cloud image is treated as a fatal build defect
by the startup guard in main_cloud.py / main_web.py / main_worker.py.
"""
import os

from gateway.providers.base import UserInfo


_CLOUD_ENV_MARKERS = ("FIRESTORE_PROJECT",)
_STRIPE_MARKER_PREFIX = "STRIPE_"

if any(os.environ.get(m) for m in _CLOUD_ENV_MARKERS) or any(
    k.startswith(_STRIPE_MARKER_PREFIX) for k in os.environ
):
    raise RuntimeError(
        "gateway.auth_offline loaded with cloud env configured "
        "(FIRESTORE_PROJECT / STRIPE_*) — refusing to expose offline admin bypass."
    )


OFFLINE_USER = UserInfo(
    id="local-user",
    email="user@localhost",
    username="local-user",
    display_name="Local User",
    avatar_url=None,
    roles=["admin"],
    groups=[],
    organization_id=None,
    is_admin=True,
    is_active=True,
    subscription_plan="offline",
    subscription_status="active",
    metadata={"offline": True},
)
