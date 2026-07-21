/**
 * Circuit Breaker / Error Handling / Retry Logic
 *
 * Prevents telemetry failures from causing error loops.
 * After FAILURE_LIMIT consecutive failures, telemetry is disabled
 * for DISABLE_DURATION_MS milliseconds.
 */

const FAILURE_LIMIT = 3
const DISABLE_DURATION_MS = 60000

let failureCount = 0
let disabledUntil = 0

/**
 * Check if telemetry is currently disabled by the circuit breaker
 * @returns {boolean} True if disabled
 */
export function isCircuitOpen() {
  return disabledUntil > 0 && Date.now() < disabledUntil
}

/**
 * Record a successful send - resets the failure counter
 */
export function recordSuccess() {
  failureCount = 0
  disabledUntil = 0
}

/**
 * Record a failed send - may trip the circuit breaker
 */
export function recordFailure() {
  failureCount += 1
  if (failureCount >= FAILURE_LIMIT) {
    disabledUntil = Date.now() + DISABLE_DURATION_MS
  }
}
