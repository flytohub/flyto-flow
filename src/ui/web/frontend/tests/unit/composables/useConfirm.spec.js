import { describe, it, expect, beforeEach } from 'vitest'
import { useConfirm } from '@/composables/useConfirm'

describe('useConfirm', () => {
  let confirmDialog

  beforeEach(() => {
    confirmDialog = useConfirm()
    confirmDialog.close()
  })

  it('returns the expected API', () => {
    expect(confirmDialog).toHaveProperty('state')
    expect(confirmDialog).toHaveProperty('show')
    expect(confirmDialog).toHaveProperty('confirm')
    expect(confirmDialog).toHaveProperty('cancel')
    expect(confirmDialog).toHaveProperty('close')
  })

  it('starts with dialog hidden', () => {
    expect(confirmDialog.state.show).toBe(false)
  })

  describe('show', () => {
    it('opens the dialog with options', () => {
      confirmDialog.show({
        title: 'Delete?',
        message: 'Are you sure?',
        type: 'danger',
        confirmText: 'Yes',
        cancelText: 'No'
      })

      expect(confirmDialog.state.show).toBe(true)
      expect(confirmDialog.state.title).toBe('Delete?')
      expect(confirmDialog.state.message).toBe('Are you sure?')
      expect(confirmDialog.state.type).toBe('danger')
      expect(confirmDialog.state.confirmText).toBe('Yes')
      expect(confirmDialog.state.cancelText).toBe('No')
    })

    it('uses defaults for missing options', () => {
      confirmDialog.show({})

      expect(confirmDialog.state.type).toBe('warning')
      expect(confirmDialog.state.title).toBe('')
      expect(confirmDialog.state.confirmText).toBe('Confirm')
      expect(confirmDialog.state.cancelText).toBe('Cancel')
    })

    it('returns a promise', () => {
      const result = confirmDialog.show({ title: 'Test' })
      expect(result).toBeInstanceOf(Promise)
    })
  })

  describe('confirm', () => {
    it('resolves promise with true', async () => {
      const promise = confirmDialog.show({ title: 'Test' })
      confirmDialog.confirm()
      const result = await promise
      expect(result).toBe(true)
    })

    it('closes the dialog', () => {
      confirmDialog.show({ title: 'Test' })
      confirmDialog.confirm()
      expect(confirmDialog.state.show).toBe(false)
    })
  })

  describe('cancel', () => {
    it('resolves promise with false', async () => {
      const promise = confirmDialog.show({ title: 'Test' })
      confirmDialog.cancel()
      const result = await promise
      expect(result).toBe(false)
    })

    it('closes the dialog', () => {
      confirmDialog.show({ title: 'Test' })
      confirmDialog.cancel()
      expect(confirmDialog.state.show).toBe(false)
    })
  })

  describe('close', () => {
    it('hides dialog and clears resolve', () => {
      confirmDialog.show({ title: 'Test' })
      confirmDialog.close()
      expect(confirmDialog.state.show).toBe(false)
    })
  })

  describe('singleton behavior', () => {
    it('shares state across multiple calls', () => {
      const c2 = useConfirm()
      confirmDialog.show({ title: 'Shared' })
      expect(c2.state.show).toBe(true)
      expect(c2.state.title).toBe('Shared')
    })
  })
})
