import { describe, it, expect } from 'vitest'
import { getIconUrl, searchIcons, BRAND_ICONS, CATEGORY_ICONS } from '@/utils/iconify'

describe('iconify utilities', () => {
  describe('getIconUrl', () => {
    it('returns null for falsy input', () => {
      expect(getIconUrl(null)).toBeNull()
      expect(getIconUrl(undefined)).toBeNull()
      expect(getIconUrl('')).toBeNull()
    })

    it('generates URL for prefixed icon ID', () => {
      const url = getIconUrl('simple-icons:openai')
      expect(url).toContain('https://api.iconify.design/simple-icons/openai.svg')
    })

    it('defaults to lucide prefix for unprefixed icon ID', () => {
      const url = getIconUrl('bot')
      expect(url).toContain('https://api.iconify.design/lucide/bot.svg')
    })

    it('includes size params by default', () => {
      const url = getIconUrl('lucide:bot')
      expect(url).toContain('width=24')
      expect(url).toContain('height=24')
    })

    it('includes custom size', () => {
      const url = getIconUrl('lucide:bot', { size: 32 })
      expect(url).toContain('width=32')
      expect(url).toContain('height=32')
    })

    it('includes color with hash prefix', () => {
      const url = getIconUrl('lucide:bot', { color: '#FF0000' })
      expect(url).toContain('color=%23FF0000')
    })

    it('adds hash prefix to color without one', () => {
      const url = getIconUrl('lucide:bot', { color: 'FF0000' })
      expect(url).toContain('color=%23FF0000')
    })
  })

  describe('searchIcons', () => {
    it('returns popular icons when no query', () => {
      const results = searchIcons('')
      expect(results.length).toBeGreaterThan(0)
      expect(results.length).toBeLessThanOrEqual(30)
    })

    it('returns popular icons for null query', () => {
      const results = searchIcons(null)
      expect(results.length).toBeGreaterThan(0)
    })

    it('filters by name match', () => {
      const results = searchIcons('openai')
      expect(results.length).toBeGreaterThan(0)
      expect(results.some(r => r.name.toLowerCase().includes('openai'))).toBe(true)
    })

    it('filters by icon ID match', () => {
      const results = searchIcons('simple-icons:github')
      expect(results.length).toBeGreaterThan(0)
    })

    it('respects limit option', () => {
      const results = searchIcons('', { limit: 5 })
      expect(results.length).toBeLessThanOrEqual(5)
    })

    it('can exclude brands', () => {
      const results = searchIcons('', { includeBrands: false })
      const hasBrand = results.some(r => r.id.startsWith('simple-icons'))
      expect(hasBrand).toBe(false)
    })

    it('can exclude categories', () => {
      const results = searchIcons('', { includeCategories: false })
      const hasCategory = results.some(r => r.id.startsWith('lucide'))
      expect(hasCategory).toBe(false)
    })

    it('is case-insensitive', () => {
      const lower = searchIcons('github')
      const upper = searchIcons('GITHUB')
      expect(lower.length).toBe(upper.length)
    })

    it('returns empty for no match', () => {
      const results = searchIcons('xyznonexistent12345')
      expect(results).toEqual([])
    })
  })

  describe('BRAND_ICONS', () => {
    it('is an array with id, name, color', () => {
      expect(Array.isArray(BRAND_ICONS)).toBe(true)
      expect(BRAND_ICONS.length).toBeGreaterThan(0)
      expect(BRAND_ICONS[0]).toHaveProperty('id')
      expect(BRAND_ICONS[0]).toHaveProperty('name')
      expect(BRAND_ICONS[0]).toHaveProperty('color')
    })
  })

  describe('CATEGORY_ICONS', () => {
    it('is an array with id, name, color', () => {
      expect(Array.isArray(CATEGORY_ICONS)).toBe(true)
      expect(CATEGORY_ICONS.length).toBeGreaterThan(0)
      expect(CATEGORY_ICONS[0]).toHaveProperty('id')
      expect(CATEGORY_ICONS[0]).toHaveProperty('name')
      expect(CATEGORY_ICONS[0]).toHaveProperty('color')
    })
  })
})
