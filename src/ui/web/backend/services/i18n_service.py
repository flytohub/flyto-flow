"""
i18n Translation Service

Loads translations from flyto-i18n repository and provides lookup.
Used to translate module labels/descriptions based on user's locale.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache for loaded translations
_translations_cache: Dict[str, Dict[str, str]] = {}

# Path to flyto-i18n locales
# Priority: env var > monorepo sibling > PyInstaller bundled (static/locales)
def _resolve_i18n_path() -> str:
    """Resolve the path to flyto-i18n locale files."""
    env_path = os.environ.get("FLYTO_I18N_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # Dev: monorepo sibling (flyto-cloud/../flyto-i18n/locales)
    monorepo_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent / "flyto-i18n" / "locales"
    if monorepo_path.exists():
        return str(monorepo_path)

    # Desktop app: PyInstaller bundled in static/locales
    base = getattr(sys, '_MEIPASS', Path(__file__).parent.parent)
    bundled_path = Path(base) / "static" / "locales"
    if bundled_path.exists():
        return str(bundled_path)

    # Fallback to monorepo path (will log warning when locale not found)
    return str(monorepo_path)

FLYTO_I18N_PATH = _resolve_i18n_path()


def _load_locale_translations(locale: str) -> Dict[str, str]:
    """
    Load all translations for a locale from flyto-i18n.

    Args:
        locale: Locale code (e.g., 'zh-TW', 'en', 'ja')

    Returns:
        Dict of translation key -> translated text
    """
    translations = {}
    locale_path = Path(FLYTO_I18N_PATH) / locale

    if not locale_path.exists():
        logger.warning(f"[i18n] Locale directory not found: {locale_path}")
        return translations

    # Load all JSON files in the locale directory
    for json_file in locale_path.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Each file has { "translations": { "key": "value" } }
                file_translations = data.get("translations", {})
                translations.update(file_translations)
        except Exception as e:
            logger.warning(f"[i18n] Error loading {json_file}: {e}")

    logger.info(f"[i18n] Loaded {len(translations)} translations for locale '{locale}'")
    return translations


def _normalize_locale(locale: str) -> str:
    """
    Normalize locale code to match flyto-i18n directory names.

    Args:
        locale: Input locale (e.g., 'zh', 'zh-TW', 'en')

    Returns:
        Normalized locale matching flyto-i18n directories
    """
    # Mapping from short codes to full locale codes
    LOCALE_MAP = {
        "zh": "zh-TW",
        "ja": "ja",
        "en": "en",
    }
    return LOCALE_MAP.get(locale, locale)


def get_translations(locale: str) -> Dict[str, str]:
    """
    Get translations for a locale (cached).

    Args:
        locale: Locale code (e.g., 'zh-TW', 'zh', 'en')

    Returns:
        Dict of translation key -> translated text
    """
    # Normalize locale (e.g., 'zh' -> 'zh-TW')
    normalized_locale = _normalize_locale(locale)

    if normalized_locale not in _translations_cache:
        _translations_cache[normalized_locale] = _load_locale_translations(normalized_locale)
    return _translations_cache[normalized_locale]


def translate(key: Optional[str], locale: str, fallback: str = "") -> str:
    """
    Translate a key to the specified locale.

    Args:
        key: Translation key (e.g., 'modules.http.request.label')
        locale: Locale code (e.g., 'zh-TW')
        fallback: Fallback value if translation not found

    Returns:
        Translated text or fallback
    """
    if not key:
        return fallback

    translations = get_translations(locale)
    return translations.get(key, fallback)


def translate_module(
    label: str,
    description: str,
    label_key: Optional[str],
    description_key: Optional[str],
    locale: str
) -> tuple[str, str]:
    """
    Translate module label and description.

    Args:
        label: Original label (fallback)
        description: Original description (fallback)
        label_key: Translation key for label
        description_key: Translation key for description
        locale: Target locale

    Returns:
        Tuple of (translated_label, translated_description)
    """
    # Skip translation for English (source language)
    if locale == "en":
        return label, description

    translated_label = translate(label_key, locale, label)
    translated_description = translate(description_key, locale, description)

    return translated_label, translated_description


def sync_translations(locale: str, translations: Dict[str, str]) -> int:
    """
    Accept module translations pushed from the frontend (after CDN hot-update).

    Frontend filters to modules.* keys only before sending.
    Merges into cache — CDN data takes priority over bundled files.
    """
    normalized = _normalize_locale(locale)

    if normalized not in _translations_cache:
        _translations_cache[normalized] = _load_locale_translations(normalized)

    _translations_cache[normalized].update(translations)
    count = len(translations)
    logger.info(f"[i18n] Synced {count} module translations for '{normalized}' from frontend")
    return count


def clear_cache():
    """Clear the translation cache."""
    _translations_cache.clear()
    logger.info("[i18n] Translation cache cleared")


def get_available_locales() -> list[str]:
    """Get list of available locales."""
    locales_path = Path(FLYTO_I18N_PATH)
    if not locales_path.exists():
        return ["en"]

    return [
        d.name for d in locales_path.iterdir()
        if d.is_dir() and not d.name.startswith(".")
    ]
