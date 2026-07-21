/**
 * storageService Unit Tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { localStore, sessionStore, storageService } from '@/services/storageService'

describe('storageService', () => {
  beforeEach(() => {
    localStorage.clear()
    sessionStorage.clear()
  })

  // =========================================================================
  // localStore
  // =========================================================================

  describe('localStore', () => {
    describe('get', () => {
      it('should return parsed JSON value', () => {
        localStorage.setItem('key', JSON.stringify({ a: 1 }))
        expect(localStore.get('key')).toEqual({ a: 1 })
      })

      it('should return plain string if not valid JSON', () => {
        localStorage.setItem('key', 'plain text')
        expect(localStore.get('key')).toBe('plain text')
      })

      it('should return fallback when key does not exist', () => {
        expect(localStore.get('missing', 'default')).toBe('default')
      })

      it('should return null as default fallback', () => {
        expect(localStore.get('missing')).toBeNull()
      })

      it('should return fallback on storage error', () => {
        vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
          throw new Error('storage error')
        })
        expect(localStore.get('key', 'fallback')).toBe('fallback')
        vi.restoreAllMocks()
      })

      it('should parse boolean values', () => {
        localStorage.setItem('flag', 'true')
        expect(localStore.get('flag')).toBe(true)
      })

      it('should parse number values', () => {
        localStorage.setItem('count', '42')
        expect(localStore.get('count')).toBe(42)
      })

      it('should parse array values', () => {
        localStorage.setItem('arr', JSON.stringify([1, 2, 3]))
        expect(localStore.get('arr')).toEqual([1, 2, 3])
      })

      it('should return null for null storage value', () => {
        expect(localStore.get('nonexistent')).toBeNull()
      })
    })

    describe('getRaw', () => {
      it('should return raw string value', () => {
        localStorage.setItem('key', '{"a":1}')
        expect(localStore.getRaw('key')).toBe('{"a":1}')
      })

      it('should return null for missing key', () => {
        expect(localStore.getRaw('missing')).toBeNull()
      })

      it('should return null on error', () => {
        vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
          throw new Error('error')
        })
        expect(localStore.getRaw('key')).toBeNull()
        vi.restoreAllMocks()
      })
    })

    describe('set', () => {
      it('should store JSON-stringified value', () => {
        localStore.set('key', { a: 1 })
        expect(localStorage.getItem('key')).toBe('{"a":1}')
      })

      it('should store string values directly', () => {
        localStore.set('key', 'hello')
        expect(localStorage.getItem('key')).toBe('hello')
      })

      it('should return true on success', () => {
        expect(localStore.set('key', 'value')).toBe(true)
      })

      it('should return false on error', () => {
        vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
          throw new Error('quota exceeded')
        })
        expect(localStore.set('key', 'value')).toBe(false)
        vi.restoreAllMocks()
      })

      it('should store arrays', () => {
        localStore.set('arr', [1, 2, 3])
        expect(JSON.parse(localStorage.getItem('arr'))).toEqual([1, 2, 3])
      })

      it('should store booleans as JSON', () => {
        localStore.set('flag', true)
        expect(localStorage.getItem('flag')).toBe('true')
      })
    })

    describe('remove', () => {
      it('should remove key from storage', () => {
        localStorage.setItem('key', 'value')
        localStore.remove('key')
        expect(localStorage.getItem('key')).toBeNull()
      })

      it('should return true on success', () => {
        expect(localStore.remove('key')).toBe(true)
      })

      it('should return false on error', () => {
        vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
          throw new Error('error')
        })
        expect(localStore.remove('key')).toBe(false)
        vi.restoreAllMocks()
      })
    })

    describe('has', () => {
      it('should return true for existing key', () => {
        localStorage.setItem('key', 'value')
        expect(localStore.has('key')).toBe(true)
      })

      it('should return false for missing key', () => {
        expect(localStore.has('missing')).toBe(false)
      })

      it('should return false on error', () => {
        vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
          throw new Error('error')
        })
        expect(localStore.has('key')).toBe(false)
        vi.restoreAllMocks()
      })
    })

    describe('clear', () => {
      it('should clear all items', () => {
        localStorage.setItem('a', '1')
        localStorage.setItem('b', '2')
        localStore.clear()
        expect(localStorage.length).toBe(0)
      })

      it('should return true on success', () => {
        expect(localStore.clear()).toBe(true)
      })

      it('should return false on error', () => {
        vi.spyOn(Storage.prototype, 'clear').mockImplementation(() => {
          throw new Error('error')
        })
        expect(localStore.clear()).toBe(false)
        vi.restoreAllMocks()
      })
    })
  })

  // =========================================================================
  // sessionStore
  // =========================================================================

  describe('sessionStore', () => {
    it('should get/set values in sessionStorage', () => {
      sessionStore.set('key', { x: 42 })
      expect(sessionStore.get('key')).toEqual({ x: 42 })
    })

    it('should remove values from sessionStorage', () => {
      sessionStore.set('key', 'val')
      sessionStore.remove('key')
      expect(sessionStore.has('key')).toBe(false)
    })

    it('should clear sessionStorage', () => {
      sessionStore.set('a', 1)
      sessionStore.set('b', 2)
      sessionStore.clear()
      expect(sessionStore.has('a')).toBe(false)
      expect(sessionStore.has('b')).toBe(false)
    })

    it('should return raw values', () => {
      sessionStorage.setItem('raw', 'not-json')
      expect(sessionStore.getRaw('raw')).toBe('not-json')
    })
  })

  // =========================================================================
  // storageService default export
  // =========================================================================

  describe('storageService', () => {
    it('should expose local and session wrappers', () => {
      expect(storageService.local).toBe(localStore)
      expect(storageService.session).toBe(sessionStore)
    })
  })
})
