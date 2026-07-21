"""
Config API — UI

Timing, layout, theme, limits, and keyboard shortcuts configuration.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/timing")
async def get_timing_config():
    """
    Get timing configuration for frontend.

    S-Grade: All timing values are centralized here.
    Frontend should never hardcode intervals/durations.
    """
    return {
        "ok": True,
        "timing": {
            "polling": {
                "execution_status": 1000,
                "debug_status": 1000,
                "replay": 1000,
                "recording": 3000,
                "default": 2000,
            },
            "notifications": {
                "success_duration": 3000,
                "warning_duration": 4000,
                "error_duration": 5000,
                "info_duration": 3000,
            },
            "debounce": {
                "search": 300,
                "input": 200,
                "resize": 100,
            },
            "animation": {
                "transition": 200,
                "fade": 150,
            },
        },
    }


@router.get("/layout")
async def get_layout_config():
    """
    Get layout configuration for workflow editor.

    S-Grade: All layout values are centralized here.
    Frontend should never hardcode spacing/dimensions.
    Values sourced from config/layout.py LAYOUT_CONFIG (SSOT).
    """
    from config.layout import LAYOUT_CONFIG

    return {
        "ok": True,
        "layout": {
            "workflow": {
                "horizontal_spacing": LAYOUT_CONFIG["horizontal_spacing"],
                "vertical_spacing": LAYOUT_CONFIG["vertical_spacing"],
                "initial_x": LAYOUT_CONFIG["initial_x"],
                "initial_y": LAYOUT_CONFIG["initial_y"],
                "node_width": LAYOUT_CONFIG["node_width"],
                "node_height": LAYOUT_CONFIG["node_height"],
            },
            "canvas": {
                "min_zoom": 0.1,
                "max_zoom": 2.0,
                "default_zoom": 1.0,
                "fit_padding": 50,
            },
        },
    }


@router.get("/theme")
async def get_theme_config():
    """
    Get theme configuration for UI components.

    S-Grade: All colors are centralized here.
    Frontend should never hardcode color values.
    """
    return {
        "ok": True,
        "theme": {
            "colors": {
                "primary": "#3b82f6",
                "secondary": "#8b5cf6",
                "success": "#10b981",
                "warning": "#f59e0b",
                "error": "#ef4444",
                "info": "#3b82f6",
            },
            "particles": {
                "colors": ["#3b82f6", "#8b5cf6", "#06b6d4"],
                "count": 50,
                "speed": 1.0,
            },
            "charts": {
                "palette": ["#3b82f6", "#10b981", "#f59e0b", "#ef4444"],
            },
            "status": {
                "running": "#3b82f6",
                "success": "#10b981",
                "failed": "#ef4444",
                "pending": "#6b7280",
                "cancelled": "#9ca3af",
            },
        },
    }


@router.get("/limits")
async def get_limits_config():
    """
    Get data limits configuration.

    S-Grade: All limits are centralized here.
    Frontend should never hardcode size/count limits.
    """
    return {
        "ok": True,
        "limits": {
            "logs": {
                "max_entries": 1000,
                "max_line_length": 10000,
            },
            "files": {
                "max_size_bytes": 10485760,  # 10MB
                "allowed_types": ["image/*", "application/pdf", ".json", ".yaml", ".yml"],
            },
            "strings": {
                "max_name_length": 255,
                "max_description_length": 2000,
            },
            "pagination": {
                "default_page_size": 20,
                "available_sizes": [10, 20, 50, 100],
            },
            "workflow": {
                "max_steps": 100,
                "max_parallel_executions": 10,
            },
        },
    }


@router.get("/shortcuts")
async def get_shortcuts_config():
    """
    Get keyboard shortcuts configuration.

    S-Grade: All shortcuts are centralized here.
    Frontend should never hardcode key bindings.
    """
    return {
        "ok": True,
        "shortcuts": {
            "workflow": {
                "save": "Ctrl+S",
                "undo": "Ctrl+Z",
                "redo": "Ctrl+Shift+Z",
                "delete": "Delete",
                "copy": "Ctrl+C",
                "paste": "Ctrl+V",
                "select_all": "Ctrl+A",
                "deselect": "Escape",
                "fit_view": "Ctrl+0",
                "zoom_in": "Ctrl+=",
                "zoom_out": "Ctrl+-",
            },
            "global": {
                "search": "Ctrl+K",
                "help": "F1",
                "settings": "Ctrl+,",
            },
        },
    }
