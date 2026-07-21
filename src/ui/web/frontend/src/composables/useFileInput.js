/**
 * File Input Composable
 * Handles file upload, preview, and cleanup for form inputs
 */

import { ref, reactive, onUnmounted } from 'vue'
import { formatFileSize } from '@/utils/format'

/**
 * Create file input handling composable
 * @returns {Object} File input methods and state
 */
export function useFileInput() {
  // Track file preview URLs for cleanup
  const filePreviewUrls = reactive({})
  const fileInputRefs = reactive({})
  const isDragging = ref(null)

  /**
   * Check if file is an image
   */
  function isImageFile(file) {
    if (!file) return false
    return file.type?.startsWith('image/')
  }

  /**
   * Check if field type is a file type
   */
  function isFileType(type) {
    return type === 'file' || type === 'image'
  }

  // formatFileSize imported from @/utils/format

  /**
   * Get accepted MIME types for file input
   */
  function getAcceptTypes(def) {
    if (def.accept) return def.accept
    if (def.type === 'image') return 'image/*'
    return '*/*'
  }

  /**
   * Trigger file input click
   */
  function triggerFileInput(key) {
    fileInputRefs[key]?.click()
  }

  /**
   * Handle file selection from input
   */
  function handleFileSelect(key, event, inputValues) {
    const file = event.target.files?.[0]
    if (file) {
      setFile(key, file, inputValues)
    }
  }

  /**
   * Handle file drop
   */
  function handleFileDrop(key, event, inputValues) {
    isDragging.value = null
    const file = event.dataTransfer.files?.[0]
    if (file) {
      setFile(key, file, inputValues)
    }
  }

  /**
   * Set file value and create preview URL if image
   */
  function setFile(key, file, inputValues) {
    inputValues[key] = file

    if (isImageFile(file)) {
      // Cleanup old preview URL
      if (filePreviewUrls[key]) {
        URL.revokeObjectURL(filePreviewUrls[key])
      }
      filePreviewUrls[key] = URL.createObjectURL(file)
    }
  }

  /**
   * Remove file and cleanup preview URL
   */
  function removeFile(key, inputValues) {
    inputValues[key] = null
    if (filePreviewUrls[key]) {
      URL.revokeObjectURL(filePreviewUrls[key])
      delete filePreviewUrls[key]
    }
  }

  /**
   * Cleanup all preview URLs
   */
  function cleanupPreviewUrls() {
    for (const url of Object.values(filePreviewUrls)) {
      URL.revokeObjectURL(url)
    }
  }

  // Cleanup on unmount
  onUnmounted(() => {
    cleanupPreviewUrls()
  })

  return {
    // State
    filePreviewUrls,
    fileInputRefs,
    isDragging,
    // Methods
    isImageFile,
    isFileType,
    formatFileSize,
    getAcceptTypes,
    triggerFileInput,
    handleFileSelect,
    handleFileDrop,
    setFile,
    removeFile,
    cleanupPreviewUrls
  }
}
