"""
Storage API Routes

Provides file upload and management endpoints.
"""

import logging
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Depends, Query, Response, UploadFile, File, Form

from api.auth import get_current_user
from gateway.providers.hub import get_data_provider
from gateway.providers.data.models import (
    FileUploadDTO,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/storage", tags=["Storage"])

# Blocked MIME types — executable/script types that pose security risks if stored and served back.
# Using a deny-list instead of allow-list because workflows may upload diverse file types.
BLOCKED_MIME_TYPES = frozenset({
    # Executables
    "application/x-executable", "application/x-msdownload", "application/x-msdos-program",
    "application/x-dosexec", "application/vnd.microsoft.portable-executable",
    "application/x-elf", "application/x-mach-binary",
    # Scripts (XSS risk if served back with content-type sniffing)
    "application/javascript", "text/javascript", "application/x-javascript",
    "application/x-sh", "application/x-bash", "application/x-csh",
    "application/x-python-code", "application/x-perl",
    # HTML/XML (XSS risk if served back)
    "text/html", "application/xhtml+xml",
    # Java / .NET
    "application/java-archive", "application/x-java-class",
    "application/x-msdownload", "application/x-ms-installer",
})


# =============================================================================
# Endpoints
# =============================================================================


@router.post("/upload", response_model=FileUploadDTO)
async def upload_file(
    file: UploadFile = File(...),
    purpose: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
):
    """Upload a file"""
    provider = get_data_provider()

    # Validate MIME type — block dangerous types (executables, scripts, HTML)
    content_type = file.content_type or "application/octet-stream"
    if content_type in BLOCKED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed: {content_type}. "
                   f"Executable, script, and HTML files are blocked for security.",
        )

    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024
    content = await file.read()

    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Reset file position for provider
    from io import BytesIO
    file_data = BytesIO(content)

    try:
        result = await provider.storage.upload_file(
            user_id=current_user["id"],
            file_data=file_data,
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            purpose=purpose,
        )
        return result
    except Exception as exc:
        logger.exception("[Storage] Upload failed")
        raise HTTPException(status_code=500, detail="File upload failed") from exc


@router.get("/", response_model=PaginatedResponse)
async def list_files(
    purpose: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    """List user's uploaded files"""
    provider = get_data_provider()
    result = await provider.storage.list_user_files(
        user_id=current_user["id"],
        purpose=purpose,
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/content/{token}/{file_id}.bin")
async def download_file_content(token: str, file_id: str):
    """Serve a private enterprise object through a signed capability URL."""
    provider = get_data_provider()
    storage = provider.storage
    validate_token = getattr(storage, "validate_download_token", None)
    if not callable(validate_token):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        user_id = validate_token(token, file_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="File not found") from exc
    try:
        stored_file = await storage.download_file(user_id=user_id, file_id=file_id)
    except Exception as exc:
        logger.exception("[Storage] Download failed")
        raise HTTPException(status_code=503, detail="File storage unavailable") from exc
    if stored_file is None:
        raise HTTPException(status_code=404, detail="File not found")
    encoded_name = quote(stored_file.filename, safe="")
    return Response(
        content=stored_file.content,
        media_type=stored_file.content_type,
        headers={
            "Cache-Control": "private, max-age=300",
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_name}",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.delete("/{file_id}")
async def delete_file(
    file_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Delete a file"""
    provider = get_data_provider()
    success = await provider.storage.delete_file(
        user_id=current_user["id"],
        file_id=file_id,
    )

    if not success:
        raise HTTPException(status_code=404, detail="File not found")

    return {"ok": True, "message": "File deleted"}
