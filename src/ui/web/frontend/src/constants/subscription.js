/**
 * Subscription Constants
 *
 * Single source of truth for all subscription-related values.
 * Must be kept in sync with backend SubscriptionPlan enum in models.py
 *
 * SECURITY NOTE: These constants are for UI display and local fallbacks ONLY.
 * Actual Pro/subscription validation is performed server-side.
 * The backend /api/capabilities endpoint returns authoritative values:
 * - is_pro: Server-computed Pro access (plan + admin check)
 * - license_type: Server-verified license type
 *
 * Always use the capabilities store values which come from the server.
 */

// Subscription Plans (matches backend SubscriptionPlan enum)
export const SUBSCRIPTION_PLANS = Object.freeze({
  FREE: 'free',
  PRO: 'pro',
  TEAM: 'team',
  OFFLINE: 'offline',        // One-time purchase offline license
  ENTERPRISE: 'enterprise'
})

// Subscription Status values
export const SUBSCRIPTION_STATUS = Object.freeze({
  ACTIVE: 'active',
  TRIALING: 'trialing',
  CANCELLED: 'cancelled',
  EXPIRED: 'expired',
  PAST_DUE: 'past_due'
})

// License Types (matches backend LicenseType enum)
// NOTE: These now match SUBSCRIPTION_PLANS for consistency
export const LICENSE_TYPES = Object.freeze({
  FREE: 'free',
  PRO: 'pro',
  TEAM: 'team',
  OFFLINE: 'offline',
  ENTERPRISE: 'enterprise'
})

// Deployment Modes (matches backend DeploymentMode enum)
export const DEPLOYMENT_MODES = Object.freeze({
  SAAS_CLOUD: 'saas_cloud',
  LOCAL_ONLINE: 'local_online',
  LOCAL_OFFLINE: 'local_offline',
  ENTERPRISE_INTRANET: 'enterprise_intranet'
})

export default {
  SUBSCRIPTION_PLANS,
  SUBSCRIPTION_STATUS,
  LICENSE_TYPES,
  DEPLOYMENT_MODES
}
