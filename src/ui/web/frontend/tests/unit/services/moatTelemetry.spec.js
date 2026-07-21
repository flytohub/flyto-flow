/**
 * moatTelemetry Unit Tests
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock the telemetry dependency
vi.mock('@/services/telemetry', () => ({
  telemetry: {
    track: vi.fn().mockResolvedValue(undefined)
  }
}))

import { telemetry } from '@/services/telemetry'
import { moatTelemetry, moatTimer } from '@/services/moatTelemetry'

describe('moatTelemetry', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  // =========================================================================
  // Checkpoint Tracking
  // =========================================================================

  describe('checkpoint tracking', () => {
    it('trackFailureShow should send correct event', () => {
      moatTelemetry.trackFailureShow('wf-1', 'node-5', 3, true)

      expect(telemetry.track).toHaveBeenCalledWith('moat.checkpoint.failure_show', {
        workflow_id: 'wf-1',
        failure_node: 'node-5',
        checkpoints_count: 3,
        has_recommended: true,
        feature: 'checkpoint'
      })
    })

    it('trackQuickResume should send correct event', () => {
      moatTelemetry.trackQuickResume('wf-1', 'cp-2', 4)

      expect(telemetry.track).toHaveBeenCalledWith('moat.checkpoint.quick_resume', {
        workflow_id: 'wf-1',
        checkpoint_id: 'cp-2',
        steps_skipped: 4,
        feature: 'checkpoint'
      })
    })

    it('trackManualCheckpointSelect should send correct event', () => {
      moatTelemetry.trackManualCheckpointSelect('wf-1', 'cp-3', false)

      expect(telemetry.track).toHaveBeenCalledWith('moat.checkpoint.manual_select', {
        workflow_id: 'wf-1',
        checkpoint_id: 'cp-3',
        was_recommended: false,
        feature: 'checkpoint'
      })
    })

    it('trackRetryFromStart should send correct event', () => {
      moatTelemetry.trackRetryFromStart('wf-1', 5)

      expect(telemetry.track).toHaveBeenCalledWith('moat.checkpoint.retry_from_start', {
        workflow_id: 'wf-1',
        checkpoints_available: 5,
        feature: 'checkpoint'
      })
    })

    it('trackCheckpointAbandon should send correct event', () => {
      moatTelemetry.trackCheckpointAbandon('wf-1', 'too complex')

      expect(telemetry.track).toHaveBeenCalledWith('moat.checkpoint.abandon', {
        workflow_id: 'wf-1',
        reason: 'too complex',
        feature: 'checkpoint'
      })
    })

    it('trackTimeSaved should send correct event', () => {
      moatTelemetry.trackTimeSaved('wf-1', 5000, 3)

      expect(telemetry.track).toHaveBeenCalledWith('moat.checkpoint.time_saved', {
        workflow_id: 'wf-1',
        time_saved_ms: 5000,
        steps_skipped: 3,
        feature: 'checkpoint'
      })
    })
  })

  // =========================================================================
  // Data Pinning Tracking
  // =========================================================================

  describe('data pinning tracking', () => {
    it('trackPinOutput should send correct event', () => {
      moatTelemetry.trackPinOutput('wf-1', 'node-3', false)

      expect(telemetry.track).toHaveBeenCalledWith('moat.pinning.pin_output', {
        workflow_id: 'wf-1',
        node_id: 'node-3',
        is_auto_pin: false,
        feature: 'pinning'
      })
    })

    it('trackUnpinOutput should send correct event', () => {
      moatTelemetry.trackUnpinOutput('wf-1', 'node-3')

      expect(telemetry.track).toHaveBeenCalledWith('moat.pinning.unpin_output', {
        workflow_id: 'wf-1',
        node_id: 'node-3',
        feature: 'pinning'
      })
    })

    it('trackAutoPinToggle should send enabled event', () => {
      moatTelemetry.trackAutoPinToggle(true)

      expect(telemetry.track).toHaveBeenCalledWith('moat.pinning.auto_enabled', {
        feature: 'pinning'
      })
    })

    it('trackAutoPinToggle should send disabled event', () => {
      moatTelemetry.trackAutoPinToggle(false)

      expect(telemetry.track).toHaveBeenCalledWith('moat.pinning.auto_disabled', {
        feature: 'pinning'
      })
    })

    it('trackPinSkipExecution should send correct event', () => {
      moatTelemetry.trackPinSkipExecution('wf-1', ['n1', 'n2'])

      expect(telemetry.track).toHaveBeenCalledWith('moat.pinning.skip_execution', {
        workflow_id: 'wf-1',
        skipped_count: 2,
        feature: 'pinning'
      })
    })

    it('trackPinSkipExecution should handle null skippedNodes', () => {
      moatTelemetry.trackPinSkipExecution('wf-1', null)

      expect(telemetry.track).toHaveBeenCalledWith('moat.pinning.skip_execution', {
        workflow_id: 'wf-1',
        skipped_count: 0,
        feature: 'pinning'
      })
    })
  })

  // =========================================================================
  // Collaboration Tracking
  // =========================================================================

  describe('collaboration tracking', () => {
    it('trackCollabJoin should send correct event', () => {
      moatTelemetry.trackCollabJoin('wf-1', 'sess-1', 3)

      expect(telemetry.track).toHaveBeenCalledWith('moat.collaboration.session_join', {
        workflow_id: 'wf-1',
        session_id: 'sess-1',
        participants_count: 3,
        feature: 'collaboration'
      })
    })

    it('trackCollabLeave should send correct event', () => {
      moatTelemetry.trackCollabLeave('wf-1', 'sess-1', 60000)

      expect(telemetry.track).toHaveBeenCalledWith('moat.collaboration.session_leave', {
        workflow_id: 'wf-1',
        session_id: 'sess-1',
        duration_ms: 60000,
        feature: 'collaboration'
      })
    })

    it('trackCollabReconnect should send correct event', () => {
      moatTelemetry.trackCollabReconnect('wf-1', 2, true)

      expect(telemetry.track).toHaveBeenCalledWith('moat.collaboration.reconnect', {
        workflow_id: 'wf-1',
        attempt: 2,
        success: true,
        feature: 'collaboration'
      })
    })

    it('trackConflictResolved should send correct event', () => {
      moatTelemetry.trackConflictResolved('wf-1', 'node_position')

      expect(telemetry.track).toHaveBeenCalledWith('moat.collaboration.conflict_resolved', {
        workflow_id: 'wf-1',
        conflict_type: 'node_position',
        feature: 'collaboration'
      })
    })
  })

  // =========================================================================
  // Friction/Success/Error Tracking
  // =========================================================================

  describe('friction and success tracking', () => {
    it('trackFriction should send correct event', () => {
      moatTelemetry.trackFriction('checkpoint', 'resume', 'no checkpoints', { workflowId: 'wf-1' })

      expect(telemetry.track).toHaveBeenCalledWith('moat.friction', {
        feature: 'checkpoint',
        action: 'resume',
        friction_reason: 'no checkpoints',
        workflowId: 'wf-1'
      })
    })

    it('trackSuccess should send correct event', () => {
      moatTelemetry.trackSuccess('pinning', 'pin', 200, { nodeId: 'n1' })

      expect(telemetry.track).toHaveBeenCalledWith('moat.success', {
        feature: 'pinning',
        action: 'pin',
        duration_ms: 200,
        nodeId: 'n1'
      })
    })

    it('trackSuccess should handle null duration', () => {
      moatTelemetry.trackSuccess('pinning', 'pin')

      expect(telemetry.track).toHaveBeenCalledWith('moat.success', {
        feature: 'pinning',
        action: 'pin',
        duration_ms: null
      })
    })

    it('trackError should send correct event', () => {
      moatTelemetry.trackError('collaboration', 'join', 'WebSocket failed', { sessionId: 's1' })

      expect(telemetry.track).toHaveBeenCalledWith('moat.error', {
        feature: 'collaboration',
        action: 'join',
        error_message: 'WebSocket failed',
        sessionId: 's1'
      })
    })
  })
})

// =============================================================================
// moatTimer
// =============================================================================

describe('moatTimer', () => {
  beforeEach(() => {
    vi.spyOn(Date, 'now')
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('should start and end a timer returning duration', () => {
    Date.now.mockReturnValueOnce(1000).mockReturnValueOnce(1500)

    moatTimer.start('test-op')
    const duration = moatTimer.end('test-op')

    expect(duration).toBe(500)
  })

  it('should return null for unknown timer key', () => {
    expect(moatTimer.end('nonexistent')).toBeNull()
  })

  it('should clear a timer', () => {
    moatTimer.start('to-clear')
    moatTimer.clear('to-clear')
    expect(moatTimer.end('to-clear')).toBeNull()
  })

  it('should handle multiple timers independently', () => {
    Date.now
      .mockReturnValueOnce(1000) // start A
      .mockReturnValueOnce(1100) // start B
      .mockReturnValueOnce(1300) // end A
      .mockReturnValueOnce(1500) // end B

    moatTimer.start('a')
    moatTimer.start('b')
    const durationA = moatTimer.end('a')
    const durationB = moatTimer.end('b')

    expect(durationA).toBe(300)
    expect(durationB).toBe(400)
  })

  it('should remove timer after end', () => {
    Date.now.mockReturnValue(1000)
    moatTimer.start('once')
    moatTimer.end('once')
    expect(moatTimer.end('once')).toBeNull()
  })
})
