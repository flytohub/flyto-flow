import { describe, it, expect, vi, beforeEach } from 'vitest'

const {
  mockDownloadViaAnchor,
  mockDownloadText,
  mockDownloadJson,
  mockDownloadImage,
  mockCopyToClipboard,
  mockOpenInNewTab
} = vi.hoisted(() => ({
  mockDownloadViaAnchor: vi.fn(),
  mockDownloadText: vi.fn(),
  mockDownloadJson: vi.fn(),
  mockDownloadImage: vi.fn(),
  mockCopyToClipboard: vi.fn(),
  mockOpenInNewTab: vi.fn()
}))

vi.mock('@/services/domUtils', () => ({
  downloadViaAnchor: mockDownloadViaAnchor,
  downloadText: mockDownloadText,
  downloadJson: mockDownloadJson,
  downloadImage: mockDownloadImage,
  copyToClipboard: mockCopyToClipboard,
  openInNewTab: mockOpenInNewTab
}))

import { useResultActions } from '@/composables/useResultActions'

describe('useResultActions', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns the expected API', () => {
    const actions = useResultActions()
    expect(typeof actions.downloadResult).toBe('function')
    expect(typeof actions.copyResult).toBe('function')
    expect(typeof actions.copyImageToClipboard).toBe('function')
    expect(typeof actions.downloadAsFile).toBe('function')
    expect(typeof actions.downloadAsJson).toBe('function')
  })

  describe('downloadResult', () => {
    it('does nothing when result is null', () => {
      const { downloadResult } = useResultActions()
      downloadResult(null)
      expect(mockOpenInNewTab).not.toHaveBeenCalled()
      expect(mockDownloadImage).not.toHaveBeenCalled()
    })

    it('opens download URL in new tab', () => {
      const { downloadResult } = useResultActions()
      downloadResult({ downloadUrl: 'https://example.com/file.pdf' })
      expect(mockOpenInNewTab).toHaveBeenCalledWith('https://example.com/file.pdf')
    })

    it('opens file_url in new tab (snake_case)', () => {
      const { downloadResult } = useResultActions()
      downloadResult({ file_url: 'https://example.com/data.csv' })
      expect(mockOpenInNewTab).toHaveBeenCalledWith('https://example.com/data.csv')
    })

    it('downloads base64 image', () => {
      const { downloadResult } = useResultActions()
      downloadResult({ imageBase64: 'iVBORw0...' })
      expect(mockDownloadImage).toHaveBeenCalledWith('iVBORw0...', 'result.png', true)
    })

    it('downloads image by URL', () => {
      const { downloadResult } = useResultActions()
      downloadResult({ imageUrl: 'https://example.com/img.png' })
      expect(mockDownloadViaAnchor).toHaveBeenCalledWith('https://example.com/img.png', 'result.png')
    })

    it('uses getResult option when no argument passed', () => {
      const { downloadResult } = useResultActions({
        getResult: () => ({ downloadUrl: 'https://auto.com/file' })
      })
      downloadResult()
      expect(mockOpenInNewTab).toHaveBeenCalledWith('https://auto.com/file')
    })
  })

  describe('copyResult', () => {
    it('returns false for null result', async () => {
      const { copyResult } = useResultActions()
      const result = await copyResult(null)
      expect(result).toBe(false)
    })

    it('copies string result directly', async () => {
      mockCopyToClipboard.mockResolvedValue(true)
      const { copyResult } = useResultActions()
      await copyResult('hello world')
      expect(mockCopyToClipboard).toHaveBeenCalledWith('hello world')
    })

    it('copies object result as JSON', async () => {
      mockCopyToClipboard.mockResolvedValue(true)
      const { copyResult } = useResultActions()
      await copyResult({ key: 'value' })
      expect(mockCopyToClipboard).toHaveBeenCalledWith(JSON.stringify({ key: 'value' }, null, 2))
    })
  })

  describe('copyImageToClipboard', () => {
    it('returns false for null result', async () => {
      const { copyImageToClipboard } = useResultActions()
      const result = await copyImageToClipboard(null)
      expect(result).toBe(false)
    })

    it('copies base64 image as data URI', async () => {
      mockCopyToClipboard.mockResolvedValue(true)
      const { copyImageToClipboard } = useResultActions()
      await copyImageToClipboard({ imageBase64: 'abc123' })
      expect(mockCopyToClipboard).toHaveBeenCalledWith('data:image/png;base64,abc123')
    })

    it('copies image URL', async () => {
      mockCopyToClipboard.mockResolvedValue(true)
      const { copyImageToClipboard } = useResultActions()
      await copyImageToClipboard({ imageUrl: 'https://example.com/pic.png' })
      expect(mockCopyToClipboard).toHaveBeenCalledWith('https://example.com/pic.png')
    })

    it('returns false when no image data', async () => {
      const { copyImageToClipboard } = useResultActions()
      const result = await copyImageToClipboard({ text: 'no image' })
      expect(result).toBe(false)
    })
  })

  describe('downloadAsFile', () => {
    it('does nothing for null result', () => {
      const { downloadAsFile } = useResultActions()
      downloadAsFile(null)
      expect(mockDownloadText).not.toHaveBeenCalled()
    })

    it('downloads string as text file', () => {
      const { downloadAsFile } = useResultActions()
      downloadAsFile('hello', 'output.txt')
      expect(mockDownloadText).toHaveBeenCalledWith('hello', 'output.txt')
    })

    it('downloads object as JSON text', () => {
      const { downloadAsFile } = useResultActions()
      downloadAsFile({ a: 1 })
      expect(mockDownloadText).toHaveBeenCalledWith(
        JSON.stringify({ a: 1 }, null, 2),
        'result.txt'
      )
    })
  })

  describe('downloadAsJson', () => {
    it('does nothing for null result', () => {
      const { downloadAsJson } = useResultActions()
      downloadAsJson(null)
      expect(mockDownloadJson).not.toHaveBeenCalled()
    })

    it('downloads result as JSON', () => {
      const { downloadAsJson } = useResultActions()
      downloadAsJson({ data: [1, 2, 3] }, 'data.json')
      expect(mockDownloadJson).toHaveBeenCalledWith({ data: [1, 2, 3] }, 'data.json')
    })
  })
})
