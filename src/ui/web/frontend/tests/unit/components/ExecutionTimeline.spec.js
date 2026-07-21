import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key, fallback) => (typeof fallback === 'string' ? fallback : key) }),
}))

// Mock format utility
vi.mock('@/utils/format', () => ({
  formatDuration: (ms) => {
    if (!ms && ms !== 0) return '0ms'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  },
}))

const stubs = {
  Clock: true,
  Activity: true,
  StatusDot: { template: '<span class="status-dot"></span>', props: ['status'] },
}

import ExecutionTimeline from '@/components/execution/ExecutionTimeline.vue'

function factory(props = {}) {
  return shallowMount(ExecutionTimeline, {
    props: {
      nodes: [],
      ...props,
    },
    global: {
      plugins: [createPinia()],
      stubs,
      mocks: {
        $t: (key, fallback) => (typeof fallback === 'string' ? fallback : key),
      },
    },
  })
}

const now = new Date('2026-01-15T10:00:00Z')
const sampleNodes = [
  {
    id: 'node-1',
    label: 'Open Browser',
    status: 'success',
    startedAt: new Date(now.getTime()).toISOString(),
    durationMs: 2000,
  },
  {
    id: 'node-2',
    label: 'Click Button',
    status: 'failed',
    startedAt: new Date(now.getTime() + 2000).toISOString(),
    durationMs: 500,
  },
  {
    id: 'node-3',
    label: 'Extract Data',
    status: 'running',
    startedAt: new Date(now.getTime() + 2500).toISOString(),
    durationMs: 1500,
  },
]

describe('ExecutionTimeline.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // =========================================================================
  // Basic rendering
  // =========================================================================
  it('renders without errors', () => {
    const wrapper = factory()
    expect(wrapper.exists()).toBe(true)
  })

  it('renders the timeline header', () => {
    const wrapper = factory()
    expect(wrapper.find('.timeline-header').exists()).toBe(true)
  })

  it('displays the title text', () => {
    const wrapper = factory()
    expect(wrapper.find('.title').exists()).toBe(true)
  })

  // =========================================================================
  // Empty state
  // =========================================================================
  it('shows empty state when nodes array is empty', () => {
    const wrapper = factory({ nodes: [] })
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.html()).toContain('No execution data')
  })

  it('does not show timeline rows when empty', () => {
    const wrapper = factory({ nodes: [] })
    expect(wrapper.find('.timeline-rows').exists()).toBe(false)
  })

  // =========================================================================
  // Timeline bars
  // =========================================================================
  it('renders timeline rows for each node', () => {
    const wrapper = factory({ nodes: sampleNodes })
    const rows = wrapper.findAll('.timeline-row')
    expect(rows.length).toBe(3)
  })

  it('displays node labels', () => {
    const wrapper = factory({ nodes: sampleNodes })
    const labels = wrapper.findAll('.node-label')
    expect(labels[0].text()).toBe('Open Browser')
    expect(labels[1].text()).toBe('Click Button')
    expect(labels[2].text()).toBe('Extract Data')
  })

  it('renders StatusDot for each node', () => {
    const wrapper = factory({ nodes: sampleNodes })
    const dots = wrapper.findAll('.status-dot')
    expect(dots.length).toBe(3)
  })

  // =========================================================================
  // Status color mapping
  // =========================================================================
  it('applies bar-success class for completed status', () => {
    const wrapper = factory({
      nodes: [{ id: '1', label: 'Test', status: 'success', startedAt: now.toISOString(), durationMs: 100 }],
    })
    expect(wrapper.find('.bar-success').exists()).toBe(true)
  })

  it('applies bar-error class for failed status', () => {
    const wrapper = factory({
      nodes: [{ id: '1', label: 'Test', status: 'failed', startedAt: now.toISOString(), durationMs: 100 }],
    })
    expect(wrapper.find('.bar-error').exists()).toBe(true)
  })

  it('applies bar-running class for running status', () => {
    const wrapper = factory({
      nodes: [{ id: '1', label: 'Test', status: 'running', startedAt: now.toISOString(), durationMs: 100 }],
    })
    expect(wrapper.find('.bar-running').exists()).toBe(true)
  })

  it('applies bar-pending class for pending status', () => {
    const wrapper = factory({
      nodes: [{ id: '1', label: 'Test', status: 'pending', startedAt: now.toISOString(), durationMs: 100 }],
    })
    expect(wrapper.find('.bar-pending').exists()).toBe(true)
  })

  it('applies bar-default class for unknown status', () => {
    const wrapper = factory({
      nodes: [{ id: '1', label: 'Test', status: 'cancelled', startedAt: now.toISOString(), durationMs: 100 }],
    })
    expect(wrapper.find('.bar-default').exists()).toBe(true)
  })

  // =========================================================================
  // Duration formatting
  // =========================================================================
  it('displays formatted duration for each node', () => {
    const wrapper = factory({
      nodes: [{ id: '1', label: 'Test', status: 'success', startedAt: now.toISOString(), durationMs: 2000 }],
    })
    const duration = wrapper.find('.duration')
    expect(duration.text()).toBe('2.0s')
  })

  it('shows total duration in the header', () => {
    const wrapper = factory({ nodes: sampleNodes })
    const totalDuration = wrapper.find('.total-duration')
    expect(totalDuration.exists()).toBe(true)
    // Total should be max end - min start = (2500+1500) - 0 = 4000ms = 4.0s
    expect(totalDuration.text()).toBe('4.0s')
  })

  // =========================================================================
  // Selection / Events
  // =========================================================================
  it('emits select event when a row is clicked', async () => {
    const wrapper = factory({ nodes: sampleNodes })
    const row = wrapper.findAll('.timeline-row')[0]
    await row.trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')[0][0]).toBe('node-1')
  })

  it('highlights the selected node row', () => {
    const wrapper = factory({ nodes: sampleNodes, selectedNodeId: 'node-2' })
    const rows = wrapper.findAll('.timeline-row')
    expect(rows[1].classes()).toContain('selected')
  })

  // =========================================================================
  // Sorting
  // =========================================================================
  it('sorts nodes by start time', () => {
    const reversed = [...sampleNodes].reverse()
    const wrapper = factory({ nodes: reversed })
    const labels = wrapper.findAll('.node-label')
    expect(labels[0].text()).toBe('Open Browser')
    expect(labels[1].text()).toBe('Click Button')
    expect(labels[2].text()).toBe('Extract Data')
  })
})
