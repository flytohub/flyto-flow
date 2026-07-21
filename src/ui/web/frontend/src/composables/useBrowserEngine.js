import { ref, computed, onMounted, onUnmounted } from 'vue'
import { get, post } from '@/api/client'

/**
 * useBrowserEngine
 *
 * Surfaces the browser-engine (Playwright chromium + node) first-run
 * provisioning state so the UI can show download progress and offer a retry
 * instead of silently failing to crawl.
 *
 * Source of truth: GET /api/health → { browserEngine: { ready, state,
 *   node: { state, reason, progress }, chromium: { state, reason, progress } } }
 * (the api client camelCases snake_case response keys, so browser_engine →
 *  browserEngine).
 *
 * Polling cadence:
 *   - provisioning / pending / unknown → fast poll (~2s) so progress feels live
 *   - degraded                          → fast poll (so a recovery flips us back)
 *   - ready                             → slow poll (~30s) as a cheap liveness check
 *
 * Resilience: a failed /api/health request (e.g. sidecar still booting) is
 * swallowed and treated as "pending" — we keep polling, never throw.
 */

const FAST_INTERVAL_MS = 2000
const SLOW_INTERVAL_MS = 30000

export function useBrowserEngine() {
  // Reactive engine state. Start "pending" (unknown) until the first poll lands.
  const state = ref('pending')
  const node = ref(null)
  const chromium = ref(null)
  const error = ref(null) // degraded reason (string) or null
  const retrying = ref(false)

  let timer = null
  let stopped = false

  const ready = computed(() => state.value === 'ready')

  // Overall percent: average of whatever component progresses are known.
  // null when nothing reports progress yet (so the bar can render
  // indeterminate instead of a misleading 0%).
  const percent = computed(() => {
    const vals = [node.value?.progress, chromium.value?.progress]
      .filter((p) => typeof p === 'number' && !Number.isNaN(p))
    if (vals.length === 0) return null
    const avg = vals.reduce((a, b) => a + b, 0) / vals.length
    return Math.max(0, Math.min(100, Math.round(avg)))
  })

  function intervalForState(s) {
    return s === 'ready' ? SLOW_INTERVAL_MS : FAST_INTERVAL_MS
  }

  function applyEngine(engine) {
    if (!engine || typeof engine !== 'object') {
      // No browser_engine block in the payload — backend may be too old or
      // the sidecar isn't reporting yet. Treat as unknown, keep polling.
      state.value = 'pending'
      error.value = null
      return
    }
    state.value = engine.state || (engine.ready ? 'ready' : 'pending')
    node.value = engine.node || null
    chromium.value = engine.chromium || null
    error.value =
      state.value === 'degraded'
        ? engine.node?.reason || engine.chromium?.reason || 'Browser engine provisioning failed'
        : null
  }

  async function poll() {
    try {
      const data = await get('/health')
      applyEngine(data?.browserEngine)
    } catch {
      // Sidecar starting / network blip — stay in (or fall back to) unknown.
      // Do NOT clobber a previously-known good state into pending on a
      // transient error; only downgrade if we never had a real state.
      if (state.value === 'ready') {
        // keep ready; a single failed liveness check shouldn't alarm the user
      } else if (state.value !== 'degraded') {
        state.value = 'pending'
      }
    } finally {
      schedule()
    }
  }

  function schedule() {
    if (stopped) return
    clearTimer()
    timer = setTimeout(poll, intervalForState(state.value))
  }

  function clearTimer() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  async function retry() {
    if (retrying.value) return
    retrying.value = true
    try {
      const data = await post('/browser-engine/provision', {})
      if (data?.browserEngine) {
        applyEngine(data.browserEngine)
      } else {
        // Provision accepted but no snapshot returned — force a fast re-poll.
        state.value = 'provisioning'
      }
    } catch {
      // Re-trigger failed (sidecar unreachable). Leave state as-is; the next
      // poll will reflect reality. Surface a generic reason if we have none.
      if (!error.value) error.value = 'Retry failed — will keep trying'
    } finally {
      retrying.value = false
      // Resume fast polling immediately so progress / recovery shows up.
      schedule()
    }
  }

  onMounted(() => {
    stopped = false
    poll() // immediate first read; schedules the next tick itself
  })

  onUnmounted(() => {
    stopped = true
    clearTimer()
  })

  return {
    state,
    ready,
    node,
    chromium,
    error,
    percent,
    retrying,
    retry,
  }
}
