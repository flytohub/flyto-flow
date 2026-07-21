"""
Translation API — Write Operations.

Endpoints: save (patch), import, export.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from api.content.translations.deps import require_admin
from api.content.translations.github_service import (
    github_create_branch,
    github_create_pr,
    github_get_file_content,
    github_get_main_sha,
    github_list_files,
    github_update_file,
)
from api.content.translations.models import ImportTranslationsRequest, SaveTranslationsRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/export/{locale}")
async def export_translations(
    locale: str,
    format: str = Query("json"),
    _: dict = Depends(require_admin),
):
    """
    Export all translations for a locale.
    """
    try:
        files = await github_list_files(locale)
        all_translations = {}

        for f in files:
            try:
                data = await github_get_file_content(locale, f["name"])
                translations = data["content"].get("translations", {})
                all_translations.update(translations)
            except Exception as e:
                logger.warning(f"Error exporting {f['name']}: {e}")

        if format == "json":
            return {
                "ok": True,
                "locale": locale,
                "translations": all_translations,
                "total_keys": len(all_translations)
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/files/{locale}/{filename}")
async def save_translations(
    locale: str,
    filename: str,
    data: SaveTranslationsRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Save translations to a file (PATCH - partial update).

    This updates specific keys without affecting others.
    Creates a PR with the changes.
    """
    try:
        if not data.translations:
            raise HTTPException(status_code=400, detail="No translations to save")

        # Get current file content
        try:
            current = await github_get_file_content(locale, filename)
            content = current["content"]
            sha = current["sha"]
        except HTTPException:
            # File doesn't exist, create new
            content = {
                "$schema": "../../schema/locale.schema.json",
                "locale": locale,
                "category": filename.replace(".json", ""),
                "version": "1.0.0",
                "translations": {}
            }
            sha = None

        # Merge translations
        content["translations"].update(data.translations)

        # Get main branch SHA for new branch
        main_sha = await github_get_main_sha()

        # Create branch
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        user_id = current_user.get("uid", "unknown")[:8]
        branch_name = f"save/{user_id}/{timestamp}"

        await github_create_branch(branch_name, main_sha)

        # Format JSON
        json_content = json.dumps(content, indent=2, ensure_ascii=False) + "\n"

        # Commit message
        commit_msg = data.commit_message or f"chore(i18n): update {locale}/{filename}"

        # Update file
        await github_update_file(
            filepath=f"locales/{locale}/{filename}",
            content=json_content,
            message=commit_msg,
            sha=sha,
            branch=branch_name
        )

        # Create PR
        pr = await github_create_pr(
            title=f"Translation update: {locale}/{filename}",
            body=f"""## Translation Update

Updated translations in `{locale}/{filename}`

**Keys updated:** {len(data.translations)}
**Submitted by:** {current_user.get('email', 'Unknown')}
**Generated at:** {datetime.now().isoformat()}
""",
            head_branch=branch_name
        )

        return {
            "ok": True,
            "message": f"Saved {len(data.translations)} translations",
            "pr_number": pr["number"],
            "pr_url": pr["html_url"],
            "branch": branch_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save translations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_translations_file(
    current_user: dict = Depends(require_admin),
    file: Any = None,  # UploadFile from frontend FormData
    locale: str = Query("zh-TW"),
    format: str = Query("json"),
):
    """
    Import translations from uploaded file.

    Frontend sends FormData with file upload.
    """
    from fastapi import UploadFile, File
    try:
        # For now, return a placeholder response
        # Real implementation would parse the uploaded file
        return {
            "ok": True,
            "imported": 0,
            "message": "File import not yet implemented. Use JSON import endpoint instead."
        }
    except Exception as e:
        logger.error(f"Failed to import file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/{locale}")
async def import_translations(
    locale: str,
    data: ImportTranslationsRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Import translations for a locale (JSON body).

    Bulk import translations, optionally merging with existing.
    Creates a PR with the changes.
    """
    try:
        if not data.translations:
            raise HTTPException(status_code=400, detail="No translations to import")

        # Group translations by file/category
        files_to_update: Dict[str, Dict[str, str]] = {}

        for key, value in data.translations.items():
            # Determine file from key prefix (e.g., "modules.browser.title" -> "modules.browser.json")
            parts = key.split(".")
            if len(parts) >= 2:
                filename = f"{parts[0]}.{parts[1]}.json"
            else:
                filename = "common.json"

            if filename not in files_to_update:
                files_to_update[filename] = {}
            files_to_update[filename][key] = value

        # Get main branch SHA
        main_sha = await github_get_main_sha()

        # Create branch
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        user_id = current_user.get("uid", "unknown")[:8]
        branch_name = f"import/{user_id}/{timestamp}"

        await github_create_branch(branch_name, main_sha)

        # Update each file
        committed_files = []
        for filename, translations in files_to_update.items():
            # Get current content
            try:
                current = await github_get_file_content(locale, filename)
                content = current["content"]
                sha = current["sha"]
            except HTTPException:
                content = {
                    "$schema": "../../schema/locale.schema.json",
                    "locale": locale,
                    "category": filename.replace(".json", ""),
                    "version": "1.0.0",
                    "translations": {}
                }
                sha = None

            # Merge or replace
            if data.merge:
                content["translations"].update(translations)
            else:
                content["translations"] = translations

            # Format and commit
            json_content = json.dumps(content, indent=2, ensure_ascii=False) + "\n"

            await github_update_file(
                filepath=f"locales/{locale}/{filename}",
                content=json_content,
                message=f"chore(i18n): import {locale}/{filename}",
                sha=sha,
                branch=branch_name
            )
            committed_files.append(filename)

        # Create PR
        pr = await github_create_pr(
            title=f"Translation import: {locale} ({len(data.translations)} keys)",
            body=f"""## Translation Import

Imported translations for locale `{locale}`

**Total keys:** {len(data.translations)}
**Files updated:** {len(committed_files)}
{chr(10).join(f'- `{f}`' for f in committed_files)}

**Merge mode:** {'Merge with existing' if data.merge else 'Replace existing'}
**Submitted by:** {current_user.get('email', 'Unknown')}
**Generated at:** {datetime.now().isoformat()}
""",
            head_branch=branch_name
        )

        return {
            "ok": True,
            "message": f"Imported {len(data.translations)} translations to {len(committed_files)} files",
            "pr_number": pr["number"],
            "pr_url": pr["html_url"],
            "branch": branch_name,
            "files_updated": committed_files,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to import translations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
