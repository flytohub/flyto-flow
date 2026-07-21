import { describe, it, expect } from 'vitest'
import { getBaseModuleType, resolveModuleLabel, isTemplateModule } from '@/utils/moduleIdUtils'

describe('moduleIdUtils', () => {
  describe('getBaseModuleType', () => {
    it('returns empty string for falsy input', () => {
      expect(getBaseModuleType(null)).toBe('')
      expect(getBaseModuleType(undefined)).toBe('')
      expect(getBaseModuleType('')).toBe('')
    })

    it('returns "template.invoke" for template modules', () => {
      expect(getBaseModuleType('template.invoke:my-template')).toBe('template.invoke')
      expect(getBaseModuleType('template.invoke:abc-123')).toBe('template.invoke')
    })

    it('returns the moduleId as-is for regular modules', () => {
      expect(getBaseModuleType('browser.click')).toBe('browser.click')
      expect(getBaseModuleType('api.request')).toBe('api.request')
    })
  })

  describe('resolveModuleLabel', () => {
    it('returns empty string for falsy input', () => {
      expect(resolveModuleLabel(null)).toBe('')
      expect(resolveModuleLabel(undefined)).toBe('')
      expect(resolveModuleLabel('')).toBe('')
    })

    it('returns label from modulesStore metadata if available', () => {
      const store = {
        modulesMetadata: {
          'browser.goto': { label: 'Navigate to URL' }
        }
      }
      expect(resolveModuleLabel('browser.goto', store)).toBe('Navigate to URL')
    })

    it('falls back to title-cased last segment', () => {
      expect(resolveModuleLabel('browser.goto')).toBe('Goto')
      expect(resolveModuleLabel('browser.click_element')).toBe('Click Element')
    })

    it('handles single-segment module IDs', () => {
      expect(resolveModuleLabel('delay')).toBe('Delay')
    })
  })

  describe('isTemplateModule', () => {
    it('returns false for falsy input', () => {
      expect(isTemplateModule(null)).toBe(false)
      expect(isTemplateModule(undefined)).toBe(false)
      expect(isTemplateModule('')).toBe(false)
    })

    it('uses backend isTemplate flag when available', () => {
      const store = {
        modulesMetadata: {
          'my.module': { isTemplate: true }
        }
      }
      expect(isTemplateModule('my.module', store)).toBe(true)
    })

    it('uses backend isTemplate=false flag when available', () => {
      const store = {
        modulesMetadata: {
          'template.invoke:abc': { isTemplate: false }
        }
      }
      expect(isTemplateModule('template.invoke:abc', store)).toBe(false)
    })

    it('falls back to pattern matching when no metadata', () => {
      expect(isTemplateModule('template.invoke:abc')).toBe(true)
      expect(isTemplateModule('template.invoke')).toBe(true)
      expect(isTemplateModule('browser.click')).toBe(false)
    })
  })
})
