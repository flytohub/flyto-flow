"""
Translation API — GitHub PR Operations.

Endpoints: create PR, get PR status, list PRs.
"""

import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from api.content.translations.deps import require_admin
from api.content.translations.github_service import (
    github_create_branch,
    github_create_pr,
    github_get_file_content,
    github_get_main_sha,
    github_get_pr,
    github_list_prs,
    github_update_file,
)
from api.content.translations.models import CreatePRRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/github/pr")
async def create_translation_pr(
    data: CreatePRRequest,
    current_user: dict = Depends(require_admin),
):
    """
    Create a PR with translation changes.
    """
    try:
        if not data.files:
            raise HTTPException(status_code=400, detail="No files to commit")

        # Get main branch SHA
        main_sha = await github_get_main_sha()

        # Create branch
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        user_id = current_user.get("uid", "unknown")[:8]
        branch_name = f"translations/{user_id}/{timestamp}"

        await github_create_branch(branch_name, main_sha)

        # Commit each file
        committed_files = []
        for filepath, translations in data.files.items():
            # Parse locale and filename from filepath
            parts = filepath.split("/")
            if len(parts) >= 2:
                locale = parts[0]
                filename = parts[1]
            else:
                continue

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
            content["translations"].update(translations)

            # Format JSON
            json_content = json.dumps(content, indent=2, ensure_ascii=False) + "\n"

            # Commit file
            await github_update_file(
                filepath=f"locales/{locale}/{filename}",
                content=json_content,
                message=f"chore(i18n): update {locale}/{filename}",
                sha=sha,
                branch=branch_name
            )
            committed_files.append(f"{locale}/{filename}")

        # Create PR
        title = data.title or f"Translation updates ({', '.join(committed_files[:3])})"
        if len(committed_files) > 3:
            title += f" and {len(committed_files) - 3} more"

        description = data.description or f"""## Translation Updates

Updated translations in the following files:
{chr(10).join(f'- `{f}`' for f in committed_files)}

**Submitted by:** {current_user.get('email', 'Unknown')}
**Generated at:** {datetime.now().isoformat()}
"""

        pr = await github_create_pr(
            title=title,
            body=description,
            head_branch=branch_name
        )

        return {
            "ok": True,
            "pr_number": pr["number"],
            "pr_url": pr["html_url"],
            "branch": branch_name,
            "files_committed": committed_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create PR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/github/pr/{pr_number}")
async def get_pr_status(
    pr_number: int,
    _: dict = Depends(require_admin),
):
    """
    Get status of a pull request.
    """
    try:
        pr = await github_get_pr(pr_number)
        return {
            "ok": True,
            "pr": {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "merged": pr.get("merged", False),
                "mergeable": pr.get("mergeable"),
                "html_url": pr["html_url"],
                "created_at": pr["created_at"],
                "updated_at": pr["updated_at"],
                "user": pr["user"]["login"]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get PR status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/github/prs")
async def list_translation_prs(
    state: str = Query("open"),
    _: dict = Depends(require_admin),
):
    """
    List translation pull requests.
    """
    try:
        prs = await github_list_prs(state)

        # Filter to translation PRs only
        translation_prs = [
            {
                "number": pr["number"],
                "title": pr["title"],
                "state": pr["state"],
                "merged": pr.get("merged", False),
                "html_url": pr["html_url"],
                "created_at": pr["created_at"],
                "user": pr["user"]["login"]
            }
            for pr in prs
            if pr["head"]["ref"].startswith("translations/")
        ]

        return {
            "ok": True,
            "prs": translation_prs,
            "total": len(translation_prs)
        }
    except Exception as e:
        logger.error(f"Failed to list PRs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
