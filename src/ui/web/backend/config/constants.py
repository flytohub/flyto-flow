"""
Application Constants
Non-configurable constant values
"""

from config.version import APP_VERSION


APP_NAME = 'Flyto2'

# Categories visible by default in the UI
DEFAULT_VISIBILITY_CATEGORIES = frozenset({
    'browser',
    'element',
    'flow',
    'api',
    'ai',  # AI Agent, LLM modules
})

# Category to icon/color mapping for frontend display
CATEGORY_DEFAULTS = {
    'browser': {
        'icon': 'Globe',
        'color': '#5CB85C',
        'nodeType': 'browser'
    },
    'element': {
        'icon': 'MousePointer',
        'color': '#5BC0DE',
        'nodeType': 'browser'
    },
    'data': {
        'icon': 'Database',
        'color': '#F0AD4E',
        'nodeType': 'data'
    },
    'file': {
        'icon': 'File',
        'color': '#777777',
        'nodeType': 'data'
    },
    'string': {
        'icon': 'Type',
        'color': '#D9534F',
        'nodeType': 'data'
    },
    'text': {
        'icon': 'Type',
        'color': '#D9534F',
        'nodeType': 'data'
    },
    'array': {
        'icon': 'List',
        'color': '#5CB85C',
        'nodeType': 'data'
    },
    'object': {
        'icon': 'Braces',
        'color': '#337AB7',
        'nodeType': 'data'
    },
    'math': {
        'icon': 'Calculator',
        'color': '#337AB7',
        'nodeType': 'data'
    },
    'datetime': {
        'icon': 'Calendar',
        'color': '#5BC0DE',
        'nodeType': 'data'
    },
    'api': {
        'icon': 'Cloud',
        'color': '#F0AD4E',
        'nodeType': 'api'
    },
    'ai': {
        'icon': 'Brain',
        'color': '#9B59B6',
        'nodeType': 'ai'
    },
    'flow': {
        'icon': 'GitBranch',
        'color': '#E74C3C',
        'nodeType': 'logic'
    },
    'logic': {
        'icon': 'GitBranch',
        'color': '#E74C3C',
        'nodeType': 'logic'
    },
    'utility': {
        'icon': 'Settings',
        'color': '#95A5A6',
        'nodeType': 'utility'
    },
    'core': {
        'icon': 'Box',
        'color': '#6C757D',
        'nodeType': 'core'
    },
    'test': {
        'icon': 'CircleCheck',
        'color': '#28A745',
        'nodeType': 'utility'
    },
    'meta': {
        'icon': 'Info',
        'color': '#17A2B8',
        'nodeType': 'utility'
    },
    'image': {
        'icon': 'Image',
        'color': '#E83E8C',
        'nodeType': 'data'
    },
    'notification': {
        'icon': 'Bell',
        'color': '#FFC107',
        'nodeType': 'api'
    },
    'communication': {
        'icon': 'MessageSquare',
        'color': '#20C997',
        'nodeType': 'api'
    },
    'db': {
        'icon': 'Database',
        'color': '#6610F2',
        'nodeType': 'api'
    },
    'cloud': {
        'icon': 'Cloud',
        'color': '#007BFF',
        'nodeType': 'api'
    },
    'payment': {
        'icon': 'CreditCard',
        'color': '#28A745',
        'nodeType': 'api'
    },
    'productivity': {
        'icon': 'Briefcase',
        'color': '#FD7E14',
        'nodeType': 'api'
    },
    'agent': {
        'icon': 'Bot',
        'color': '#6F42C1',
        'nodeType': 'ai'
    },
    'developer': {
        'icon': 'Code',
        'color': '#333333',
        'nodeType': 'developer'
    },
    'scraper': {
        'icon': 'Download',
        'color': '#5BC0DE',
        'nodeType': 'composite'
    },
    'pdf': {
        'icon': 'FileText',
        'color': '#DC3545',
        'nodeType': 'composite'
    },
    'ecommerce': {
        'icon': 'ShoppingCart',
        'color': '#FF6600',
        'nodeType': 'composite'
    },
    'social': {
        'icon': 'Share2',
        'color': '#1DA1F2',
        'nodeType': 'composite'
    },
}

# Default category metadata when category is unknown
DEFAULT_CATEGORY_META = {
    'icon': 'Box',
    'color': '#6C757D',
    'nodeType': 'utility'
}


def get_category_defaults(category: str) -> dict:
    """Get category defaults with fallback"""
    return CATEGORY_DEFAULTS.get(category.lower(), DEFAULT_CATEGORY_META)
