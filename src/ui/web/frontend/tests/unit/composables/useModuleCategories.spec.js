import { describe, it, expect, vi } from 'vitest'

vi.mock('lucide-vue-next', () => ({
  Box: 'BoxIcon',
  Package: 'PackageIcon'
}))

import { useModuleCategories, CATEGORY_CONFIG } from '@/composables/useModuleCategories'

describe('useModuleCategories', () => {
  const {
    getCategoryLabel,
    getCategoryColor,
    getCategoryGradient,
    getCategoryIcon,
    adjustColor,
    getAvailableCategories
  } = useModuleCategories()

  describe('getCategoryLabel', () => {
    it('returns configured label for known category', () => {
      expect(getCategoryLabel('default')).toBe('Module')
      expect(getCategoryLabel('my-templates')).toBe('My Templates')
    })

    it('capitalizes first letter for unknown category', () => {
      expect(getCategoryLabel('browser')).toBe('Browser')
      expect(getCategoryLabel('api')).toBe('Api')
    })
  })

  describe('getCategoryColor', () => {
    it('returns configured color for known category', () => {
      expect(getCategoryColor('my-templates')).toBe('#8B5CF6')
    })

    it('returns default color for unknown category', () => {
      expect(getCategoryColor('unknown')).toBe('#6C757D')
    })
  })

  describe('getCategoryGradient', () => {
    it('returns configured gradient for known category', () => {
      const gradient = getCategoryGradient('my-templates')
      expect(gradient).toContain('#8B5CF6')
      expect(gradient).toContain('linear-gradient')
    })

    it('returns default gradient for unknown category', () => {
      const gradient = getCategoryGradient('unknown')
      expect(gradient).toContain('#6C757D')
    })
  })

  describe('getCategoryIcon', () => {
    it('returns configured icon for known category', () => {
      expect(getCategoryIcon('default')).toBe('BoxIcon')
      expect(getCategoryIcon('my-templates')).toBe('PackageIcon')
    })

    it('returns Box for unknown category', () => {
      expect(getCategoryIcon('unknown')).toBe('BoxIcon')
    })
  })

  describe('adjustColor', () => {
    it('lightens a color with positive percent', () => {
      const result = adjustColor('#000000', 20)
      expect(result).toMatch(/^#[0-9a-f]{6}$/i)
      // 20% of 255 = 51 => R=G=B=51 => #333333
      expect(result).toBe('#333333')
    })

    it('does not exceed 255 per channel', () => {
      const result = adjustColor('#ffffff', 50)
      expect(result).toBe('#ffffff')
    })
  })

  describe('getAvailableCategories', () => {
    it('returns empty for no modules', () => {
      expect(getAvailableCategories([])).toEqual([])
    })

    it('extracts unique categories from modules', () => {
      const modules = [
        { category: 'browser' },
        { category: 'browser' },
        { category: 'api' }
      ]
      const cats = getAvailableCategories(modules)
      expect(cats).toHaveLength(2)
      expect(cats.map(c => c.name)).toContain('browser')
      expect(cats.map(c => c.name)).toContain('api')
    })

    it('falls back to moduleId prefix when no category', () => {
      const modules = [{ moduleId: 'scraper.extract_data' }]
      const cats = getAvailableCategories(modules)
      expect(cats[0].name).toBe('scraper')
    })

    it('defaults to "default" when no category or moduleId', () => {
      const modules = [{ label: 'Something' }]
      const cats = getAvailableCategories(modules)
      expect(cats[0].name).toBe('default')
    })

    it('returns capitalized labels', () => {
      const modules = [{ category: 'browser' }]
      const cats = getAvailableCategories(modules)
      expect(cats[0].label).toBe('Browser')
    })
  })
})
