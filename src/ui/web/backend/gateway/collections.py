"""
Hosted data-store collection name constants.

Central registry of collection names used by hosted provider adapters.
New code SHOULD use these constants instead of hardcoded strings.
If you need to rename a collection or migrate to a different backend,
change it here — all new code references this module.

Usage:
    from gateway.collections import Collections

    store.open_collection(Collections.USERS)
    store.open_collection(Collections.TEMPLATES).open_document(template_id)

NOTE: Existing call sites (~600+) still use hardcoded strings.
      This registry exists so new code can reference constants, and
      as documentation of every collection in use. Migration of
      existing call sites is intentionally deferred to avoid risk.
"""


class Collections:
    """Collection names shared by hosted provider adapters."""

    # ── Core ────────────────────────────────────────────────────────
    USERS = "users"
    TEMPLATES = "templates"
    WORKFLOWS = "workflows"
    EXECUTIONS = "executions"

    # ── Auth & Identity ─────────────────────────────────────────────
    API_KEYS = "api_keys"
    AUTH_CODES = "auth_codes"
    DESKTOP_OAUTH_FLOWS = "desktop_oauth_flows"
    FCM_TOKENS = "fcm_tokens"
    INVITE_KEYS = "invite_keys"

    # ── AI ──────────────────────────────────────────────────────────
    AI_CONFIGS = "ai_configs"
    AI_USAGE = "ai_usage"
    AI_USAGE_LOGS = "ai_usage_logs"
    CONVERSATIONS = "conversations"
    MESSAGES = "messages"

    # ── Marketplace & Commerce ──────────────────────────────────────
    PURCHASES = "purchases"
    PURCHASED_TEMPLATES = "purchased_templates"
    FAILED_PURCHASES = "failed_purchases"
    PENDING_CHECKOUTS = "pending_checkouts"
    ORDERS = "orders"
    REVIEWS = "reviews"
    REPORTS = "reports"

    # ── Subscriptions & Payments ────────────────────────────────────
    SUBSCRIPTIONS = "subscriptions"
    SUBSCRIPTION_PAYMENTS = "subscription_payments"
    CREDIT_TOPUPS = "credit_topups"
    CREDIT_TRANSACTIONS = "credit_transactions"

    # ── Creator & Earnings ──────────────────────────────────────────
    CREATOR_APPLICATIONS = "creator_applications"
    EARNINGS = "earnings"
    EARNINGS_TRANSACTIONS = "earnings_transactions"
    FEE_HISTORY = "fee_history"
    FEE_TRANSACTIONS = "fee_transactions"
    PAYOUTS = "payouts"

    # ── Template Structure (subcollections or related) ──────────────
    NODES = "nodes"
    EDGES = "edges"
    VERSIONS = "versions"
    CATEGORIES = "categories"
    KEYWORDS = "keywords"
    FORKS = "forks"
    FORKED_TEMPLATES = "forked_templates"
    TEMPLATE_FOLDERS = "template_folders"
    TEMPLATE_ISSUES = "template_issues"
    TEMPLATE_PULL_REQUESTS = "template_pull_requests"

    # ── Collaboration ───────────────────────────────────────────────
    COLLABORATION_INVITES = "collaboration_invites"
    COLLABORATION_USAGE = "collaboration_usage"
    FOLLOWS = "follows"
    PEOPLE = "people"

    # ── Triggers ────────────────────────────────────────────────────
    WEBHOOKS = "webhooks"
    WEBHOOK_FAILURES = "webhook_failures"
    WEBHOOK_NONCES = "webhook_nonces"
    WEBHOOK_RETRIES = "webhook_retries"
    PROCESSED_WEBHOOK_EVENTS = "processed_webhook_events"
    SCHEDULES = "schedules"

    # ── Notifications & Chat ────────────────────────────────────────
    NOTIFICATIONS = "notifications"

    # ── Admin & Audit ───────────────────────────────────────────────
    AUDIT_LOGS = "audit_logs"
    FEATURE_USAGE = "feature_usage"
    FLAGS = "flags"

    # ── Licensing ───────────────────────────────────────────────────
    OFFLINE_LICENSES = "offline_licenses"
    LICENSE_TRANSFERS = "license_transfers"

    # ── Misc / Stripe ───────────────────────────────────────────────
    FAILED_REFUNDS = "failed_refunds"
    PURCHASE_ANOMALIES = "purchase_anomalies"

    # ── User Content ────────────────────────────────────────────────
    LIBRARY = "library"
    FILES = "files"
    ITEMS = "items"
    BOOKS = "books"
    MAGAZINES = "magazines"

    # ── Stats & History (often subcollections) ──────────────────────
    STATS = "stats"
    DAILY = "daily"
    HISTORY = "history"

    # ── System ──────────────────────────────────────────────────────
    SYSTEM = "system"
    SYSTEM_CONFIG = "system-config"

    # ── Deletion ────────────────────────────────────────────────────
    ALERTS = "alerts"
