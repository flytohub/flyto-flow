/**
 * domUtils Unit Tests
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  downloadViaAnchor,
  downloadBlob,
  downloadText,
  downloadJson,
  downloadBase64,
  downloadImage,
  copyToClipboard,
  openInNewTab,
  createCanvas,
  escapeHtml,
  triggerFileInput
} from '@/services/domUtils'

describe('domUtils', () => {
  let appendChildSpy
  let removeChildSpy
  let originalCreateObjectURL
  let originalRevokeObjectURL

  beforeEach(() => {
    appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation(() => {})
    removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => {})

    // jsdom does not implement URL.createObjectURL/revokeObjectURL, so stub them
    originalCreateObjectURL = URL.createObjectURL
    originalRevokeObjectURL = URL.revokeObjectURL
    URL.createObjectURL = vi.fn().mockReturnValue('blob:http://localhost/fake-id')
    URL.revokeObjectURL = vi.fn()
  })

  afterEach(() => {
    URL.createObjectURL = originalCreateObjectURL
    URL.revokeObjectURL = originalRevokeObjectURL
    vi.restoreAllMocks()
  })

  // =========================================================================
  // downloadViaAnchor
  // =========================================================================

  describe('downloadViaAnchor', () => {
    it('should create an anchor element and trigger click', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')
      const clickSpy = vi.fn()

      createElementSpy.mockReturnValueOnce({
        href: '',
        download: '',
        style: {},
        click: clickSpy
      })

      downloadViaAnchor('http://example.com/file.txt', 'file.txt')

      expect(createElementSpy).toHaveBeenCalledWith('a')
      expect(clickSpy).toHaveBeenCalled()
      expect(appendChildSpy).toHaveBeenCalled()
      expect(removeChildSpy).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // downloadBlob
  // =========================================================================

  describe('downloadBlob', () => {
    it('should create object URL and download', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')
      const clickSpy = vi.fn()

      createElementSpy.mockReturnValueOnce({
        href: '',
        download: '',
        style: {},
        click: clickSpy
      })

      const blob = new Blob(['hello'], { type: 'text/plain' })
      downloadBlob(blob, 'test.txt')

      expect(URL.createObjectURL).toHaveBeenCalledWith(blob)
      expect(clickSpy).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // downloadText
  // =========================================================================

  describe('downloadText', () => {
    it('should create blob from text and download', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')

      createElementSpy.mockReturnValueOnce({
        href: '',
        download: '',
        style: {},
        click: vi.fn()
      })

      downloadText('hello world', 'test.txt', 'text/plain')
      expect(URL.createObjectURL).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // downloadJson
  // =========================================================================

  describe('downloadJson', () => {
    it('should stringify object and download as JSON', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')

      createElementSpy.mockReturnValueOnce({
        href: '',
        download: '',
        style: {},
        click: vi.fn()
      })

      downloadJson({ key: 'value' }, 'data.json')
      expect(URL.createObjectURL).toHaveBeenCalled()
    })

    it('should use string data directly', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')

      createElementSpy.mockReturnValueOnce({
        href: '',
        download: '',
        style: {},
        click: vi.fn()
      })

      downloadJson('{"already":"json"}', 'data.json')
      expect(URL.createObjectURL).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // downloadBase64
  // =========================================================================

  describe('downloadBase64', () => {
    it('should create data URL from base64 and download', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')
      const mockAnchor = { href: '', download: '', style: {}, click: vi.fn() }
      createElementSpy.mockReturnValueOnce(mockAnchor)

      downloadBase64('SGVsbG8=', 'file.bin', 'application/octet-stream')

      expect(mockAnchor.href).toBe('data:application/octet-stream;base64,SGVsbG8=')
      expect(mockAnchor.download).toBe('file.bin')
      expect(mockAnchor.click).toHaveBeenCalled()
    })
  })

  // =========================================================================
  // downloadImage
  // =========================================================================

  describe('downloadImage', () => {
    it('should download base64 image when isBase64 is true', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')
      const mockAnchor = { href: '', download: '', style: {}, click: vi.fn() }
      createElementSpy.mockReturnValueOnce(mockAnchor)

      downloadImage('iVBOR...', 'img.png', true)

      expect(mockAnchor.href).toContain('data:image/png;base64,')
    })

    it('should download URL image when isBase64 is false', () => {
      const createElementSpy = vi.spyOn(document, 'createElement')
      const mockAnchor = { href: '', download: '', style: {}, click: vi.fn() }
      createElementSpy.mockReturnValueOnce(mockAnchor)

      downloadImage('http://example.com/img.png', 'img.png', false)

      expect(mockAnchor.href).toBe('http://example.com/img.png')
    })
  })

  // =========================================================================
  // copyToClipboard
  // =========================================================================

  describe('copyToClipboard', () => {
    it('should use navigator.clipboard.writeText when available', async () => {
      const writeTextSpy = vi.fn().mockResolvedValue(undefined)
      const originalClipboard = navigator.clipboard
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: writeTextSpy },
        writable: true,
        configurable: true
      })

      const result = await copyToClipboard('hello')
      expect(result).toBe(true)
      expect(writeTextSpy).toHaveBeenCalledWith('hello')

      Object.defineProperty(navigator, 'clipboard', {
        value: originalClipboard,
        writable: true,
        configurable: true
      })
    })

    it('should fallback to execCommand when clipboard API fails', async () => {
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
        writable: true,
        configurable: true
      })

      const mockTextArea = {
        value: '',
        style: { cssText: '' },
        select: vi.fn()
      }
      vi.spyOn(document, 'createElement').mockReturnValueOnce(mockTextArea)
      document.execCommand = vi.fn().mockReturnValue(true)

      const result = await copyToClipboard('fallback text')
      expect(result).toBe(true)
      expect(mockTextArea.select).toHaveBeenCalled()
    })

    it('should return false when both methods fail', async () => {
      Object.defineProperty(navigator, 'clipboard', {
        value: { writeText: vi.fn().mockRejectedValue(new Error('denied')) },
        writable: true,
        configurable: true
      })

      const mockTextArea = {
        value: '',
        style: { cssText: '' },
        select: vi.fn()
      }
      vi.spyOn(document, 'createElement').mockReturnValueOnce(mockTextArea)
      document.execCommand = vi.fn().mockImplementation(() => { throw new Error('fail') })

      const result = await copyToClipboard('text')
      expect(result).toBe(false)
    })
  })

  // =========================================================================
  // openInNewTab
  // =========================================================================

  describe('openInNewTab', () => {
    it('should call window.open with correct params', () => {
      const openSpy = vi.spyOn(window, 'open').mockImplementation(() => null)
      openInNewTab('http://example.com')
      expect(openSpy).toHaveBeenCalledWith('http://example.com', '_blank', 'noopener,noreferrer')
    })
  })

  // =========================================================================
  // createCanvas
  // =========================================================================

  describe('createCanvas', () => {
    it('should create canvas with specified dimensions', () => {
      const canvas = createCanvas(800, 600)
      expect(canvas.width).toBe(800)
      expect(canvas.height).toBe(600)
    })

    it('should apply default styles', () => {
      const canvas = createCanvas(100, 100)
      expect(canvas.style.position).toBe('absolute')
      expect(canvas.style.inset).toBe('0')
    })

    it('should merge custom styles', () => {
      const canvas = createCanvas(100, 100, { zIndex: '10' })
      expect(canvas.style.zIndex).toBe('10')
      expect(canvas.style.position).toBe('absolute')
    })
  })

  // =========================================================================
  // escapeHtml
  // =========================================================================

  describe('escapeHtml', () => {
    it('should escape HTML special characters', () => {
      const result = escapeHtml('<script>alert("xss")</script>')
      expect(result).not.toContain('<script>')
      expect(result).toContain('&lt;')
    })

    it('should handle plain text without escaping', () => {
      const result = escapeHtml('hello world')
      expect(result).toBe('hello world')
    })

    it('should escape ampersands', () => {
      const result = escapeHtml('a & b')
      expect(result).toContain('&amp;')
    })
  })

  // =========================================================================
  // triggerFileInput
  // =========================================================================

  describe('triggerFileInput', () => {
    it('should create file input and trigger click', () => {
      const mockInput = {
        type: '',
        accept: '',
        multiple: false,
        style: {},
        onchange: null,
        oncancel: null,
        click: vi.fn(),
        files: []
      }
      vi.spyOn(document, 'createElement').mockReturnValueOnce(mockInput)

      const promise = triggerFileInput({ accept: '.json', multiple: true })

      expect(mockInput.type).toBe('file')
      expect(mockInput.accept).toBe('.json')
      expect(mockInput.multiple).toBe(true)
      expect(mockInput.click).toHaveBeenCalled()

      // Simulate file selection
      mockInput.files = ['file1']
      mockInput.onchange()

      return promise.then(files => {
        expect(files).toEqual(['file1'])
      })
    })

    it('should resolve null on cancel', () => {
      const mockInput = {
        type: '',
        accept: '',
        multiple: false,
        style: {},
        onchange: null,
        oncancel: null,
        click: vi.fn(),
        files: []
      }
      vi.spyOn(document, 'createElement').mockReturnValueOnce(mockInput)

      const promise = triggerFileInput()
      mockInput.oncancel()

      return promise.then(result => {
        expect(result).toBeNull()
      })
    })
  })
})
