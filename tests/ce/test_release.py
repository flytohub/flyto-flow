import importlib.util
import os
import sys
from pathlib import Path

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "src/ui/web/backend"
sys.path.insert(0, str(BACKEND))
os.environ["DEPLOYMENT_MODE"] = "offline"
os.environ["FLYTO_EDITION_PROFILE"] = "cloud_ce"
os.environ["FLYTO_OFFLINE_LOGIN_MODE"] = "jwt"
os.environ["FLYTO_OFFLINE_AUTH_SECRET"] = "ce-test-secret-with-at-least-32-characters"
os.environ["API_HOST"] = "127.0.0.1"


@pytest.fixture(autouse=True)
def isolated_offline_storage(tmp_path, monkeypatch):
    from gateway.providers.hub import reset_provider_hub
    from gateway.storage.offline_db import close_offline_db

    close_offline_db()
    reset_provider_hub()
    monkeypatch.setenv("FLYTO_OFFLINE_DB_PATH", str(tmp_path / "offline.db"))
    monkeypatch.delenv("FLYTO_OFFLINE_ALLOW_REGISTRATION", raising=False)
    yield
    reset_provider_hub()
    close_offline_db()


def test_private_provider_implementations_are_absent():
    for module_name in (
        "gateway.providers.hosted",
        "gateway.providers.auth.firebase",
        "gateway.providers.auth.enterprise",
        "gateway.providers.data.firebase",
        "gateway.providers.data.enterprise",
    ):
        assert importlib.util.find_spec(module_name) is None, module_name


def test_offline_provider_hub_is_fail_closed():
    from gateway.providers.hub import get_provider_hub

    hub = get_provider_hub()
    assert hub.is_offline is True
    assert hub.is_cloud is False
    assert hub.is_enterprise is False
    assert hub.get_provider_info()["mode"] == "offline"


def test_offline_application_exposes_only_ce_route_families():
    from main_offline import app

    paths = set(app.openapi()["paths"])
    assert "/api/health" in paths
    assert "/api/app/version" in paths
    assert any(path.startswith("/api/workflows") for path in paths)
    assert any(path.startswith("/api/templates") for path in paths)
    assert any(path.startswith("/api/mcp") for path in paths)

    forbidden = (
        "/api/admin",
        "/api/billing",
        "/api/enterprise",
        "/api/marketplace",
        "/api/payments",
        "/api/subscriptions",
        "/api/telemetry",
        "/api/usage",
        "/api/wallet",
    )
    assert not [path for path in paths if path.startswith(forbidden)]


@pytest.mark.asyncio
async def test_local_jwt_auth_round_trip_and_registration_lock(isolated_offline_storage):
    from main_offline import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        assert (await client.get("/api/auth/me")).status_code == 401

        registration = await client.post(
            "/api/auth/register",
            json={
                "email": "owner@example.com",
                "password": "StrongPassword123",
                "username": "Owner",
            },
        )
        assert registration.status_code == 200, registration.text
        registered = registration.json()
        assert registered["user"]["is_admin"] is True

        second_registration = await client.post(
            "/api/auth/register",
            json={
                "email": "public@example.com",
                "password": "StrongPassword456",
            },
        )
        assert second_registration.status_code == 400

        login = await client.post(
            "/api/auth/login",
            json={"email": "owner@example.com", "password": "StrongPassword123"},
        )
        assert login.status_code == 200, login.text
        tokens = login.json()

        me = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert me.status_code == 200
        assert me.json()["user"]["email"] == "owner@example.com"

        refresh = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert refresh.status_code == 200
        assert refresh.json()["access_token"]


@pytest.mark.asyncio
async def test_ce_capabilities_and_quota_are_hosted_service_free(isolated_offline_storage):
    from api.workflows.execution import _check_points_quota
    from main_offline import app

    await _check_points_quota("local-user", "free")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["billingMode"] == "disabled"
    assert body["editionProfile"] == "cloud_ce"
    assert "storage.sqlite" in body["capabilities"]
    assert "storage.postgres" not in body["capabilities"]


@pytest.mark.asyncio
async def test_authenticated_template_crud_uses_local_storage(isolated_offline_storage):
    from main_offline import app

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        follow_redirects=True,
    ) as client:
        registration = await client.post(
            "/api/auth/register",
            json={"email": "owner@example.com", "password": "StrongPassword123"},
        )
        assert registration.status_code == 200, registration.text
        headers = {
            "Authorization": f"Bearer {registration.json()['access_token']}",
        }

        created = await client.post(
            "/api/templates/",
            headers=headers,
            json={
                "name": "Local template",
                "description": "Persists in CE SQLite",
                "steps": [],
            },
        )
        assert created.status_code == 200, created.text
        template_id = created.json()["template"]["id"]

        listed = await client.get("/api/templates/", headers=headers)
        assert listed.status_code == 200, listed.text
        assert template_id in {item["id"] for item in listed.json()["items"]}

        updated = await client.put(
            f"/api/templates/{template_id}",
            headers=headers,
            json={"name": "Updated local template"},
        )
        assert updated.status_code == 200, updated.text
        assert updated.json()["template"]["name"] == "Updated local template"

        deleted = await client.delete(f"/api/templates/{template_id}", headers=headers)
        assert deleted.status_code == 200, deleted.text

        missing = await client.get(f"/api/templates/{template_id}", headers=headers)
        assert missing.status_code == 404
