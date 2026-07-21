import { describe, it, expect } from 'vitest'
import { regionToFlag, localeToFlag } from '@/utils/emoji'

describe('emoji utilities', () => {
  describe('regionToFlag', () => {
    it('converts valid 2-letter region codes to flag emoji', () => {
      expect(regionToFlag('US')).toBe('\u{1F1FA}\u{1F1F8}')
      expect(regionToFlag('TW')).toBe('\u{1F1F9}\u{1F1FC}')
      expect(regionToFlag('JP')).toBe('\u{1F1EF}\u{1F1F5}')
    })

    it('handles lowercase region codes', () => {
      expect(regionToFlag('us')).toBe('\u{1F1FA}\u{1F1F8}')
      expect(regionToFlag('gb')).toBe('\u{1F1EC}\u{1F1E7}')
    })

    it('returns fallback for null/undefined', () => {
      expect(regionToFlag(null)).toBe('\u{1F310}')
      expect(regionToFlag(undefined)).toBe('\u{1F310}')
    })

    it('returns fallback for empty string', () => {
      expect(regionToFlag('')).toBe('\u{1F310}')
    })

    it('returns fallback for wrong length strings', () => {
      expect(regionToFlag('A')).toBe('\u{1F310}')
      expect(regionToFlag('USA')).toBe('\u{1F310}')
    })

    it('returns fallback for non-alpha characters', () => {
      expect(regionToFlag('12')).toBe('\u{1F310}')
      expect(regionToFlag('A1')).toBe('\u{1F310}')
    })

    it('returns fallback for non-string input', () => {
      expect(regionToFlag(42)).toBe('\u{1F310}')
      expect(regionToFlag({})).toBe('\u{1F310}')
    })

    it('uses custom fallback when provided', () => {
      expect(regionToFlag('invalid', '?')).toBe('?')
      expect(regionToFlag(null, 'N/A')).toBe('N/A')
    })
  })

  describe('localeToFlag', () => {
    it('converts known locale codes via direct mapping', () => {
      expect(localeToFlag('en')).toBe(regionToFlag('US'))
      expect(localeToFlag('zh-TW')).toBe(regionToFlag('TW'))
      expect(localeToFlag('ja')).toBe(regionToFlag('JP'))
      expect(localeToFlag('ko')).toBe(regionToFlag('KR'))
      expect(localeToFlag('fr')).toBe(regionToFlag('FR'))
    })

    it('extracts region from unknown locale with region part', () => {
      // e.g. 'xx-GB' -> tries 'GB' as region
      expect(localeToFlag('xx-GB')).toBe(regionToFlag('GB'))
    })

    it('falls back to language code mapping', () => {
      // 'de-XX' has no direct mapping, region part 'XX' is 2 chars so tries regionToFlag('XX')
      // 'de' alone maps to 'DE'
      expect(localeToFlag('de')).toBe(regionToFlag('DE'))
    })

    it('returns fallback for null/undefined', () => {
      expect(localeToFlag(null)).toBe('\u{1F310}')
      expect(localeToFlag(undefined)).toBe('\u{1F310}')
      expect(localeToFlag('')).toBe('\u{1F310}')
    })

    it('returns fallback for completely unknown locale', () => {
      expect(localeToFlag('xyz')).toBe('\u{1F310}')
    })

    it('uses custom fallback', () => {
      expect(localeToFlag('xyz', '?')).toBe('?')
    })
  })
})
