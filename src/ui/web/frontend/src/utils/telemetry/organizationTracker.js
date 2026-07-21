/**
 * Organization Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks organization events only.
 */

import { telemetry } from '@/services/telemetry'
import { ORGANIZATION_EVENTS } from '@/constants/telemetryEvents'

export const trackOrganization = {
  update: (orgId) => {
    telemetry.track(ORGANIZATION_EVENTS.UPDATE, { org_id: orgId })
  },

  memberInvite: (orgId, role) => {
    telemetry.track(ORGANIZATION_EVENTS.MEMBER_INVITE, { org_id: orgId, role })
  },

  memberRemove: (orgId) => {
    telemetry.track(ORGANIZATION_EVENTS.MEMBER_REMOVE, { org_id: orgId })
  },

  memberRoleUpdate: (orgId, newRole) => {
    telemetry.track(ORGANIZATION_EVENTS.MEMBER_ROLE_UPDATE, { org_id: orgId, new_role: newRole })
  },
}
