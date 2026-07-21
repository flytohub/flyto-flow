"""
Telemetry constants shared across all mixins
"""

# Sensitive fields to redact
SENSITIVE_FIELDS = {
    "authorization",
    "cookie",
    "x-api-key",
    "api_key",
    "apikey",
    "token",
    "access_token",
    "accesstoken",
    "refresh_token",
    "refreshtoken",
    "password",
    "secret",
    "credential",
    "private_key",
    "privatekey",
    "api-key",
}

# Collection names
COLLECTION_NAME = "telemetry_events"
PRESENCE_COLLECTION = "user_presence"

# Presence timeout (seconds) - user considered offline after this
PRESENCE_TIMEOUT = 120  # 2 minutes

# Safety limit for Firestore queries to prevent OOM on Cloud Run
# If you need more, pre-aggregate data instead of scanning on-the-fly
MAX_QUERY_DOCS = 10000
