import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key, fallback) => (typeof fallback === 'string' ? fallback : key) }),
}))

const stubs = {
  CheckCircle: true,
  XCircle: true,
  Clock: true,
  Loader2: true,
  Timer: true,
  AlertTriangle: true,
  ChevronRight: true,
  Ban: true,
}

import ExecutionHistoryList from '@/components/execution/ExecutionHistoryList.vue'

const sampleExecutions = [
  {
    id: 'exec-1',
    status: 'success',
    statusColor: '#10b981',
    formattedStartTime: '2026-01-15 10:00',
    formattedDuration: '2.5s',
    errorMessage: null,
  },
  {
    id: 'exec-2',
    status: 'failed',
    statusColor: '#ef4444',
    formattedStartTime: '2026-01-15 10:05',
    formattedDuration: '0.8s',
    errorMessage: 'Element not found',
  },
  {
    id: 'exec-3',
    status: 'running',
    statusColor: '#3b82f6',
    formattedStartTime: '2026-01-15 10:10',
    formattedDuration: '1.2s',
    errorMessage: null,
  },
  {
    id: 'exec-4',
    status: 'pending',
    statusColor: '#f59e0b',
    formattedStartTime: '2026-01-15 10:15',
    formattedDuration: '-',
    errorMessage: null,
  },
]

function factory(props = {}) {
  return shallowMount(ExecutionHistoryList, {
    props: {
      executions: sampleExecutions,
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

describe('ExecutionHistoryList.vue', () => {
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

  it('renders the correct number of execution items', () => {
    const wrapper = factory()
    const items = wrapper.findAll('.execution-item')
    expect(items.length).toBe(4)
  })

  // =========================================================================
  // Empty state
  // =========================================================================
  it('renders no items when executions is empty', () => {
    const wrapper = factory({ executions: [] })
    const items = wrapper.findAll('.execution-item')
    expect(items.length).toBe(0)
  })

  // =========================================================================
  // Execution details
  // =========================================================================
  it('displays formatted start time for each execution', () => {
    const wrapper = factory()
    const times = wrapper.findAll('.execution-time')
    expect(times[0].text()).toBe('2026-01-15 10:00')
    expect(times[1].text()).toBe('2026-01-15 10:05')
  })

  it('displays formatted duration for each execution', () => {
    const wrapper = factory()
    const durations = wrapper.findAll('.duration')
    expect(durations[0].text()).toContain('2.5s')
    expect(durations[1].text()).toContain('0.8s')
  })

  // =========================================================================
  // Status badges / icons
  // =========================================================================
  it('renders status icon container for success', () => {
    const wrapper = factory({
      executions: [sampleExecutions[0]],
    })
    const statusIcon = wrapper.find('.status-icon')
    expect(statusIcon.exists()).toBe(true)
    expect(statusIcon.attributes('style')).toContain('background-color')
  })

  it('applies correct status class for each execution', () => {
    const wrapper = factory()
    const items = wrapper.findAll('.execution-item')
    expect(items[0].classes()).toContain('status-success')
    expect(items[1].classes()).toContain('status-failed')
    expect(items[2].classes()).toContain('status-running')
    expect(items[3].classes()).toContain('status-pending')
  })

  it('renders status icon for each execution', () => {
    const wrapper = factory()
    const icons = wrapper.findAll('.status-icon')
    expect(icons.length).toBe(4)
  })

  it('renders ChevronRight action icon for each item', () => {
    const wrapper = factory()
    const actions = wrapper.findAll('.execution-actions')
    expect(actions.length).toBe(4)
  })

  // =========================================================================
  // Error display
  // =========================================================================
  it('shows error hint for executions with errors', () => {
    const wrapper = factory()
    const errorHints = wrapper.findAll('.error-hint')
    expect(errorHints.length).toBe(1) // only exec-2 has an error
    expect(errorHints[0].text()).toContain('Error')
  })

  it('does not show error hint for successful executions', () => {
    const wrapper = factory({
      executions: [sampleExecutions[0]],
    })
    expect(wrapper.find('.error-hint').exists()).toBe(false)
  })

  // =========================================================================
  // Click / selection events
  // =========================================================================
  it('emits select event when an execution item is clicked', async () => {
    const wrapper = factory()
    const items = wrapper.findAll('.execution-item')
    await items[0].trigger('click')
    expect(wrapper.emitted('select')).toBeTruthy()
    expect(wrapper.emitted('select')[0][0]).toEqual(sampleExecutions[0])
  })

  it('emits select with correct execution on second item click', async () => {
    const wrapper = factory()
    const items = wrapper.findAll('.execution-item')
    await items[1].trigger('click')
    expect(wrapper.emitted('select')[0][0]).toEqual(sampleExecutions[1])
  })

  // =========================================================================
  // Selection highlighting
  // =========================================================================
  it('highlights the selected execution', () => {
    const wrapper = factory({ selectedExecutionId: 'exec-2' })
    const items = wrapper.findAll('.execution-item')
    expect(items[1].classes()).toContain('is-selected')
  })

  it('does not highlight non-selected executions', () => {
    const wrapper = factory({ selectedExecutionId: 'exec-2' })
    const items = wrapper.findAll('.execution-item')
    expect(items[0].classes()).not.toContain('is-selected')
    expect(items[2].classes()).not.toContain('is-selected')
  })

  // =========================================================================
  // Status color
  // =========================================================================
  it('applies statusColor to the status icon background', () => {
    const wrapper = factory({
      executions: [sampleExecutions[0]],
    })
    const icon = wrapper.find('.status-icon')
    expect(icon.attributes('style')).toContain('background-color: rgb(16, 185, 129)')
  })
})
