"""
Module Access Control Service

Provides module-level access control based on user permissions,
subscription plans, and purchased modules.

Access Levels:
- FREE: Modules available to all users
- SUBSCRIPTION: Requires active subscription (pro/team/enterprise)
- PURCHASED: Requires individual module purchase
- ORG_SHARED: Available through organization sharing
- PERSONAL: User-created custom modules
"""

import logging
from enum import Enum
from typing import Set, List, Optional, Dict, Any
from dataclasses import dataclass, field

from gateway.providers.base import UserInfo

logger = logging.getLogger(__name__)


class AccessLevel(str, Enum):
    """Module access level types"""
    FREE = 'free'
    SUBSCRIPTION = 'subscription'
    PURCHASED = 'purchased'
    ORG_SHARED = 'org_shared'
    PERSONAL = 'personal'


class SubscriptionPlan(str, Enum):
    """Subscription plan types"""
    FREE = 'free'
    PRO = 'pro'
    TEAM = 'team'
    ENTERPRISE = 'enterprise'


@dataclass
class ModuleAccessConfig:
    """
    Configuration for module access control.

    Defines which modules are available at each access level.
    """
    # Modules available to all users (no subscription required)
    free_modules: Set[str] = field(default_factory=lambda: {
        # Basic flow control
        'flow.start',
        'flow.end',
        'flow.branch',
        'flow.trigger',
        'flow.switch',
        'flow.foreach',
        'flow.loop',
        'flow.merge',
        'flow.fork',
        'flow.join',
        # String operations
        'string.uppercase',
        'string.lowercase',
        'string.trim',
        'string.concat',
        'string.replace',
        'string.split',
        'string.join',
        'string.length',
        # Array operations
        'array.length',
        'array.first',
        'array.last',
        'array.push',
        'array.pop',
        'array.slice',
        # Object operations
        'object.get',
        'object.set',
        'object.keys',
        'object.values',
        # Math operations
        'math.add',
        'math.subtract',
        'math.multiply',
        'math.divide',
        'math.round',
        # Data operations
        'data.transform',
        'data.filter',
        # Debug
        'debug.log',
    })

    # Module categories available with subscription
    subscription_categories: Set[str] = field(default_factory=lambda: {
        'http',
        'api',
        'file',
        'database',
        'ai',
        'browser',
        'notification',
        'schedule',
        'webhook',
        'llm',
    })

    # Modules that require enterprise plan
    enterprise_modules: Set[str] = field(default_factory=lambda: {
        'flow.invoke',
        'flow.container',
        'security.encrypt',
        'security.decrypt',
        'audit.log',
        'compliance.check',
    })


# Global config instance
_config = ModuleAccessConfig()


class ModuleAccessService:
    """
    Service for checking and filtering module access based on user permissions.

    Usage:
        service = ModuleAccessService()
        accessible = await service.get_accessible_modules(user)
        can_use = await service.check_module_access(user, 'http.request')
    """

    def __init__(self, config: Optional[ModuleAccessConfig] = None):
        """
        Initialize the service.

        Args:
            config: Optional custom configuration
        """
        self.config = config or _config
        self._purchased_cache: Dict[str, Set[str]] = {}
        self._org_shared_cache: Dict[str, Set[str]] = {}

    async def get_accessible_modules(
        self,
        user: Optional[UserInfo],
        include_all_ids: bool = False
    ) -> Set[str]:
        """
        Get all module IDs that a user can access.

        Args:
            user: User info (None for anonymous)
            include_all_ids: If True, return all accessible module IDs;
                           if False, return only the filter criteria

        Returns:
            Set of accessible module IDs
        """
        accessible = set(self.config.free_modules)

        if user is None:
            return accessible

        # Check subscription
        plan = self._get_subscription_plan(user)
        if plan in (SubscriptionPlan.PRO, SubscriptionPlan.TEAM, SubscriptionPlan.ENTERPRISE):
            if self._is_subscription_active(user):
                # Add all subscription-level modules
                accessible.update(self._get_subscription_modules())

        # Check enterprise features
        if plan == SubscriptionPlan.ENTERPRISE:
            accessible.update(self.config.enterprise_modules)

        # Add purchased modules
        purchased = await self._get_purchased_modules(user.id)
        accessible.update(purchased)

        # Add organization shared modules
        if user.organization_id:
            org_modules = await self._get_org_shared_modules(user.organization_id)
            accessible.update(org_modules)

        # Add personal/custom modules
        personal = await self._get_personal_modules(user.id)
        accessible.update(personal)

        return accessible

    async def check_module_access(
        self,
        user: Optional[UserInfo],
        module_id: str
    ) -> bool:
        """
        Check if a user can use a specific module.

        Args:
            user: User info (None for anonymous)
            module_id: Module ID to check

        Returns:
            True if user can access the module
        """
        # Free modules are always accessible
        if module_id in self.config.free_modules:
            return True

        if user is None:
            return False

        # Check subscription-level access
        plan = self._get_subscription_plan(user)
        category = module_id.split('.')[0] if '.' in module_id else module_id

        if category in self.config.subscription_categories:
            if plan in (SubscriptionPlan.PRO, SubscriptionPlan.TEAM, SubscriptionPlan.ENTERPRISE):
                if self._is_subscription_active(user):
                    return True

        # Check enterprise modules
        if module_id in self.config.enterprise_modules:
            if plan == SubscriptionPlan.ENTERPRISE and self._is_subscription_active(user):
                return True

        # Check purchased modules
        purchased = await self._get_purchased_modules(user.id)
        if module_id in purchased:
            return True

        # Check organization shared
        if user.organization_id:
            org_modules = await self._get_org_shared_modules(user.organization_id)
            if module_id in org_modules:
                return True

        # Check personal modules
        personal = await self._get_personal_modules(user.id)
        if module_id in personal:
            return True

        return False

    async def get_access_level(
        self,
        user: Optional[UserInfo],
        module_id: str
    ) -> Optional[AccessLevel]:
        """
        Get the access level for a module.

        Args:
            user: User info
            module_id: Module ID

        Returns:
            AccessLevel or None if no access
        """
        if module_id in self.config.free_modules:
            return AccessLevel.FREE

        if user is None:
            return None

        category = module_id.split('.')[0] if '.' in module_id else module_id
        plan = self._get_subscription_plan(user)

        # Check subscription categories
        if category in self.config.subscription_categories:
            if plan in (SubscriptionPlan.PRO, SubscriptionPlan.TEAM, SubscriptionPlan.ENTERPRISE):
                if self._is_subscription_active(user):
                    return AccessLevel.SUBSCRIPTION

        # Check enterprise
        if module_id in self.config.enterprise_modules:
            if plan == SubscriptionPlan.ENTERPRISE and self._is_subscription_active(user):
                return AccessLevel.SUBSCRIPTION

        # Check purchased
        purchased = await self._get_purchased_modules(user.id)
        if module_id in purchased:
            return AccessLevel.PURCHASED

        # Check org shared
        if user.organization_id:
            org_modules = await self._get_org_shared_modules(user.organization_id)
            if module_id in org_modules:
                return AccessLevel.ORG_SHARED

        # Check personal
        personal = await self._get_personal_modules(user.id)
        if module_id in personal:
            return AccessLevel.PERSONAL

        return None

    def filter_modules(
        self,
        modules: List[Dict[str, Any]],
        accessible_ids: Set[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter a list of modules to only those accessible.

        Args:
            modules: List of module dicts (with moduleId or module_id key)
            accessible_ids: Set of accessible module IDs

        Returns:
            Filtered list of modules
        """
        result = []
        for module in modules:
            module_id = module.get('moduleId') or module.get('module_id') or module.get('id')
            if module_id and module_id in accessible_ids:
                result.append(module)
        return result

    def _get_subscription_plan(self, user: UserInfo) -> SubscriptionPlan:
        """Get user's subscription plan."""
        plan = user.subscription_plan
        if plan is None:
            return SubscriptionPlan.FREE

        plan_lower = plan.lower()
        if plan_lower == 'pro':
            return SubscriptionPlan.PRO
        elif plan_lower == 'team':
            return SubscriptionPlan.TEAM
        elif plan_lower == 'enterprise':
            return SubscriptionPlan.ENTERPRISE
        return SubscriptionPlan.FREE

    def _is_subscription_active(self, user: UserInfo) -> bool:
        """Check if user's subscription is active."""
        status = user.subscription_status
        if status is None:
            # Default to active if plan exists but no status
            return user.subscription_plan is not None

        return status.lower() in ('active', 'trialing')

    def _get_subscription_modules(self) -> Set[str]:
        """
        Get all modules available with subscription.

        This is a placeholder - in production, this would query
        the module registry for all modules in subscription categories.
        """
        # Return category wildcards for now
        # The actual filtering happens in check_module_access
        subscription_modules = set()

        # In production, this would be:
        # registry = get_module_registry()
        # for module_id in registry.list_all():
        #     category = module_id.split('.')[0]
        #     if category in self.config.subscription_categories:
        #         subscription_modules.add(module_id)

        return subscription_modules

    def _get_module_access_provider(self):
        """Resolve module access storage through the deployment provider hub."""
        from gateway.providers.hub import get_provider_hub

        hub = get_provider_hub()
        provider = getattr(getattr(hub, "data", None), "module_access", None)
        if provider is None:
            raise RuntimeError("module_access provider is not configured")
        return provider

    async def _get_purchased_modules(self, user_id: str) -> Set[str]:
        """
        Get modules purchased by user.

        Args:
            user_id: User ID

        Returns:
            Set of purchased module IDs
        """
        # Check cache
        if user_id in self._purchased_cache:
            return self._purchased_cache[user_id]

        # Query the active deployment provider.
        try:
            provider = self._get_module_access_provider()
            purchased = await provider.get_user_module_ids(user_id)
            self._purchased_cache[user_id] = purchased
            return purchased
        except Exception as e:
            logger.warning(f"Error fetching purchased modules: {e}")
            return set()

    async def _get_org_shared_modules(self, org_id: str) -> Set[str]:
        """
        Get modules shared within organization.

        Args:
            org_id: Organization ID

        Returns:
            Set of org-shared module IDs
        """
        # Check cache
        if org_id in self._org_shared_cache:
            return self._org_shared_cache[org_id]

        # Query the active deployment provider.
        try:
            provider = self._get_module_access_provider()
            shared = await provider.get_org_module_ids(org_id)
            self._org_shared_cache[org_id] = shared
            return shared
        except Exception as e:
            logger.warning(f"Error fetching org shared modules: {e}")
            return set()

    async def _get_personal_modules(self, user_id: str) -> Set[str]:
        """
        Get user's personal/custom modules.

        Args:
            user_id: User ID

        Returns:
            Set of personal module IDs
        """
        try:
            from gateway.providers.data.models.module_access import AccessType

            provider = self._get_module_access_provider()
            records = await provider.list_user_access(
                user_id=user_id,
                access_type=AccessType.PERSONAL
            )
            return {r.module_id for r in records}
        except Exception as e:
            logger.warning(f"Error fetching personal modules: {e}")
            return set()

    def clear_cache(self, user_id: Optional[str] = None, org_id: Optional[str] = None):
        """
        Clear access cache.

        Args:
            user_id: Clear cache for specific user
            org_id: Clear cache for specific organization
        """
        if user_id:
            self._purchased_cache.pop(user_id, None)
        if org_id:
            self._org_shared_cache.pop(org_id, None)
        if user_id is None and org_id is None:
            self._purchased_cache.clear()
            self._org_shared_cache.clear()


# Singleton instance
_service: Optional[ModuleAccessService] = None


def get_module_access_service() -> ModuleAccessService:
    """Get or create the module access service singleton."""
    global _service
    if _service is None:
        _service = ModuleAccessService()
    return _service
