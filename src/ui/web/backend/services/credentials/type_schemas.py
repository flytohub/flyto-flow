"""
Credential Type Schemas

Defines the field structure for each credential type,
used by the frontend to render appropriate input forms.
"""

from typing import Any, Dict, List

CREDENTIAL_TYPE_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "api_key": {
        "label": "API Key",
        "description": "A single API key or token for service authentication",
        "fields": [
            {
                "name": "value",
                "label": "API Key",
                "type": "password",
                "required": True,
                "placeholder": "sk-...",
            },
        ],
        "docs_url": None,
    },
    "bearer_token": {
        "label": "Bearer Token",
        "description": "OAuth Bearer token for API authorization",
        "fields": [
            {
                "name": "value",
                "label": "Token",
                "type": "password",
                "required": True,
                "placeholder": "xoxb-... or ghp_...",
            },
        ],
        "docs_url": None,
    },
    "basic_auth": {
        "label": "Basic Auth",
        "description": "Username and password for HTTP Basic authentication",
        "fields": [
            {
                "name": "username",
                "label": "Username",
                "type": "text",
                "required": True,
                "placeholder": "user@flyto2.com",
            },
            {
                "name": "password",
                "label": "Password",
                "type": "password",
                "required": True,
                "placeholder": "",
            },
        ],
        "docs_url": None,
    },
    "oauth2": {
        "label": "OAuth2",
        "description": "OAuth2 credentials with client ID and secret",
        "fields": [
            {
                "name": "client_id",
                "label": "Client ID",
                "type": "text",
                "required": True,
                "placeholder": "",
            },
            {
                "name": "client_secret",
                "label": "Client Secret",
                "type": "password",
                "required": True,
                "placeholder": "",
            },
            {
                "name": "token_url",
                "label": "Token URL",
                "type": "text",
                "required": False,
                "placeholder": "https://oauth.flyto2.com/token",
            },
            {
                "name": "scopes",
                "label": "Scopes",
                "type": "text",
                "required": False,
                "placeholder": "read write",
            },
        ],
        "docs_url": None,
    },
    "generic": {
        "label": "Generic",
        "description": "Free-form secret value",
        "fields": [
            {
                "name": "value",
                "label": "Value",
                "type": "password",
                "required": True,
                "placeholder": "",
            },
        ],
        "docs_url": None,
    },
}


def get_type_schemas() -> Dict[str, Dict[str, Any]]:
    """Return all credential type schemas."""
    return CREDENTIAL_TYPE_SCHEMAS


def pack_credential_value(credential_type: str, fields: Dict[str, str]) -> str:
    """
    Pack multiple fields into a single stored value.

    For single-field types (api_key, bearer_token, generic): returns the value as-is.
    For multi-field types (basic_auth, oauth2): JSON-encodes the fields.
    """
    import json

    schema = CREDENTIAL_TYPE_SCHEMAS.get(credential_type, CREDENTIAL_TYPE_SCHEMAS["generic"])
    field_names = [f["name"] for f in schema["fields"]]

    if len(field_names) == 1:
        return fields.get(field_names[0], fields.get("value", ""))

    return json.dumps({k: v for k, v in fields.items() if k in field_names})
