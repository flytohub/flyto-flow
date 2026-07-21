/**
 * Trial Mode Telemetry Tracker
 *
 * S-Grade: Single responsibility - tracks trial mode events only.
 */

import { telemetry } from '@/services/telemetry'
import { TRIAL_EVENTS } from '@/constants/telemetryEvents'

export const trackTrial = {
  start: (workflowId, itemsCount, batchSize, inputMethod = 'manual') => {
    telemetry.track(TRIAL_EVENTS.START, {
      workflow_id: workflowId,
      items_count: itemsCount,
      batch_size: batchSize,
      input_method: inputMethod,
    })
  },

  continue: (trialId, batchSize, processedCount, remainingCount) => {
    telemetry.track(TRIAL_EVENTS.CONTINUE, {
      trial_id: trialId,
      batch_size: batchSize,
      processed_count: processedCount,
      remaining_count: remainingCount,
    })
  },

  abort: (trialId, processedCount, reason = 'user_request') => {
    telemetry.track(TRIAL_EVENTS.ABORT, {
      trial_id: trialId,
      processed_count: processedCount,
      reason,
    })
  },

  complete: (trialId, totalItems, successCount, failCount, durationMs) => {
    telemetry.track(TRIAL_EVENTS.COMPLETE, {
      trial_id: trialId,
      total_items: totalItems,
      success_count: successCount,
      fail_count: failCount,
      duration_ms: durationMs,
    })
  },

  batchStart: (trialId, batchNumber, batchSize) => {
    telemetry.track(TRIAL_EVENTS.BATCH_START, {
      trial_id: trialId,
      batch_number: batchNumber,
      batch_size: batchSize,
    })
  },

  batchComplete: (trialId, batchNumber, successCount, failCount) => {
    telemetry.track(TRIAL_EVENTS.BATCH_COMPLETE, {
      trial_id: trialId,
      batch_number: batchNumber,
      success_count: successCount,
      fail_count: failCount,
    })
  },

  batchError: (trialId, batchNumber, error) => {
    telemetry.track(TRIAL_EVENTS.BATCH_ERROR, {
      trial_id: trialId,
      batch_number: batchNumber,
      error: typeof error === 'string' ? error : error?.message,
    })
  },

  waitingApproval: (trialId, processedCount, remainingCount) => {
    telemetry.track(TRIAL_EVENTS.WAITING_APPROVAL, {
      trial_id: trialId,
      processed_count: processedCount,
      remaining_count: remainingCount,
    })
  },

  csvUpload: (fileName, rowCount, columnCount) => {
    telemetry.track(TRIAL_EVENTS.CSV_UPLOAD, {
      file_name: fileName,
      row_count: rowCount,
      column_count: columnCount,
    })
  },

  manualInput: (itemsCount) => {
    telemetry.track(TRIAL_EVENTS.MANUAL_INPUT, { items_count: itemsCount })
  },
}
