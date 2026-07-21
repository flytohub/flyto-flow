"""
Config API — Business

Marketplace, subscription, workflow types, form types, and countries configuration.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/marketplace")
async def get_marketplace_config():
    """
    Get marketplace configuration.

    Categories, pricing options, currencies, and visibility settings.
    """
    return {
        "ok": True,
        "categories": [
            {"slug": "browser", "name": "Browser / Scraping", "icon": "Globe", "color": "#3b82f6"},
            {"slug": "data", "name": "Data Processing", "icon": "Database", "color": "#8b5cf6"},
            {"slug": "ai", "name": "AI / LLM", "icon": "Brain", "color": "#ec4899"},
            {"slug": "file", "name": "File Operations", "icon": "FileText", "color": "#f59e0b"},
            {"slug": "http", "name": "HTTP / API", "icon": "Globe", "color": "#10b981"},
            {"slug": "flow", "name": "Flow Control", "icon": "GitBranch", "color": "#6366f1"},
            {"slug": "integration", "name": "Integrations", "icon": "Plug", "color": "#14b8a6"},
            {"slug": "utility", "name": "Utilities", "icon": "Wrench", "color": "#64748b"},
            {"slug": "messaging", "name": "Messaging", "icon": "MessageCircle", "color": "#22c55e"},
            {"slug": "other", "name": "Other", "icon": "Package", "color": "#94a3b8"},
        ],
        "template_status": {
            "draft": {"name": "Draft", "color": "#64748b"},
            "published": {"name": "Published", "color": "#10b981"},
            "archived": {"name": "Archived", "color": "#f59e0b"},
            "rejected": {"name": "Rejected", "color": "#ef4444"},
        },
        "visibility_options": [
            {"id": "public", "name": "Public", "description": "Anyone can discover and use"},
            {"id": "private", "name": "Private", "description": "Only you can see"},
            {"id": "unlisted", "name": "Unlisted", "description": "Only accessible via direct link"},
            {"id": "organization", "name": "Organization", "description": "Only org members can see"},
        ],
        "mutability_options": [
            {"id": "locked", "name": "Locked", "description": "Users cannot modify"},
            {"id": "fork_on_use", "name": "Forkable", "description": "Users get their own copy"},
            {"id": "editable", "name": "Editable", "description": "Users can modify directly"},
        ],
        "currencies": [
            {"code": "USD", "name": "US Dollar", "symbol": "$", "decimal_places": 2},
            {"code": "TWD", "name": "Taiwan Dollar", "symbol": "NT$", "decimal_places": 0},
            {"code": "EUR", "name": "Euro", "symbol": "\u20ac", "decimal_places": 2},
            {"code": "GBP", "name": "British Pound", "symbol": "\u00a3", "decimal_places": 2},
            {"code": "JPY", "name": "Japanese Yen", "symbol": "\u00a5", "decimal_places": 0},
        ],
        "price_suggestions": [
            {"value": 0, "label": "Free"},
            {"value": 299, "label": "$2.99"},
            {"value": 499, "label": "$4.99"},
            {"value": 999, "label": "$9.99"},
            {"value": 1999, "label": "$19.99"},
            {"value": 4999, "label": "$49.99"},
        ],
        "invite_key_usage_options": [
            {"value": None, "label": "Unlimited"},
            {"value": 1, "label": "1 use"},
            {"value": 5, "label": "5 uses"},
            {"value": 10, "label": "10 uses"},
            {"value": 25, "label": "25 uses"},
            {"value": 100, "label": "100 uses"},
        ],
    }


@router.get("/subscription")
async def get_subscription_config():
    """
    Get subscription plans and status configuration.
    """
    return {
        "ok": True,
        "plans": [
            {
                "id": "free",
                "name": "Free",
                "description": "Basic features for personal use",
                "features": ["5 workflows", "100 executions/month", "Community support"],
            },
            {
                "id": "pro",
                "name": "Pro",
                "description": "Advanced features for professionals",
                "features": ["Unlimited workflows", "10,000 executions/month", "Priority support", "API access"],
            },
            {
                "id": "team",
                "name": "Team",
                "description": "Collaboration features for teams",
                "features": ["Everything in Pro", "Team collaboration", "Shared workflows", "Admin dashboard"],
            },
            {
                "id": "enterprise",
                "name": "Enterprise",
                "description": "Custom solutions for organizations",
                "features": ["Everything in Team", "Custom integrations", "SLA", "Dedicated support"],
            },
        ],
        "statuses": [
            {"id": "active", "name": "Active", "color": "#10b981"},
            {"id": "trialing", "name": "Trial", "color": "#3b82f6"},
            {"id": "cancelled", "name": "Cancelled", "color": "#f59e0b"},
            {"id": "expired", "name": "Expired", "color": "#ef4444"},
            {"id": "past_due", "name": "Past Due", "color": "#ef4444"},
        ],
    }


@router.get("/workflow-types")
async def get_workflow_types_config():
    """
    Get workflow node and edge type definitions.
    """
    return {
        "ok": True,
        "node_types": [
            {"id": "standard", "name": "Standard", "description": "Basic execution node"},
            {"id": "branch", "name": "Branch", "description": "Conditional branching"},
            {"id": "switch", "name": "Switch", "description": "Multi-way branching"},
            {"id": "loop", "name": "Loop", "description": "Iteration node"},
            {"id": "merge", "name": "Merge", "description": "Merge multiple branches"},
            {"id": "fork", "name": "Fork", "description": "Parallel execution"},
            {"id": "trigger", "name": "Trigger", "description": "Workflow start point"},
            {"id": "terminal", "name": "Terminal", "description": "Workflow end point"},
            {"id": "subflow", "name": "Subflow", "description": "Embedded workflow"},
            {"id": "comment", "name": "Comment", "description": "Documentation node"},
        ],
        "edge_types": [
            {"id": "control", "name": "Control Flow", "description": "Execution order"},
            {"id": "data", "name": "Data Flow", "description": "Data passing"},
            {"id": "error", "name": "Error Flow", "description": "Error handling path"},
        ],
        "port_types": [
            {"id": "input", "name": "Input", "direction": "in"},
            {"id": "output", "name": "Output", "direction": "out"},
            {"id": "error", "name": "Error", "direction": "out"},
        ],
    }


@router.get("/form-types")
async def get_form_types_config():
    """
    Get form field types and binding types for template builder.
    """
    return {
        "ok": True,
        "form_types": [
            {"id": "input", "name": "Text Input", "icon": "Type"},
            {"id": "number", "name": "Number", "icon": "Hash"},
            {"id": "email", "name": "Email", "icon": "Mail"},
            {"id": "password", "name": "Password", "icon": "Lock"},
            {"id": "url", "name": "URL", "icon": "Link"},
            {"id": "tel", "name": "Phone", "icon": "Phone"},
            {"id": "textarea", "name": "Text Area", "icon": "AlignLeft"},
            {"id": "select", "name": "Dropdown", "icon": "ChevronDown"},
            {"id": "checkbox", "name": "Checkbox", "icon": "CheckSquare"},
            {"id": "radio", "name": "Radio", "icon": "Circle"},
            {"id": "switch", "name": "Switch", "icon": "ToggleLeft"},
            {"id": "date", "name": "Date", "icon": "Calendar"},
            {"id": "time", "name": "Time", "icon": "Clock"},
            {"id": "datetime", "name": "Date & Time", "icon": "CalendarClock"},
            {"id": "range", "name": "Slider", "icon": "Sliders"},
            {"id": "rating", "name": "Rating", "icon": "Star"},
            {"id": "file", "name": "File Upload", "icon": "Upload"},
            {"id": "color", "name": "Color Picker", "icon": "Palette"},
        ],
        "input_types": [
            {"id": "text", "name": "Text"},
            {"id": "number", "name": "Number"},
            {"id": "email", "name": "Email"},
            {"id": "password", "name": "Password"},
            {"id": "url", "name": "URL"},
            {"id": "tel", "name": "Phone"},
            {"id": "date", "name": "Date"},
            {"id": "time", "name": "Time"},
            {"id": "datetime-local", "name": "DateTime"},
            {"id": "file", "name": "File"},
            {"id": "hidden", "name": "Hidden"},
        ],
        "output_types": [
            {"id": "text", "name": "Text", "icon": "Type"},
            {"id": "image", "name": "Image", "icon": "Image"},
            {"id": "file", "name": "File", "icon": "File"},
            {"id": "pdf", "name": "PDF", "icon": "FileText"},
            {"id": "video", "name": "Video", "icon": "Video"},
            {"id": "audio", "name": "Audio", "icon": "Volume2"},
            {"id": "json", "name": "JSON", "icon": "Braces"},
            {"id": "table", "name": "Table", "icon": "Table"},
            {"id": "chart", "name": "Chart", "icon": "BarChart"},
            {"id": "html", "name": "HTML", "icon": "Code"},
            {"id": "markdown", "name": "Markdown", "icon": "FileCode"},
        ],
        "binding_sources": [
            {"id": "static", "name": "Static Value"},
            {"id": "variable", "name": "Variable"},
            {"id": "expression", "name": "Expression"},
            {"id": "step_output", "name": "Step Output"},
            {"id": "env", "name": "Environment"},
            {"id": "secret", "name": "Secret"},
        ],
    }


@router.get("/countries")
async def get_countries_config():
    """
    Get supported countries list (for Stripe, etc.)
    """
    return {
        "ok": True,
        "stripe_supported": [
            {"code": "US", "name": "United States", "flag": "\U0001f1fa\U0001f1f8"},
            {"code": "GB", "name": "United Kingdom", "flag": "\U0001f1ec\U0001f1e7"},
            {"code": "CA", "name": "Canada", "flag": "\U0001f1e8\U0001f1e6"},
            {"code": "AU", "name": "Australia", "flag": "\U0001f1e6\U0001f1fa"},
            {"code": "DE", "name": "Germany", "flag": "\U0001f1e9\U0001f1ea"},
            {"code": "FR", "name": "France", "flag": "\U0001f1eb\U0001f1f7"},
            {"code": "JP", "name": "Japan", "flag": "\U0001f1ef\U0001f1f5"},
            {"code": "SG", "name": "Singapore", "flag": "\U0001f1f8\U0001f1ec"},
            {"code": "HK", "name": "Hong Kong", "flag": "\U0001f1ed\U0001f1f0"},
            {"code": "NL", "name": "Netherlands", "flag": "\U0001f1f3\U0001f1f1"},
            {"code": "SE", "name": "Sweden", "flag": "\U0001f1f8\U0001f1ea"},
            {"code": "NO", "name": "Norway", "flag": "\U0001f1f3\U0001f1f4"},
            {"code": "DK", "name": "Denmark", "flag": "\U0001f1e9\U0001f1f0"},
            {"code": "FI", "name": "Finland", "flag": "\U0001f1eb\U0001f1ee"},
            {"code": "IE", "name": "Ireland", "flag": "\U0001f1ee\U0001f1ea"},
            {"code": "NZ", "name": "New Zealand", "flag": "\U0001f1f3\U0001f1ff"},
            {"code": "AT", "name": "Austria", "flag": "\U0001f1e6\U0001f1f9"},
            {"code": "BE", "name": "Belgium", "flag": "\U0001f1e7\U0001f1ea"},
            {"code": "CH", "name": "Switzerland", "flag": "\U0001f1e8\U0001f1ed"},
            {"code": "ES", "name": "Spain", "flag": "\U0001f1ea\U0001f1f8"},
            {"code": "IT", "name": "Italy", "flag": "\U0001f1ee\U0001f1f9"},
            {"code": "PT", "name": "Portugal", "flag": "\U0001f1f5\U0001f1f9"},
            {"code": "PL", "name": "Poland", "flag": "\U0001f1f5\U0001f1f1"},
            {"code": "CZ", "name": "Czech Republic", "flag": "\U0001f1e8\U0001f1ff"},
            {"code": "MX", "name": "Mexico", "flag": "\U0001f1f2\U0001f1fd"},
            {"code": "BR", "name": "Brazil", "flag": "\U0001f1e7\U0001f1f7"},
            {"code": "MY", "name": "Malaysia", "flag": "\U0001f1f2\U0001f1fe"},
            {"code": "TH", "name": "Thailand", "flag": "\U0001f1f9\U0001f1ed"},
            {"code": "PH", "name": "Philippines", "flag": "\U0001f1f5\U0001f1ed"},
            {"code": "IN", "name": "India", "flag": "\U0001f1ee\U0001f1f3"},
            {"code": "AE", "name": "United Arab Emirates", "flag": "\U0001f1e6\U0001f1ea"},
            {"code": "IL", "name": "Israel", "flag": "\U0001f1ee\U0001f1f1"},
            {"code": "GR", "name": "Greece", "flag": "\U0001f1ec\U0001f1f7"},
            {"code": "RO", "name": "Romania", "flag": "\U0001f1f7\U0001f1f4"},
        ],
    }
