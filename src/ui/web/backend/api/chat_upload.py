"""
Chat file upload.

Accepts multipart file upload, returns a signed URL.
Max file size: 10MB.
Allowed types: images, PDFs, common documents.
"""

from io import BytesIO
import logging

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

from api.auth import get_current_user
from gateway.providers.hub import get_data_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])

_MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Magic bytes for file type validation (content-type → list of accepted signatures)
_MAGIC_BYTES = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "image/webp": [b"RIFF"],  # RIFF....WEBP
    "application/pdf": [b"%PDF"],
    "application/zip": [b"PK\x03\x04", b"PK\x05\x06"],
    "application/msword": [b"\xd0\xcf\x11\xe0"],  # OLE2
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [b"PK\x03\x04"],
    "application/vnd.ms-excel": [b"\xd0\xcf\x11\xe0"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [b"PK\x03\x04"],
}


def _validate_magic_bytes(data: bytes, content_type: str) -> bool:
    """Verify file content matches declared content type via magic bytes."""
    signatures = _MAGIC_BYTES.get(content_type)
    if signatures is None:
        # text/plain, text/csv, application/json — no reliable magic bytes
        return True
    return any(data.startswith(sig) for sig in signatures)


_ALLOWED_CONTENT_TYPES = {
    "image/jpeg", "image/png", "image/gif", "image/webp",
    "application/pdf",
    "text/plain", "text/csv",
    "application/json",
    "application/zip",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


def _storage_unavailable_error() -> HTTPException:
    return HTTPException(status_code=503, detail="File storage not available")


def _get_storage_provider():
    provider = get_data_provider()
    storage_provider = getattr(provider, "storage", None) if provider else None
    if storage_provider is None:
        raise _storage_unavailable_error()
    return storage_provider


@router.post("/upload")
async def upload_chat_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
):
    """
    Upload a file for chat attachment.

    Returns a public URL for the uploaded file.
    Max size: 10MB. Allowed: images, PDFs, documents.
    """
    # Validate content type
    content_type = file.content_type or "application/octet-stream"
    if content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            400,
            f"File type '{content_type}' not allowed. "
            f"Allowed: images, PDFs, documents.",
        )

    # Read and validate size
    data = await file.read()
    if len(data) > _MAX_FILE_SIZE:
        raise HTTPException(400, f"File too large. Max size: {_MAX_FILE_SIZE // (1024*1024)}MB")
    if not data:
        raise HTTPException(400, "Empty file")

    # Validate file magic bytes match declared content type
    if not _validate_magic_bytes(data, content_type):
        raise HTTPException(
            400,
            "File content does not match declared type. "
            "Please upload a valid file.",
        )

    user_id = current_user["id"]
    ext = _extension_from_content_type(content_type)
    filename = file.filename or f"file{ext}"
    storage = _get_storage_provider()

    try:
        upload = await storage.upload_file(
            user_id=user_id,
            file_data=BytesIO(data),
            filename=filename,
            content_type=content_type,
            purpose="chat",
        )
    except NotImplementedError as e:
        raise _storage_unavailable_error() from e
    except Exception as e:
        logger.error("File upload failed: %s", e)
        raise HTTPException(500, "File upload failed")

    return {
        "ok": True,
        "file_id": upload.id,
        "url": upload.url,
        "name": filename,
        "size": len(data),
        "content_type": content_type,
    }


def _extension_from_content_type(ct: str) -> str:
    """Map content type to file extension."""
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "application/pdf": ".pdf",
        "text/plain": ".txt",
        "text/csv": ".csv",
        "application/json": ".json",
        "application/zip": ".zip",
    }
    return mapping.get(ct, "")
