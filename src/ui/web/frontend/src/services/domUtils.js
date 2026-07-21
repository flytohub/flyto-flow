/**
 * DOM Utilities Service
 *
 * Centralizes all direct DOM operations to:
 * - Reduce code duplication
 * - Provide consistent behavior
 * - Enable easier testing (can be mocked)
 * - Isolate side effects
 */

/**
 * Download content as a file via anchor click
 * @param {string} url - URL or data URL to download
 * @param {string} filename - Filename for the download
 */
export function downloadViaAnchor(url, filename) {
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * Download a Blob as a file
 * @param {Blob} blob - Blob to download
 * @param {string} filename - Filename for the download
 */
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)
  downloadViaAnchor(url, filename)
  // Cleanup after a short delay to ensure download starts
  setTimeout(() => {
    if (typeof URL.revokeObjectURL === 'function') {
      URL.revokeObjectURL(url)
    }
  }, 100)
}

/**
 * Download text content as a file
 * @param {string} content - Text content to download
 * @param {string} filename - Filename for the download
 * @param {string} mimeType - MIME type (default: text/plain)
 */
export function downloadText(content, filename, mimeType = 'text/plain') {
  const blob = new Blob([content], { type: mimeType })
  downloadBlob(blob, filename)
}

/**
 * Download JSON content as a file
 * @param {any} data - Data to serialize and download
 * @param {string} filename - Filename for the download
 */
export function downloadJson(data, filename = 'data.json') {
  const content = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  downloadText(content, filename, 'application/json')
}

/**
 * Download base64 data as a file
 * @param {string} base64Data - Base64 encoded data
 * @param {string} filename - Filename for the download
 * @param {string} mimeType - MIME type (default: application/octet-stream)
 */
export function downloadBase64(base64Data, filename, mimeType = 'application/octet-stream') {
  const dataUrl = `data:${mimeType};base64,${base64Data}`
  downloadViaAnchor(dataUrl, filename)
}

/**
 * Download an image from URL or base64
 * @param {string} source - Image URL or base64 data
 * @param {string} filename - Filename for the download
 * @param {boolean} isBase64 - Whether source is base64 data
 */
export function downloadImage(source, filename = 'image.png', isBase64 = false) {
  if (isBase64) {
    downloadBase64(source, filename, 'image/png')
  } else {
    downloadViaAnchor(source, filename)
  }
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
export async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    textArea.style.cssText = 'position: fixed; left: -9999px; top: -9999px;'
    document.body.appendChild(textArea)
    textArea.select()
    try {
      document.execCommand('copy')
      return true
    } catch {
      return false
    } finally {
      document.body.removeChild(textArea)
    }
  }
}

/**
 * Open URL in new tab
 * @param {string} url - URL to open
 */
export function openInNewTab(url) {
  window.open(url, '_blank', 'noopener,noreferrer')
}

/**
 * Create a canvas element
 * @param {number} width - Canvas width
 * @param {number} height - Canvas height
 * @param {Object} style - Optional CSS style object
 * @returns {HTMLCanvasElement}
 */
export function createCanvas(width, height, style = {}) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height

  const defaultStyle = {
    position: 'absolute',
    inset: '0',
    width: '100%',
    height: '100%',
    ...style
  }

  Object.assign(canvas.style, defaultStyle)
  return canvas
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
export function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

/**
 * Trigger file input click for uploads
 * @param {Object} options - Options
 * @param {string} options.accept - Accepted file types
 * @param {boolean} options.multiple - Allow multiple files
 * @returns {Promise<FileList|null>} Selected files
 */
export function triggerFileInput({ accept = '*', multiple = false } = {}) {
  return new Promise((resolve) => {
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = accept
    input.multiple = multiple
    input.style.display = 'none'

    input.onchange = () => {
      resolve(input.files)
      document.body.removeChild(input)
    }

    input.oncancel = () => {
      resolve(null)
      document.body.removeChild(input)
    }

    document.body.appendChild(input)
    input.click()
  })
}

export default {
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
}
