"""
Icon Normalization Utilities

Functions for normalizing icon inputs to unified IconSpec format.
"""

from typing import Dict, Any, Optional


def normalize_icon(raw: Any, color: Optional[str] = None) -> Dict[str, str]:
    """
    Normalize any icon input to unified IconSpec format.

    Backend is single source of truth - frontend receives ready-to-use icon data:
    - { "type": "lucide", "value": "Package" } for Lucide icons
    - { "type": "url", "value": "https://..." } for URLs / data URLs / Iconify CDN

    Input handling:
    - None -> {"type": "lucide", "value": "Box"}
    - "Globe" -> {"type": "lucide", "value": "Globe"}
    - "https://..." -> {"type": "url", "value": "https://..."}
    - {"name": "X"} -> {"type": "lucide", "value": "X"}
    - {"type": "url", "url": "..."} -> {"type": "url", "value": "..."}
    - {"type": "lucide", "name": "Y"} -> {"type": "lucide", "value": "Y"}
    - "simple-icons:openai" -> {"type": "url", "value": "https://api.iconify.design/..."}

    Args:
        raw: Icon value in any supported format
        color: Optional color for Iconify CDN icons

    Returns:
        Unified IconSpec: {"type": "lucide"|"url", "value": str}
    """
    # Default icon
    if not raw:
        return {"type": "lucide", "value": "Box"}

    # Already an object/dict
    if isinstance(raw, dict):
        icon_type = raw.get("type", "lucide")

        # Handle old format with "name" or "url" keys
        if icon_type == "lucide":
            value = raw.get("value") or raw.get("name") or "Box"
            return {"type": "lucide", "value": _normalize_lucide_name(value)}
        elif icon_type == "url":
            value = raw.get("value") or raw.get("url") or ""
            return {"type": "url", "value": value}
        else:
            # Unknown type, try to extract value
            value = raw.get("value") or raw.get("name") or raw.get("url") or "Box"
            if value.startswith(("http://", "https://", "data:")):
                return {"type": "url", "value": value}
            return {"type": "lucide", "value": _normalize_lucide_name(value)}

    # String input
    if isinstance(raw, str):
        # URL icons (http/https, data: base64)
        if raw.startswith(("http://", "https://", "data:")):
            return {"type": "url", "value": raw}

        # Iconify format (prefix:name like simple-icons:openai)
        if ":" in raw and not raw.startswith("http"):
            prefix, name = raw.split(":", 1)
            url = f"https://api.iconify.design/{prefix}/{name}.svg"
            if color:
                color_param = color if color.startswith("#") else f"#{color}"
                url += f"?color={color_param}&width=24&height=24"
            else:
                url += "?width=24&height=24"
            return {"type": "url", "value": url}

        # Lucide icon name
        return {"type": "lucide", "value": _normalize_lucide_name(raw)}

    # Fallback
    return {"type": "lucide", "value": "Box"}


def _normalize_lucide_name(name: str) -> str:
    """Normalize Lucide icon name to PascalCase."""
    if not name:
        return "Box"

    # Convert kebab-case or snake_case to PascalCase
    if "-" in name or "_" in name:
        parts = name.replace("_", "-").split("-")
        return "".join(part.capitalize() for part in parts)

    # Capitalize first letter if needed
    if name[0].islower():
        return name[0].upper() + name[1:]

    return name
