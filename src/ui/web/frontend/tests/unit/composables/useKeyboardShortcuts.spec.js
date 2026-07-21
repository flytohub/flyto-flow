import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock Vue lifecycle hooks since we're not in a component context
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onMounted: vi.fn((cb) => cb()),
    onUnmounted: vi.fn()
  }
})

import { useClipboard } from '@/composables/keyboardShortcuts/useClipboard'
import { useHistory } from '@/composables/keyboardShortcuts/useHistory'
import { hasModifier, DEFAULT_SHORTCUTS } from '@/composables/keyboardShortcuts/constants'
import { useKeyboardShortcuts } from '@/composables/keyboardShortcuts/useKeyboardShortcutsCore'

describe('useClipboard', () => {
  it('starts with no data', () => {
    const { hasData } = useClipboard()
    expect(hasData.value).toBe(false)
  })

  it('copy stores data (deep clone)', () => {
    const { copy, paste, hasData } = useClipboard()
    const data = { a: 1, b: [2, 3] }
    copy(data)
    expect(hasData.value).toBe(true)

    // Verify deep clone
    data.a = 999
    const pasted = paste()
    expect(pasted.a).toBe(1)
  })

  it('paste returns deep clone of stored data', () => {
    const { copy, paste } = useClipboard()
    copy({ x: 'hello' })
    const p1 = paste()
    const p2 = paste()
    expect(p1).toEqual(p2)
    expect(p1).not.toBe(p2) // different references
  })

  it('paste returns null when no data', () => {
    const { paste } = useClipboard()
    expect(paste()).toBeNull()
  })

  it('clear removes data', () => {
    const { copy, clear, hasData } = useClipboard()
    copy({ data: true })
    clear()
    expect(hasData.value).toBe(false)
  })
})

describe('useHistory', () => {
  it('starts empty', () => {
    const { canUndo, canRedo, historySize } = useHistory()
    expect(canUndo.value).toBe(false)
    expect(canRedo.value).toBe(false)
    expect(historySize.value).toBe(0)
  })

  it('push adds state', () => {
    const { push, historySize } = useHistory()
    push({ step: 1 })
    expect(historySize.value).toBe(1)
    push({ step: 2 })
    expect(historySize.value).toBe(2)
  })

  it('undo returns previous state', () => {
    const { push, undo, canUndo } = useHistory()
    push({ step: 1 })
    push({ step: 2 })
    expect(canUndo.value).toBe(true)
    const state = undo()
    expect(state).toEqual({ step: 1 })
  })

  it('undo returns null when at start', () => {
    const { push, undo } = useHistory()
    push({ step: 1 })
    expect(undo()).toBeNull()
  })

  it('redo returns next state', () => {
    const { push, undo, redo, canRedo } = useHistory()
    push({ step: 1 })
    push({ step: 2 })
    undo()
    expect(canRedo.value).toBe(true)
    const state = redo()
    expect(state).toEqual({ step: 2 })
  })

  it('redo returns null when at end', () => {
    const { push, redo } = useHistory()
    push({ step: 1 })
    expect(redo()).toBeNull()
  })

  it('push after undo discards future states', () => {
    const { push, undo, redo, historySize } = useHistory()
    push({ step: 1 })
    push({ step: 2 })
    push({ step: 3 })
    undo() // at step 2
    push({ step: 4 }) // discard step 3
    expect(historySize.value).toBe(3) // [1, 2, 4]
    expect(redo()).toBeNull()
  })

  it('respects maxSize limit', () => {
    const { push, historySize } = useHistory({ maxSize: 3 })
    push({ s: 1 })
    push({ s: 2 })
    push({ s: 3 })
    push({ s: 4 }) // should drop oldest
    expect(historySize.value).toBe(3)
  })

  it('clear resets everything', () => {
    const { push, clear, historySize, canUndo, canRedo } = useHistory()
    push({ s: 1 })
    push({ s: 2 })
    clear()
    expect(historySize.value).toBe(0)
    expect(canUndo.value).toBe(false)
    expect(canRedo.value).toBe(false)
  })
})

describe('DEFAULT_SHORTCUTS', () => {
  it('has expected shortcut definitions', () => {
    expect(DEFAULT_SHORTCUTS.copy).toEqual({ key: 'c', modifier: true, description: expect.any(String) })
    expect(DEFAULT_SHORTCUTS.undo).toEqual({ key: 'z', modifier: true, description: expect.any(String) })
    expect(DEFAULT_SHORTCUTS.redo).toEqual({ key: 'z', modifier: true, shift: true, description: expect.any(String) })
    expect(DEFAULT_SHORTCUTS.delete.key).toEqual(['Delete', 'Backspace'])
    expect(DEFAULT_SHORTCUTS.escape.key).toBe('Escape')
  })
})

describe('hasModifier', () => {
  it('checks ctrlKey on non-Mac platforms', () => {
    // In jsdom, navigator.platform is typically empty, so isMac = false
    expect(hasModifier({ ctrlKey: true, metaKey: false })).toBe(true)
    expect(hasModifier({ ctrlKey: false, metaKey: true })).toBe(false)
  })
})

describe('useKeyboardShortcuts', () => {
  let addEventListenerSpy, removeEventListenerSpy

  beforeEach(() => {
    addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
  })

  it('registers keydown listener on mount', () => {
    useKeyboardShortcuts({})
    expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
  })

  it('returns expected API', () => {
    const result = useKeyboardShortcuts({})
    expect(result).toHaveProperty('activeShortcuts')
    expect(result).toHaveProperty('lastTriggered')
    expect(result).toHaveProperty('availableShortcuts')
    expect(result).toHaveProperty('getShortcutDisplay')
    expect(result).toHaveProperty('isMac')
  })

  it('getShortcutDisplay formats shortcut strings', () => {
    const { getShortcutDisplay } = useKeyboardShortcuts({})
    const display = getShortcutDisplay('copy')
    // On non-Mac (jsdom), should be "Ctrl+C"
    expect(display).toContain('C')
  })

  it('getShortcutDisplay returns empty for unknown action', () => {
    const { getShortcutDisplay } = useKeyboardShortcuts({})
    expect(getShortcutDisplay('nonexistent')).toBe('')
  })

  it('availableShortcuts only includes actions with handlers', () => {
    const { availableShortcuts } = useKeyboardShortcuts({
      copy: vi.fn(),
      save: vi.fn()
    })
    const actions = availableShortcuts.value.map(s => s.action)
    expect(actions).toContain('copy')
    expect(actions).toContain('save')
    expect(actions).not.toContain('paste') // no handler
  })

  it('dispatches handler when matching shortcut key event fires', () => {
    const copyHandler = vi.fn()
    useKeyboardShortcuts({ copy: copyHandler })

    // Simulate Ctrl+C keydown
    const event = new KeyboardEvent('keydown', {
      key: 'c',
      ctrlKey: true,
      bubbles: true
    })
    window.dispatchEvent(event)
    expect(copyHandler).toHaveBeenCalled()
  })

  it('does not dispatch when disabled', () => {
    const { ref } = require('vue')
    const enabled = ref(false)
    const copyHandler = vi.fn()
    useKeyboardShortcuts({ copy: copyHandler }, { enabled })

    const event = new KeyboardEvent('keydown', {
      key: 'c',
      ctrlKey: true,
      bubbles: true
    })
    window.dispatchEvent(event)
    expect(copyHandler).not.toHaveBeenCalled()
  })
})
