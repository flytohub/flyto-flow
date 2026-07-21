import { describe, it, expect, vi, beforeEach } from 'vitest'

// Mock onUnmounted to avoid Vue component lifecycle errors
vi.mock('vue', async () => {
  const actual = await vi.importActual('vue')
  return {
    ...actual,
    onUnmounted: vi.fn()
  }
})

vi.mock('@/utils/format', () => ({
  formatFileSize: vi.fn((bytes) => `${bytes} B`)
}))

import { useFileInput } from '@/composables/useFileInput'

describe('useFileInput', () => {
  let fileInput
  const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
  const mockRevokeObjectURL = vi.fn()

  beforeEach(() => {
    globalThis.URL.createObjectURL = mockCreateObjectURL
    globalThis.URL.revokeObjectURL = mockRevokeObjectURL
    mockCreateObjectURL.mockClear()
    mockRevokeObjectURL.mockClear()
    fileInput = useFileInput()
  })

  it('returns the expected API', () => {
    expect(fileInput).toHaveProperty('filePreviewUrls')
    expect(fileInput).toHaveProperty('fileInputRefs')
    expect(fileInput).toHaveProperty('isDragging')
    expect(typeof fileInput.isImageFile).toBe('function')
    expect(typeof fileInput.isFileType).toBe('function')
    expect(typeof fileInput.getAcceptTypes).toBe('function')
    expect(typeof fileInput.setFile).toBe('function')
    expect(typeof fileInput.removeFile).toBe('function')
  })

  describe('isImageFile', () => {
    it('returns false for falsy input', () => {
      expect(fileInput.isImageFile(null)).toBe(false)
      expect(fileInput.isImageFile(undefined)).toBe(false)
    })

    it('returns true for image MIME types', () => {
      expect(fileInput.isImageFile({ type: 'image/png' })).toBe(true)
      expect(fileInput.isImageFile({ type: 'image/jpeg' })).toBe(true)
    })

    it('returns false for non-image types', () => {
      expect(fileInput.isImageFile({ type: 'text/plain' })).toBe(false)
      expect(fileInput.isImageFile({ type: 'application/pdf' })).toBe(false)
    })
  })

  describe('isFileType', () => {
    it('returns true for "file" and "image"', () => {
      expect(fileInput.isFileType('file')).toBe(true)
      expect(fileInput.isFileType('image')).toBe(true)
    })

    it('returns false for other types', () => {
      expect(fileInput.isFileType('text')).toBe(false)
      expect(fileInput.isFileType('number')).toBe(false)
    })
  })

  describe('getAcceptTypes', () => {
    it('returns custom accept when provided', () => {
      expect(fileInput.getAcceptTypes({ accept: '.csv,.xlsx' })).toBe('.csv,.xlsx')
    })

    it('returns image/* for image type', () => {
      expect(fileInput.getAcceptTypes({ type: 'image' })).toBe('image/*')
    })

    it('returns */* as default', () => {
      expect(fileInput.getAcceptTypes({ type: 'file' })).toBe('*/*')
    })
  })

  describe('setFile', () => {
    it('sets file on input values', () => {
      const inputValues = {}
      const file = { type: 'text/plain', name: 'test.txt' }
      fileInput.setFile('myKey', file, inputValues)
      expect(inputValues.myKey).toBe(file)
    })

    it('creates preview URL for image files', () => {
      const inputValues = {}
      const file = { type: 'image/png', name: 'photo.png' }
      fileInput.setFile('img', file, inputValues)
      expect(mockCreateObjectURL).toHaveBeenCalledWith(file)
      expect(fileInput.filePreviewUrls.img).toBe('blob:mock-url')
    })

    it('does not create preview URL for non-image files', () => {
      const inputValues = {}
      const file = { type: 'text/plain', name: 'doc.txt' }
      fileInput.setFile('doc', file, inputValues)
      expect(mockCreateObjectURL).not.toHaveBeenCalled()
      expect(fileInput.filePreviewUrls.doc).toBeUndefined()
    })

    it('revokes old preview URL before creating new one', () => {
      const inputValues = {}
      fileInput.filePreviewUrls.img = 'blob:old-url'
      const file = { type: 'image/png', name: 'new.png' }
      fileInput.setFile('img', file, inputValues)
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:old-url')
    })
  })

  describe('removeFile', () => {
    it('clears file from input values', () => {
      const inputValues = { myKey: { name: 'test.txt' } }
      fileInput.removeFile('myKey', inputValues)
      expect(inputValues.myKey).toBeNull()
    })

    it('revokes preview URL if it exists', () => {
      const inputValues = { myKey: { name: 'test.png' } }
      fileInput.filePreviewUrls.myKey = 'blob:url'
      fileInput.removeFile('myKey', inputValues)
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:url')
      expect(fileInput.filePreviewUrls.myKey).toBeUndefined()
    })
  })

  describe('handleFileSelect', () => {
    it('sets file from input event', () => {
      const inputValues = {}
      const file = { type: 'text/plain', name: 'test.txt' }
      const event = { target: { files: [file] } }
      fileInput.handleFileSelect('key', event, inputValues)
      expect(inputValues.key).toBe(file)
    })

    it('does nothing when no file selected', () => {
      const inputValues = {}
      const event = { target: { files: [] } }
      fileInput.handleFileSelect('key', event, inputValues)
      expect(inputValues.key).toBeUndefined()
    })
  })

  describe('handleFileDrop', () => {
    it('sets file from drop event', () => {
      const inputValues = {}
      const file = { type: 'image/png', name: 'drop.png' }
      const event = { dataTransfer: { files: [file] } }
      fileInput.isDragging.value = 'key'
      fileInput.handleFileDrop('key', event, inputValues)
      expect(inputValues.key).toBe(file)
      expect(fileInput.isDragging.value).toBeNull()
    })
  })

  describe('cleanupPreviewUrls', () => {
    it('revokes all preview URLs', () => {
      fileInput.filePreviewUrls.a = 'blob:url-a'
      fileInput.filePreviewUrls.b = 'blob:url-b'
      fileInput.cleanupPreviewUrls()
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:url-a')
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:url-b')
    })
  })

  describe('triggerFileInput', () => {
    it('calls click on the file input ref', () => {
      const mockClick = vi.fn()
      fileInput.fileInputRefs.myKey = { click: mockClick }
      fileInput.triggerFileInput('myKey')
      expect(mockClick).toHaveBeenCalled()
    })

    it('does nothing when ref does not exist', () => {
      // Should not throw
      fileInput.triggerFileInput('nonexistent')
    })
  })
})
