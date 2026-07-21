/**
 * Job API — Cloud execution via Firestore job queue
 *
 * Used when running workflows on cloud (not desktop).
 * Job state is in Firestore (via Cloud API), not Worker memory.
 */

import { get, post } from './client'
import { normalizeExecutionStatus } from './normalizers/executionStatus'

/**
 * Get job execution state (cloud mode polling)
 * Response is wrapped in `execution` field matching normalizeExecutionStatus format.
 *
 * @param {string} jobId
 * @returns {Promise<NormalizedExecutionStatus>}
 */
export async function getJobState(jobId) {
  try {
    const response = await get(`/devices/jobs/${jobId}/state`)
    return normalizeExecutionStatus(response)
  } catch (err) {
    return normalizeExecutionStatus({ ok: false, error: err.userMessage || err.message })
  }
}

/**
 * Cancel a cloud job
 * @param {string} jobId
 * @returns {Promise<{ok: boolean}>}
 */
export async function cancelJob(jobId) {
  try {
    return await post(`/devices/jobs/${jobId}/cancel`)
  } catch (err) {
    return { ok: false, error: err.userMessage || err.message }
  }
}
