/**
 * Telemetry Service - Module Index
 *
 * Re-exports all telemetry functionality so that existing imports
 * like `import { telemetry } from '@/services/telemetry'` continue to work.
 */

export {
  telemetry,
  telemetry as default,
  initTelemetryErrorHandlers,
  addTelemetryHeaders,
  trackRequestDuration,
  trackApiErrorInterceptor,
  startHeartbeat,
  stopHeartbeat
} from './tracker'

export { getDeviceInfo, getPerformanceMetrics } from './device'

export { isCircuitOpen, recordSuccess, recordFailure } from './circuitBreaker'
