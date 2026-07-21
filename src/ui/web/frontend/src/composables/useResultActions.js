/**
 * Result Actions Composable
 * Handles download, copy, and export actions for execution results
 */
import {
  downloadViaAnchor,
  downloadText,
  downloadJson,
  downloadImage,
  copyToClipboard,
  openInNewTab
} from '@/services/domUtils'

/**
 * Create result actions composable
 * @param {Object} options
 * @param {Function} options.getResult - Function to get current result
 * @returns {Object} Result action methods
 */
export function useResultActions(options = {}) {
  const { getResult } = options

  /**
   * Download result as file or open URL
   */
  function downloadResult(result = getResult?.()) {
    if (!result) return

    if (result.downloadUrl || result.download_url || result.fileUrl || result.file_url) {
      openInNewTab(result.downloadUrl || result.download_url || result.fileUrl || result.file_url)
    } else if (result.imageBase64 || result.image_base64) {
      downloadImage(result.imageBase64 || result.image_base64, 'result.png', true)
    } else if (result.imageUrl || result.image_url || result.image) {
      downloadViaAnchor(result.imageUrl || result.image_url || result.image, 'result.png')
    }
  }

  /**
   * Copy result to clipboard as text
   */
  async function copyResult(result = getResult?.()) {
    if (!result) return false

    const text = typeof result === 'string' ? result : JSON.stringify(result, null, 2)
    return copyToClipboard(text)
  }

  /**
   * Copy image URL or base64 to clipboard
   */
  async function copyImageToClipboard(result = getResult?.()) {
    if (!result) return false

    if (result.imageBase64 || result.image_base64) {
      return copyToClipboard(`data:image/png;base64,${result.imageBase64 || result.image_base64}`)
    } else if (result.imageUrl || result.image_url || result.image) {
      return copyToClipboard(result.imageUrl || result.image_url || result.image)
    }
    return false
  }

  /**
   * Download result as text file
   */
  function downloadAsFile(result = getResult?.(), filename = 'result.txt') {
    if (!result) return

    const text = typeof result === 'string' ? result : JSON.stringify(result, null, 2)
    downloadText(text, filename)
  }

  /**
   * Download as JSON file
   */
  function downloadAsJson(result = getResult?.(), filename = 'result.json') {
    if (!result) return

    downloadJson(result, filename)
  }

  return {
    downloadResult,
    copyResult,
    copyImageToClipboard,
    downloadAsFile,
    downloadAsJson
  }
}
