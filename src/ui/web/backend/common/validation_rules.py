"""
Validation Rules — Single Source of Truth

These constants define validation rules used by both backend validators
and mirrored by frontend for UX responsiveness.
Frontend reads these via GET /api/config/validation-rules.
"""

import re

# =============================================================================
# Password
# =============================================================================
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 128
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_LOWERCASE = True
PASSWORD_REQUIRE_NUMBER = True

# =============================================================================
# Email
# =============================================================================
EMAIL_MAX_LENGTH = 254
EMAIL_PATTERN = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"

# =============================================================================
# Template
# =============================================================================
TEMPLATE_NAME_MIN_LENGTH = 1
TEMPLATE_NAME_MAX_LENGTH = 100
TEMPLATE_DESCRIPTION_MAX_LENGTH = 2000
TEMPLATE_ID_MAX_LENGTH = 50
TEMPLATE_ID_PATTERN = r"^[a-zA-Z0-9_-]+$"

# =============================================================================
# Grid (template builder UI)
# =============================================================================
GRID_COLUMN_TOTAL = 12
GRID_COLUMN_MIN = 1
GRID_COLUMN_MAX = 12

# =============================================================================
# Username
# =============================================================================
USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"

# =============================================================================
# Compiled patterns (for backend use)
# =============================================================================
EMAIL_REGEX = re.compile(EMAIL_PATTERN)
TEMPLATE_ID_REGEX = re.compile(TEMPLATE_ID_PATTERN)
USERNAME_REGEX = re.compile(USERNAME_PATTERN)
