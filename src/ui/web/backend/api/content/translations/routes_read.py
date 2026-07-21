"""
Translation API — Read Operations.

Endpoints: list files, get file content, get stats.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query

from api.content.translations.deps import require_admin
from api.content.translations.github_service import (
    calculate_stats,
    github_get,
    github_get_file_content,
    github_list_files,
)
from api.content.translations.models import TranslationEntry, TranslationFile

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/files")
async def list_translation_files(
    locale: str = Query("zh-TW"),
    _: dict = Depends(require_admin),
):
    """
    List all translation files for a locale.
    Stats are loaded lazily when a file is selected.
    """
    try:
        # Get available locales
        locales_data = await github_get("contents/locales")
        locales = [
            {"code": d["name"], "name": d["name"]}
            for d in locales_data
            if d["type"] == "dir"
        ]

        # Get English files (base) - just the file list, no content
        en_files = await github_list_files("en")

        # Get locale files to check which exist
        locale_files = await github_list_files(locale)
        locale_filenames = {f["name"] for f in locale_files}

        files = []
        for f in en_files:
            filename = f["name"]
            name = filename.replace(".json", "")
            category = name.split(".")[0] if "." in name else "other"

            # Just mark if locale file exists, don't fetch content yet
            has_locale_file = filename in locale_filenames

            files.append(TranslationFile(
                name=name,
                filename=filename,
                locale=locale,
                category=category,
                key_count=0,  # Will be loaded when file is selected
                translated_count=0,
                completion=100 if has_locale_file else 0  # Rough estimate
            ))

        # Sort by category then name
        files.sort(key=lambda x: (x.category, x.name))

        return {
            "ok": True,
            "files": [f.model_dump() for f in files],
            "locales": locales,
            "total_files": len(files),
            "locale": locale
        }
    except Exception as e:
        logger.error(f"Failed to list translation files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/{locale}/{filename}")
async def get_translation_file(
    locale: str,
    filename: str,
    _: dict = Depends(require_admin),
):
    """
    Get content of a translation file with English base for comparison.
    """
    try:
        # Get English base
        en_data = await github_get_file_content("en", filename)
        en_translations = en_data["content"].get("translations", {})

        # Get locale translations
        try:
            locale_data = await github_get_file_content(locale, filename)
            locale_translations = locale_data["content"].get("translations", {})
            locale_sha = locale_data["sha"]
        except HTTPException:
            locale_translations = {}
            locale_sha = None

        # Build entries
        entries = []
        for key, source in en_translations.items():
            value = locale_translations.get(key, "")
            entries.append(TranslationEntry(
                key=key,
                source=source,
                value=value,
                is_empty=not value,
                is_modified=False
            ))

        # Sort by key
        entries.sort(key=lambda x: x.key)

        stats = calculate_stats(en_data["content"], {"translations": locale_translations})

        return {
            "ok": True,
            "filename": filename,
            "locale": locale,
            "source": en_translations,       # English source texts
            "translations": locale_translations,  # Current locale translations
            "entries": [e.model_dump() for e in entries],
            "total": len(entries),
            "sha": locale_sha,
            "en_sha": en_data["sha"],
            **stats
        }
    except Exception as e:
        logger.error(f"Failed to get translation file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_translation_stats(
    _: dict = Depends(require_admin),
):
    """
    Get overall translation statistics for all locales.
    """
    try:
        # Get English files
        en_files = await github_list_files("en")

        # Get available locales
        locales_data = await github_get("contents/locales")
        locales = [d["name"] for d in locales_data if d["type"] == "dir" and d["name"] != "en"]

        stats = {
            "locales": {},
            "total_files": len(en_files),
            "base_locale": "en"
        }

        for locale in locales:
            locale_files = await github_list_files(locale)
            total_keys = 0
            translated_keys = 0

            for f in en_files[:5]:  # Sample first 5 files for speed
                try:
                    en_data = await github_get_file_content("en", f["name"])
                    try:
                        locale_data = await github_get_file_content(locale, f["name"])
                    except HTTPException as e:
                        if e.status_code != 404:
                            raise  # auth/timeout/5xx must not masquerade as "untranslated"
                        # Locale file doesn't exist yet — treat as untranslated.
                        locale_data = {"content": {"translations": {}}}

                    en_trans = en_data["content"].get("translations", {})
                    loc_trans = locale_data["content"].get("translations", {})

                    total_keys += len(en_trans)
                    translated_keys += sum(1 for k in en_trans if loc_trans.get(k))
                except Exception as e:
                    logger.warning(f"Error getting stats for {locale}/{f['name']}: {e}")

            stats["locales"][locale] = {
                "total_keys": total_keys,
                "translated_keys": translated_keys,
                "completion": round((translated_keys / total_keys * 100) if total_keys > 0 else 0, 1),
                "files_count": len(locale_files)
            }

        return {"ok": True, "stats": stats}
    except Exception as e:
        logger.error(f"Failed to get translation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
