/**
 * Telemetry Service
 *
 * This file re-exports from the telemetry/ directory so that both
 * `import { telemetry } from '@/services/telemetry'` (resolves to file)
 * and `import { telemetry } from '@/services/telemetry/index'` (resolves to dir)
 * continue to work.
 */

export {
  telemetry,
  telemetry as default,
  initTelemetryErrorHandlers,
  addTelemetryHeaders,
  trackRequestDuration,
  trackApiErrorInterceptor,
  startHeartbeat,
  stopHeartbeat,
  getDeviceInfo,
  getPerformanceMetrics,
  isCircuitOpen,
  recordSuccess,
  recordFailure
} from './telemetry/index'
