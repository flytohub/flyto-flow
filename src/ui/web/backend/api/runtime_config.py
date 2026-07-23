"""Public, immutable CE runtime contract."""

import os

from fastapi import APIRouter

from gateway.storage.queue_factory import get_queue_backend
from services.connections.runtime import get_connection_runtime

router = APIRouter()


@router.get("/runtime-config")
async def runtime_config():
    connection_runtime = get_connection_runtime()
    connection_factory = bool(
        os.environ.get("FLYTO_CONNECTION_RUNTIME_FACTORY", "").strip()
    )
    queue_backend = get_queue_backend()
    key_backend = os.environ.get("FLYTO_KEY_BACKEND", "local").strip().lower()
    trace_factory = bool(
        os.environ.get("FLYTO_TRACE_EXPORTER_FACTORY", "").strip()
    )
    return {
        "deploymentMode": "local_offline",
        "edition": "ce",
        "accountRequired": False,
        "deploymentId": "local",
        "network": {
            "internetAllowed": False,
            "airgap": True,
            "implicitOutboundAllowed": False,
        },
        "capabilities": {
            "connections": {
                "catalog": True,
                "types": [
                    definition.id
                    for definition in connection_runtime.catalog.list()
                    if not definition.deprecated
                ],
                "profiles": True,
                "secretReferences": True,
                "runtimeInjection": connection_factory,
                "builtInTransport": False,
                "transportProvider": "external" if connection_factory else "none",
                "supportedOperations": [
                    "catalog",
                    "profile-management",
                    "policy-validation",
                ],
            },
            "extensions": {
                "signedBundles": True,
                "permissionManifest": True,
                "trustedKeyRevocation": True,
                "templatePackValidation": True,
            },
            "operations": {
                "backupRestore": True,
                "schemaMigrations": True,
                "auditExport": True,
                "standaloneWorker": True,
            },
            "secretManagement": {
                "backend": key_backend,
                "externalProvider": key_backend in {"vault", "kms", "custom"},
                "customProviderFactory": key_backend == "custom",
            },
            "observability": {
                "prometheus": True,
                "localTraces": not trace_factory,
                "externalTraceExporter": trace_factory,
                "signedAlertWebhooks": True,
                "tamperEvidentAuditExport": True,
            },
            "enterpriseProviders": {
                "sso": False,
                "scim": False,
                "sharedQueue": queue_backend != "sqlite",
                "sharedData": False,
            },
        },
    }
