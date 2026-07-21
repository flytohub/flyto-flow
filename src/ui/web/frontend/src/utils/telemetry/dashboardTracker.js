/**
 * Dashboard Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks dashboard events only.
 */

import { telemetry } from '@/services/telemetry'
import { DASHBOARD_EVENTS } from '@/constants/telemetryEvents'

export const trackDashboard = {
  load: (stats = {}) => {
    telemetry.track(DASHBOARD_EVENTS.LOAD, stats)
  },

  dateRangeChange: (startDate, endDate) => {
    telemetry.track(DASHBOARD_EVENTS.DATE_RANGE_CHANGE, {
      start_date: startDate,
      end_date: endDate,
    })
  },

  exportReport: (reportType, format) => {
    telemetry.track(DASHBOARD_EVENTS.EXPORT_REPORT, { report_type: reportType, format })
  },
}
