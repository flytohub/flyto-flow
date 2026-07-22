"""
Capability Definitions

Enums and constants for the capabilities system.
"""

from enum import Enum
from typing import Set


class DeploymentMode(str, Enum):
    """Deployment mode enumeration"""
    CLOUD = "cloud"
    LOCAL = "local"
    OFFLINE = "offline"
    ENTERPRISE = "enterprise"
    WORKER = "worker"
    WEB = "web"


class Capability(str, Enum):
    """
    All system capabilities.

    Naming convention: category.feature
    """
    # ==========================================================================
    # Authentication Capabilities
    # ==========================================================================
    AUTH_FIREBASE = "auth.firebase"          # Firebase Authentication
    AUTH_LDAP = "auth.ldap"                  # LDAP Authentication
    AUTH_SAML = "auth.saml"                  # SAML SSO
    AUTH_OIDC = "auth.oidc"                  # OpenID Connect
    AUTH_LOCAL = "auth.local"                # Local JWT auth

    # ==========================================================================
    # User Management Capabilities
    # ==========================================================================
    USER_SELF_SIGNUP = "user.self_signup"    # Users can self-register
    USER_ADMIN_ONLY = "user.admin_only"      # Only admins create users
    USER_INVITE = "user.invite"              # Invite-based registration

    # ==========================================================================
    # Organization Capabilities (Enterprise)
    # ==========================================================================
    ORG_STRUCTURE = "org.structure"          # Organization hierarchy
    ORG_DEPARTMENTS = "org.departments"      # Department management
    ORG_TEAMS = "org.teams"                  # Team management

    # ==========================================================================
    # Access Control Capabilities
    # ==========================================================================
    ACCESS_SIMPLE = "access.simple"          # Simple role (user/admin)
    ACCESS_RBAC = "access.rbac"              # Full RBAC
    ACCESS_ABAC = "access.abac"              # Attribute-based (future)

    # ==========================================================================
    # Audit Capabilities
    # ==========================================================================
    AUDIT_BASIC = "audit.basic"              # Basic login audit
    AUDIT_FULL = "audit.full"                # Complete audit trail
    AUDIT_EVIDENCE = "audit.evidence"        # Evidence collection

    # ==========================================================================
    # Marketplace Capabilities (Cloud)
    # ==========================================================================
    MARKETPLACE = "marketplace"              # Access marketplace
    MARKETPLACE_BROWSE = "marketplace.browse"
    MARKETPLACE_PURCHASE = "marketplace.purchase"
    MARKETPLACE_PUBLISH = "marketplace.publish"

    # ==========================================================================
    # Billing Capabilities (Cloud)
    # ==========================================================================
    BILLING = "billing"                      # Billing features
    BILLING_STRIPE = "billing.stripe"        # Stripe integration
    BILLING_INVOICE = "billing.invoice"      # Invoice generation

    # ==========================================================================
    # Template Capabilities
    # ==========================================================================
    TEMPLATE_BUILDER = "template.builder"    # Template builder
    TEMPLATE_EXECUTE = "template.execute"    # Execute templates
    TEMPLATE_LOCAL = "template.local_only"   # Local-only templates

    # ==========================================================================
    # Enterprise Features
    # ==========================================================================
    ENTERPRISE_SSO = "enterprise.sso"        # Enterprise SSO
    ENTERPRISE_RUNNERS = "enterprise.runners"  # Custom runners
    ENTERPRISE_VAULT = "enterprise.vault"    # Secrets vault
    ENTERPRISE_APPROVALS = "enterprise.approvals"  # Approval workflows

    # ==========================================================================
    # Observability Capabilities (Enterprise Only - Phase 8)
    # ==========================================================================
    OBSERVABILITY_METRICS = "observability.metrics"      # Metrics collection & Prometheus export
    OBSERVABILITY_TRACING = "observability.tracing"      # Distributed tracing
    OBSERVABILITY_ALERTS = "observability.alerts"        # Alert rules & notifications

    # ==========================================================================
    # Version Control Capabilities (Enterprise Only - Phase 9)
    # ==========================================================================
    VERSIONING_WORKFLOW = "versioning.workflow"          # Workflow version control
    VERSIONING_ROLLBACK = "versioning.rollback"          # Version rollback
    VERSIONING_PROMOTE = "versioning.promote"            # Environment promotion

    # ==========================================================================
    # Advanced Audit Capabilities (Enterprise Only - Phase 9)
    # ==========================================================================
    AUDIT_IMMUTABLE = "audit.immutable"                  # Immutable audit log with hash chain
    AUDIT_ARCHIVE = "audit.archive"                      # Audit log archival & restore
    AUDIT_VERIFY = "audit.verify"                        # Chain integrity verification


# =============================================================================
# Capability Sets by Deployment Mode
# =============================================================================

CLOUD_CAPABILITIES: Set[Capability] = {
    # Auth
    Capability.AUTH_FIREBASE,

    # User
    Capability.USER_SELF_SIGNUP,

    # Access
    Capability.ACCESS_SIMPLE,

    # Audit
    Capability.AUDIT_BASIC,

    # Marketplace
    Capability.MARKETPLACE,
    Capability.MARKETPLACE_BROWSE,
    Capability.MARKETPLACE_PURCHASE,
    Capability.MARKETPLACE_PUBLISH,

    # Billing
    Capability.BILLING,
    Capability.BILLING_STRIPE,

    # Templates
    Capability.TEMPLATE_BUILDER,
    Capability.TEMPLATE_EXECUTE,
}

LOCAL_CAPABILITIES: Set[Capability] = {
    # Auth (cloud token verification via proxy)
    Capability.AUTH_FIREBASE,
    Capability.AUTH_LOCAL,

    # User
    Capability.USER_SELF_SIGNUP,

    # Access
    Capability.ACCESS_SIMPLE,

    # Templates
    Capability.TEMPLATE_BUILDER,
    Capability.TEMPLATE_EXECUTE,
    Capability.TEMPLATE_LOCAL,
}

OFFLINE_CAPABILITIES: Set[Capability] = {
    # Auth (local JWT with first-run owner setup)
    Capability.AUTH_LOCAL,

    # User
    Capability.USER_SELF_SIGNUP,

    # Access
    Capability.ACCESS_SIMPLE,

    # Templates
    Capability.TEMPLATE_BUILDER,
    Capability.TEMPLATE_EXECUTE,
    Capability.TEMPLATE_LOCAL,
}

OFFLINE_PAGES = {
    # Always accessible
    "/": True,
    "/dashboard": True,
    "/my-templates": True,
    "/templates/builder": True,
    "/templates/builder/*": True,
    "/settings": True,
    "/settings/*": True,

    # Auth pages (local JWT first-run setup and login)
    "/login": True,
    "/register": True,

    # Cloud-only pages (hidden in Offline)
    "/marketplace": False,
    "/marketplace/*": False,
    "/billing": False,
    "/billing/*": False,
    "/admin/payments": False,
    "/admin/pricing": False,

    # Enterprise pages (hidden in Offline)
    "/admin/rbac": False,
    "/admin/audit": False,
    "/admin/organization": False,
    "/admin/runners": False,
    "/admin/vault": False,
    "/admin/approvals": False,
    "/admin/metrics": False,
    "/admin/tracing": False,
    "/admin/alerts": False,
    "/admin/versions": False,
    "/admin/audit-immutable": False,
}

ENTERPRISE_CAPABILITIES: Set[Capability] = {
    # Auth
    Capability.AUTH_LDAP,
    Capability.AUTH_SAML,
    Capability.AUTH_OIDC,
    Capability.AUTH_LOCAL,

    # User
    Capability.USER_ADMIN_ONLY,
    Capability.USER_INVITE,

    # Organization
    Capability.ORG_STRUCTURE,
    Capability.ORG_DEPARTMENTS,
    Capability.ORG_TEAMS,

    # Access
    Capability.ACCESS_RBAC,

    # Audit
    Capability.AUDIT_FULL,
    Capability.AUDIT_EVIDENCE,
    Capability.AUDIT_IMMUTABLE,
    Capability.AUDIT_ARCHIVE,
    Capability.AUDIT_VERIFY,

    # Templates
    Capability.TEMPLATE_BUILDER,
    Capability.TEMPLATE_EXECUTE,
    Capability.TEMPLATE_LOCAL,

    # Enterprise
    Capability.ENTERPRISE_SSO,
    Capability.ENTERPRISE_RUNNERS,
    Capability.ENTERPRISE_VAULT,
    Capability.ENTERPRISE_APPROVALS,

    # Observability (Phase 8)
    Capability.OBSERVABILITY_METRICS,
    Capability.OBSERVABILITY_TRACING,
    Capability.OBSERVABILITY_ALERTS,

    # Versioning (Phase 9)
    Capability.VERSIONING_WORKFLOW,
    Capability.VERSIONING_ROLLBACK,
    Capability.VERSIONING_PROMOTE,
}

# =============================================================================
# Page Visibility by Deployment Mode
# =============================================================================

CLOUD_PAGES = {
    # Always accessible
    "/": True,
    "/login": True,
    "/register": True,
    "/dashboard": True,
    "/my-templates": True,
    "/templates/builder": True,
    "/templates/builder/*": True,
    "/settings": True,
    "/settings/*": True,

    # Cloud-only pages
    "/marketplace": True,
    "/marketplace/*": True,
    "/billing": True,
    "/billing/*": True,
    "/admin/payments": True,
    "/admin/pricing": True,

    # Enterprise pages (hidden in Cloud)
    "/admin/rbac": False,
    "/admin/audit": False,
    "/admin/organization": False,
    "/admin/runners": False,
    "/admin/vault": False,
    "/admin/approvals": False,

    # Phase 8 & 9 pages (Enterprise only - hidden in Cloud)
    "/admin/metrics": False,
    "/admin/tracing": False,
    "/admin/alerts": False,
    "/admin/versions": False,
    "/admin/audit-immutable": False,
}

LOCAL_PAGES = {
    # Always accessible
    "/": True,
    "/login": True,
    "/register": True,
    "/dashboard": True,
    "/my-templates": True,
    "/templates/builder": True,
    "/templates/builder/*": True,
    "/settings": True,
    "/settings/*": True,

    # Cloud-only pages (available via proxy)
    "/marketplace": True,
    "/marketplace/*": True,
    "/billing": True,
    "/billing/*": True,

    # Enterprise pages (hidden in Local)
    "/admin/payments": False,
    "/admin/pricing": False,
    "/admin/rbac": False,
    "/admin/audit": False,
    "/admin/organization": False,
    "/admin/runners": False,
    "/admin/vault": False,
    "/admin/approvals": False,
    "/admin/metrics": False,
    "/admin/tracing": False,
    "/admin/alerts": False,
    "/admin/versions": False,
    "/admin/audit-immutable": False,
}

ENTERPRISE_PAGES = {
    # Always accessible
    "/": True,
    "/login": True,
    "/dashboard": True,
    "/my-templates": True,
    "/templates/builder": True,
    "/templates/builder/*": True,
    "/settings": True,
    "/settings/*": True,

    # Cloud-only pages (hidden in Enterprise)
    "/register": False,
    "/marketplace": False,
    "/marketplace/*": False,
    "/billing": False,
    "/billing/*": False,
    "/admin/payments": False,
    "/admin/pricing": False,

    # Enterprise pages
    "/admin/rbac": True,
    "/admin/audit": True,
    "/admin/organization": True,
    "/admin/runners": True,
    "/admin/vault": True,
    "/admin/approvals": True,

    # Phase 8 & 9 pages (Enterprise only)
    "/admin/metrics": True,
    "/admin/tracing": True,
    "/admin/alerts": True,
    "/admin/versions": True,
    "/admin/audit-immutable": True,
}
