/**
 * Time constants in milliseconds
 * Use these instead of magic numbers in the codebase
 */

export const MS_PER_SECOND = 1000
export const MS_PER_MINUTE = 60 * MS_PER_SECOND
export const MS_PER_HOUR = 60 * MS_PER_MINUTE
export const MS_PER_DAY = 24 * MS_PER_HOUR
export const MS_PER_WEEK = 7 * MS_PER_DAY

// Common durations
export const DURATION = {
  ONE_SECOND: MS_PER_SECOND,
  ONE_MINUTE: MS_PER_MINUTE,
  FIVE_MINUTES: 5 * MS_PER_MINUTE,
  TEN_MINUTES: 10 * MS_PER_MINUTE,
  THIRTY_MINUTES: 30 * MS_PER_MINUTE,
  ONE_HOUR: MS_PER_HOUR,
  ONE_DAY: MS_PER_DAY,
  ONE_WEEK: MS_PER_WEEK,
  THIRTY_DAYS: 30 * MS_PER_DAY
}

export default {
  MS_PER_SECOND,
  MS_PER_MINUTE,
  MS_PER_HOUR,
  MS_PER_DAY,
  MS_PER_WEEK,
  DURATION
}
