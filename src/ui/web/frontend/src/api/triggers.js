import { get, post, patch, del } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

// ── Schedules ──────────────────────────────────────────────

/** List all schedules with optional query params */
export async function listSchedules(params = {}) {
  return await get(ENDPOINTS.TRIGGERS.SCHEDULES, { params })
}

/** Create a new schedule trigger */
export async function createSchedule(data) {
  return await post(ENDPOINTS.TRIGGERS.SCHEDULES, data)
}

/** Delete a schedule by ID */
export async function deleteSchedule(id) {
  return await del(ENDPOINTS.TRIGGERS.SCHEDULE(id))
}

/** Pause an active schedule */
export async function pauseSchedule(id) {
  return await post(ENDPOINTS.TRIGGERS.SCHEDULE_PAUSE(id))
}

/** Resume a paused schedule */
export async function resumeSchedule(id) {
  return await post(ENDPOINTS.TRIGGERS.SCHEDULE_RESUME(id))
}

/** Manually trigger a schedule to run immediately */
export async function triggerSchedule(id) {
  return await post(ENDPOINTS.TRIGGERS.SCHEDULE_TRIGGER(id))
}

// ── Webhooks ───────────────────────────────────────────────

/** List all webhooks with optional query params */
export async function listWebhooks(params = {}) {
  return await get(ENDPOINTS.TRIGGERS.WEBHOOKS, { params })
}

/** Create a new webhook trigger */
export async function createWebhook(data) {
  return await post(ENDPOINTS.TRIGGERS.WEBHOOKS, data)
}

/** Delete a webhook by ID */
export async function deleteWebhook(id) {
  return await del(ENDPOINTS.TRIGGERS.WEBHOOK(id))
}

/** Disable an active webhook */
export async function disableWebhook(id) {
  return await post(ENDPOINTS.TRIGGERS.WEBHOOK_DISABLE(id))
}

/** Enable a disabled webhook */
export async function enableWebhook(id) {
  return await post(ENDPOINTS.TRIGGERS.WEBHOOK_ENABLE(id))
}

// ── Webhook Test ──────────────────────────────────────────

/** Start a webhook test session */
export async function startWebhookTest(id) {
  return await post(ENDPOINTS.TRIGGERS.WEBHOOK_TEST_START(id))
}

/** Get the result of a webhook test */
export async function getWebhookTestResult(id) {
  return await get(ENDPOINTS.TRIGGERS.WEBHOOK_TEST_RESULT(id))
}

// ── Utilities ──────────────────────────────────────────────

/** Validate a cron expression */
export async function validateCron(expression) {
  return await post(ENDPOINTS.TRIGGERS.CRON_VALIDATE, { expression })
}

export const triggersAPI = {
  listSchedules,
  createSchedule,
  deleteSchedule,
  pauseSchedule,
  resumeSchedule,
  triggerSchedule,
  listWebhooks,
  createWebhook,
  deleteWebhook,
  disableWebhook,
  enableWebhook,
  startWebhookTest,
  getWebhookTestResult,
  validateCron,
}
