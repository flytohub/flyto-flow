/**
 * Handle ID Constants
 *
 * S-Grade: Handle/port ID constants for nodes.
 * Single responsibility: Handle identification.
 */

/**
 * Standard handle IDs used across nodes
 */
export const HANDLE_IDS = {
  // Input handles
  INPUT: 'target-input',
  IN: 'in',                         // Standard input (new unified naming)
  TARGET_TOP: 'target-top',         // Top input (loop body entry from body_out)

  // Output handles
  MAIN: 'output',
  SUCCESS: 'source-success',
  ERROR: 'source-error',

  // Branch outputs
  TRUE: 'source-true',
  FALSE: 'source-false',

  // Loop outputs
  BODY_OUT: 'body_out',             // Loop body output (bottom sub-port, blue)
  DONE_OUT: 'done_out',             // Loop done output (right, green)
  ITEM: 'source-item',              // Legacy - kept for backward compat
  DONE: 'source-done',              // Legacy - kept for backward compat

  // Switch outputs
  DEFAULT: 'source-default',
  CASE_PREFIX: 'source-case-',

  // Special
  MERGED: 'source-merged',
  JOINED: 'source-joined',
  TRIGGERED: 'source-triggered',
  START: 'source-start'
}
