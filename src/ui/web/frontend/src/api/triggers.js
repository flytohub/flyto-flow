import { get, post } from '@/api/client'

export function validateCron(expression) {
  return post('/triggers/cron/validate', { expression })
}

export function getNextCronRuns(expression, timezone = 'UTC', count = 3) {
  return get('/triggers/cron/next', { params: { expression, timezone, count } })
}

export const triggersAPI = { validateCron, getNextCronRuns }
