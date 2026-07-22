"""Offline-safe icon normalization."""

from typing import Any, Dict, Optional


def _is_embedded_image(value: str) -> bool:
    return value.startswith("data:image/")


def normalize_icon(raw: Any, color: Optional[str] = None) -> Dict[str, str]:
    """Return a bundled Lucide icon or an embedded image, never a remote URL."""
    del color
    if not raw:
        return {"type": "lucide", "value": "Box"}

    if isinstance(raw, dict):
        icon_type = raw.get("type", "lucide")
        value = str(raw.get("value") or raw.get("name") or raw.get("url") or "Box")
        if icon_type == "url":
            return (
                {"type": "url", "value": value}
                if _is_embedded_image(value)
                else {"type": "lucide", "value": "Box"}
            )
        return {"type": "lucide", "value": _normalize_lucide_name(value)}

    if isinstance(raw, str):
        if _is_embedded_image(raw):
            return {"type": "url", "value": raw}
        if raw.startswith(("http://", "https://")):
            return {"type": "lucide", "value": "Box"}
        if ":" in raw:
            prefix, name = raw.split(":", 1)
            if prefix == "lucide":
                return {"type": "lucide", "value": _normalize_lucide_name(name)}
            return {"type": "lucide", "value": "Box"}
        return {"type": "lucide", "value": _normalize_lucide_name(raw)}

    return {"type": "lucide", "value": "Box"}


def _normalize_lucide_name(name: str) -> str:
    """Normalize a Lucide icon name to PascalCase."""
    if not name:
        return "Box"
    if "-" in name or "_" in name:
        return "".join(part.capitalize() for part in name.replace("_", "-").split("-"))
    if name[0].islower():
        return name[0].upper() + name[1:]
    return name
