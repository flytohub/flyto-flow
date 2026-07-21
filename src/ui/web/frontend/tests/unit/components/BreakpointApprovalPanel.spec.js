import { describe, it, expect, vi, beforeEach } from 'vitest'
import { shallowMount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'

// Mock vue-i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key, fallback) => (typeof fallback === 'string' ? fallback : key) }),
}))

const stubs = {
  Hand: true,
  X: true,
  Loader: true,
  CheckCircle: true,
  XCircle: true,
  ChevronDown: true,
  Database: true,
  Edit3: true,
  AppTextarea: {
    template: '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)"></textarea>',
    props: ['modelValue', 'placeholder', 'rows'],
    emits: ['update:modelValue'],
  },
}

import BreakpointApprovalPanel from '@/components/execution/BreakpointApprovalPanel.vue'

const futureDate = new Date(Date.now() + 60 * 60 * 1000).toISOString() // 1 hour from now
const soonDate = new Date(Date.now() + 2 * 60 * 1000).toISOString() // 2 min from now
const pastDate = new Date(Date.now() - 60 * 1000).toISOString() // 1 min ago

const sampleBreakpoint = {
  breakpointId: 'bp-123',
  title: 'Approval Needed',
  description: 'Please review this step before continuing.',
  workflowId: 'wf-456',
  stepId: 'step-3',
  createdAt: new Date('2026-01-15T10:00:00Z').toISOString(),
  expiresAt: futureDate,
  contextSnapshot: { url: 'https://example.com', count: 42 },
  customFields: [],
}

function factory(props = {}) {
  return shallowMount(BreakpointApprovalPanel, {
    props: {
      isOpen: true,
      breakpoint: sampleBreakpoint,
      loading: false,
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

describe('BreakpointApprovalPanel.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // =========================================================================
  // Visibility
  // =========================================================================
  it('renders when isOpen is true', () => {
    const wrapper = factory({ isOpen: true })
    expect(wrapper.find('.fixed').exists()).toBe(true)
  })

  it('does not render when isOpen is false', () => {
    const wrapper = factory({ isOpen: false })
    expect(wrapper.find('.fixed').exists()).toBe(false)
  })

  // =========================================================================
  // Breakpoint details
  // =========================================================================
  it('displays breakpoint title', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('Approval Needed')
  })

  it('displays breakpoint description', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('Please review this step before continuing.')
  })

  it('displays workflow and step info', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('wf-456')
    expect(wrapper.html()).toContain('step-3')
  })

  it('shows loading spinner when loading is true', () => {
    const wrapper = factory({ loading: true })
    // The loading div contains the spinner and has animate-spin class
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
  })

  it('shows empty state when breakpoint is null', () => {
    const wrapper = factory({ breakpoint: null })
    expect(wrapper.html()).toContain('breakpoint.noBreakpoint')
  })

  // =========================================================================
  // Approve / Reject buttons
  // =========================================================================
  it('renders approve and reject buttons', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('breakpoint.approve')
    expect(wrapper.html()).toContain('breakpoint.reject')
  })

  it('emits approve event when approve button is clicked', async () => {
    const wrapper = factory()
    const approveBtn = wrapper.find('button[class*="bg-green-600"]')
    await approveBtn.trigger('click')
    expect(wrapper.emitted('approve')).toBeTruthy()
    expect(wrapper.emitted('approve')[0][0]).toMatchObject({
      breakpointId: 'bp-123',
    })
  })

  it('emits reject event when reject button is clicked', async () => {
    const wrapper = factory()
    const rejectBtn = wrapper.find('button[class*="bg-red-600"]')
    await rejectBtn.trigger('click')
    expect(wrapper.emitted('reject')).toBeTruthy()
    expect(wrapper.emitted('reject')[0][0]).toMatchObject({
      breakpointId: 'bp-123',
    })
  })

  it('emits close when backdrop is clicked', async () => {
    const wrapper = factory()
    const backdrop = wrapper.find('.fixed')
    await backdrop.trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  // =========================================================================
  // Custom fields
  // =========================================================================
  it('renders custom input fields', () => {
    const breakpoint = {
      ...sampleBreakpoint,
      customFields: [
        { name: 'reason', label: 'Reason', type: 'string', required: true },
        { name: 'amount', label: 'Amount', type: 'number', required: false },
      ],
    }
    const wrapper = factory({ breakpoint })
    expect(wrapper.html()).toContain('Reason')
    expect(wrapper.html()).toContain('Amount')
  })

  it('shows required indicator for required fields', () => {
    const breakpoint = {
      ...sampleBreakpoint,
      customFields: [
        { name: 'reason', label: 'Reason', type: 'string', required: true },
      ],
    }
    const wrapper = factory({ breakpoint })
    expect(wrapper.find('.text-red-400').exists()).toBe(true)
  })

  it('disables approve when required custom field is empty', () => {
    const breakpoint = {
      ...sampleBreakpoint,
      customFields: [
        { name: 'reason', label: 'Reason', type: 'string', required: true },
      ],
    }
    const wrapper = factory({ breakpoint })
    const approveBtn = wrapper.find('button[class*="bg-green-600"]')
    expect(approveBtn.attributes('disabled')).toBeDefined()
  })

  // =========================================================================
  // Expiration
  // =========================================================================
  it('shows expiration time', () => {
    const wrapper = factory()
    // Should show remaining time (1 hour from now -> "60m" or "1h 0m")
    const html = wrapper.html()
    expect(html).toContain('breakpoint.expires')
  })

  it('highlights expiring-soon breakpoints', () => {
    const breakpoint = { ...sampleBreakpoint, expiresAt: soonDate }
    const wrapper = factory({ breakpoint })
    expect(wrapper.find('.text-yellow-400').exists()).toBe(true)
  })

  it('shows "Expired" for past expiration', () => {
    const breakpoint = { ...sampleBreakpoint, expiresAt: pastDate }
    const wrapper = factory({ breakpoint })
    expect(wrapper.html()).toContain('Expired')
  })

  // =========================================================================
  // Context snapshot
  // =========================================================================
  it('shows context snapshot section when data exists', () => {
    const wrapper = factory()
    expect(wrapper.html()).toContain('breakpoint.contextSnapshot')
  })

  it('hides context snapshot when no data', () => {
    const breakpoint = { ...sampleBreakpoint, contextSnapshot: {} }
    const wrapper = factory({ breakpoint })
    // The section should not be rendered (v-if checks Object.keys length)
    expect(wrapper.html()).not.toContain('breakpoint.contextSnapshot')
  })
})
