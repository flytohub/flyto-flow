/**
 * Avatar Handlers
 *
 * S-Grade: Avatar upload and management functions.
 * Single responsibility: Avatar file handling.
 */

import i18n from '@/i18n'
import { uploadImageFromDataUrl } from '@/api/storage'

/**
 * Handle file selection for avatar upload
 * @param {Object} state - Profile state object
 * @param {File} file - The file to handle
 * @param {number} maxSizeMB - Maximum file size in MB
 * @param {Function} onError - Error callback
 * @returns {boolean} Success status
 */
export function handleFileSelect(state, file, maxSizeMB = 5, onError) {
  const { cropperImageSrc, showCropper } = state

  if (!file) return false

  // Validate file type
  if (!file.type.startsWith('image/')) {
    onError?.(new Error(i18n.global.t('error.invalidFileType')))
    return false
  }

  // Validate file size
  if (file.size > maxSizeMB * 1024 * 1024) {
    onError?.(new Error(i18n.global.t('error.fileTooLarge')))
    return false
  }

  // Read file and set for cropper
  const reader = new FileReader()
  reader.onload = (e) => {
    cropperImageSrc.value = e.target.result
    showCropper.value = true
  }
  reader.readAsDataURL(file)

  return true
}

/**
 * Handle cropped image - upload to storage
 * @param {Object} state - Profile state object
 * @param {string} dataUrl - Cropped image data URL
 * @param {Function} onError - Error callback
 * @returns {Promise<void>}
 */
export async function handleCropped(state, dataUrl, onError) {
  const { form, oldAvatarUrl, uploadingAvatar } = state

  uploadingAvatar.value = true
  try {
    // Save old avatar URL for deletion after save
    if (form.avatarUrl && !oldAvatarUrl.value) {
      oldAvatarUrl.value = form.avatarUrl
    }

    // Upload new avatar to storage
    const result = await uploadImageFromDataUrl(dataUrl, 'avatar.png', 'avatar')
    if (result.url) {
      form.avatarUrl = result.url
    } else {
      throw new Error('Upload failed - no URL returned')
    }
  } catch (err) {
    onError?.(err)
    // Fallback to data URL if upload fails
    form.avatarUrl = dataUrl
  } finally {
    uploadingAvatar.value = false
  }
}

/**
 * Remove avatar - deletion happens on save
 * @param {Object} state - Profile state object
 */
export function removeAvatar(state) {
  const { form, oldAvatarUrl } = state

  // Save old URL for deletion on save
  if (form.avatarUrl && !oldAvatarUrl.value) {
    oldAvatarUrl.value = form.avatarUrl
  }
  form.avatarUrl = ''
}
