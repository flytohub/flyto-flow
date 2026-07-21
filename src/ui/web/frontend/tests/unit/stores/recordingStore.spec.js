import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('@/api/client', () => ({
  post: vi.fn()
}))

import { post } from '@/api/client'
import { useRecordingStore } from '@/stores/recordingStore'

describe('useRecordingStore', () => {
  let store

  beforeEach(() => {
    setActivePinia(createPinia())
    store = useRecordingStore()
    vi.clearAllMocks()
  })

  it('starts a recording session and resets stale compile metadata', async () => {
    store.compiledSteps = [{ id: 'old' }]
    store.workflowResult = { steps: [{ id: 'old' }] }
    store.recordingSummary = { skippedActionCount: 1 }
    store.compileWarnings = [{ code: 'old_warning' }]
    post.mockResolvedValue({ ok: true, sessionId: 'rec_123' })

    await store.startRecording('https://example.com')

    expect(post).toHaveBeenCalledWith('/recording/start', { url: 'https://example.com' })
    expect(store.sessionId).toBe('rec_123')
    expect(store.isRecording).toBe(true)
    expect(store.compiledSteps).toBeNull()
    expect(store.workflowResult).toBeNull()
    expect(store.recordingSummary).toBeNull()
    expect(store.compileWarnings).toEqual([])
  })

  it('stops a recording and keeps compile summary and warnings', async () => {
    store.sessionId = 'rec_123'
    store.isRecording = true
    const steps = [
      { id: 'launch', module: 'browser.launch', params: {} },
      { id: 'close', module: 'browser.close', params: {} }
    ]
    const recordingSummary = {
      recordedActionCount: 2,
      replayableActionCount: 1,
      skippedActionCount: 1,
      stepCount: 3
    }
    const warnings = [
      {
        code: 'non_replayable_navigation',
        actionIndex: 0,
        actionType: 'navigate',
        message: 'Recorded navigation was skipped because only http and https URLs are replayable.'
      }
    ]
    post.mockResolvedValue({ ok: true, steps, recordingSummary, warnings })

    await store.stopRecording()

    expect(post).toHaveBeenCalledWith('/recording/stop', { session_id: 'rec_123' })
    expect(store.workflowResult).toEqual({ ok: true, steps, recordingSummary, warnings })
    expect(store.compiledSteps).toEqual(steps)
    expect(store.recordingSummary).toEqual(recordingSummary)
    expect(store.compileWarnings).toEqual(warnings)
    expect(store.hasCompileWarnings).toBe(true)
    expect(store.isRecording).toBe(false)
    expect(store.sessionId).toBeNull()
  })

  it('accepts snake_case compile summary responses', async () => {
    store.sessionId = 'rec_456'
    post.mockResolvedValue({
      ok: true,
      steps: [],
      recording_summary: { skipped_action_count: 0 },
      warnings: []
    })

    await store.stopRecording()

    expect(store.recordingSummary).toEqual({ skipped_action_count: 0 })
    expect(store.hasCompileWarnings).toBe(false)
  })

  it('does not expose compiled steps when stop returns a non-ok response', async () => {
    store.sessionId = 'rec_bad'
    store.isRecording = true
    const warnings = [{ code: 'compile_failed', message: 'compile failed' }]
    post.mockResolvedValue({
      ok: false,
      error: 'compile failed',
      steps: [{ id: 'unsafe' }],
      warnings,
      recordingSummary: { skippedActionCount: 1 }
    })

    await store.stopRecording()

    expect(store.error).toBe('compile failed')
    expect(store.compiledSteps).toBeNull()
    expect(store.compileWarnings).toEqual(warnings)
    expect(store.workflowResult.ok).toBe(false)
    expect(store.isRecording).toBe(false)
    expect(store.sessionId).toBeNull()
  })

  it('keeps stable empty compile state when stop returns malformed data', async () => {
    store.sessionId = 'rec_malformed'
    store.isRecording = true
    post.mockResolvedValue({
      ok: true,
      steps: [null, 'bad'],
      warnings: [{ code: 'empty' }],
      recordingSummary: 'bad'
    })

    await store.stopRecording()

    expect(store.compiledSteps).toBeNull()
    expect(store.recordingSummary).toBeNull()
    expect(store.compileWarnings).toEqual([])
    expect(store.workflowResult).toEqual({
      ok: true,
      steps: [null, 'bad'],
      warnings: [{ code: 'empty' }],
      recordingSummary: 'bad'
    })
    expect(store.isRecording).toBe(false)
  })

  it('fails start safely when the backend does not return a session id', async () => {
    post.mockResolvedValue({ ok: true })

    await expect(store.startRecording('https://example.com')).rejects.toThrow('Recording session was not created')

    expect(store.isRecording).toBe(false)
    expect(store.sessionId).toBeNull()
    expect(store.compiledSteps).toBeNull()
    expect(store.compileWarnings).toEqual([])
  })

  it('clears compile metadata on reset', () => {
    store.isRecording = true
    store.sessionId = 'rec_123'
    store.compiledSteps = [{ id: 'launch' }]
    store.workflowResult = { steps: [{ id: 'launch' }] }
    store.recordingSummary = { skippedActionCount: 1 }
    store.compileWarnings = [{ code: 'non_replayable_navigation' }]

    store.reset()

    expect(store.isRecording).toBe(false)
    expect(store.sessionId).toBeNull()
    expect(store.compiledSteps).toBeNull()
    expect(store.workflowResult).toBeNull()
    expect(store.recordingSummary).toBeNull()
    expect(store.compileWarnings).toEqual([])
    expect(store.hasCompileWarnings).toBe(false)
  })
})
