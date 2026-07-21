/**
 * Storage API
 * File upload and management
 */

import { upload, del } from './client'

/**
 * Upload an image file
 * @param {File|Blob} file - The file to upload
 * @param {string} purpose - Optional purpose (e.g., 'template_icon')
 * @returns {Promise<{url: string, file_id: string}>}
 */
export async function uploadImage(file, purpose = 'template_icon') {
  const formData = new FormData()
  formData.append('file', file)
  if (purpose) {
    formData.append('purpose', purpose)
  }

  const result = await upload('/storage/upload', formData)
  return result
}

/**
 * Convert a data URL to a Blob
 * @param {string} dataUrl - The data URL
 * @returns {Blob}
 */
function dataUrlToBlob(dataUrl) {
  const arr = dataUrl.split(',')
  const mime = arr[0].match(/:(.*?);/)[1]
  const bstr = atob(arr[1])
  let n = bstr.length
  const u8arr = new Uint8Array(n)
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n)
  }
  return new Blob([u8arr], { type: mime })
}

/**
 * Upload an image from a data URL
 * @param {string} dataUrl - The data URL
 * @param {string} filename - The filename
 * @param {string} purpose - Optional purpose
 * @returns {Promise<{url: string, file_id: string}>}
 */
export async function uploadImageFromDataUrl(dataUrl, filename = 'image.png', purpose = 'template_icon') {
  const blob = dataUrlToBlob(dataUrl)
  const file = new File([blob], filename, { type: blob.type })
  return uploadImage(file, purpose)
}

/**
 * Delete a file from storage
 * @param {string} fileId - The file ID to delete
 * @returns {Promise<{ok: boolean}>}
 */
export async function deleteFile(fileId) {
  try {
    await del(`/storage/${fileId}`)
    return { ok: true }
  } catch (err) {
    return { ok: false, error: err.message }
  }
}

/**
 * Extract file ID from Firebase Storage URL
 * URL format: https://storage.googleapis.com/bucket/uploads/userId/purpose/fileId.ext
 * @param {string} url - The storage URL
 * @returns {string|null} The file ID or null if not a storage URL
 */
export function extractFileIdFromUrl(url) {
  if (!url || typeof url !== 'string') return null
  // Skip base64 data URLs
  if (url.startsWith('data:')) return null
  // Match Firebase Storage URL pattern
  const match = url.match(/\/([a-f0-9-]+)\.[^/]+$/)
  return match ? match[1] : null
}

export const storageAPI = {
  uploadImage,
  uploadImageFromDataUrl,
  deleteFile,
  extractFileIdFromUrl
}

export default storageAPI
