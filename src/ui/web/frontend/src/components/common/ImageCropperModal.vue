<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      role="dialog"
      aria-modal="true"
      aria-labelledby="cropper-dialog-title"
      class="fixed inset-0 z-[100] flex items-center justify-center p-4"
      @keydown.esc="cancel"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/70 backdrop-blur-sm"
        @click="cancel"
      ></div>

      <!-- Modal -->
      <div class="relative w-full max-w-xl bg-white dark:bg-gray-800 rounded-2xl shadow-2xl overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 id="cropper-dialog-title" class="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Crop :size="20" class="text-purple-500" aria-hidden="true" />
            Crop Image
          </h3>
          <button
            @click="cancel"
            :aria-label="t('accessibility.closeDialog')"
            class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
          >
            <X :size="20" aria-hidden="true" />
          </button>
        </div>

        <!-- Body -->
        <div class="p-4">
          <!-- Cropper Container -->
          <div
            ref="containerRef"
            class="cropper-container relative bg-gray-900 rounded-lg overflow-hidden"
            style="height: 320px;"
          >
            <img
              v-show="!cropperReady"
              :src="imageSrc"
              class="max-w-full max-h-full opacity-50"
              @load="initCropper"
            />
            <div
              v-show="cropperReady"
              ref="cropperWrapperRef"
              class="cropper-wrapper"
            ></div>
          </div>

          <!-- Controls -->
          <div class="flex items-center justify-center gap-2 mt-4" role="toolbar" :aria-label="t('accessibility.imageEditingControls')">
            <button
              @click="rotate(-90)"
              :aria-label="t('accessibility.rotateLeft')"
              class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
            >
              <RotateCcw :size="18" aria-hidden="true" />
            </button>
            <button
              @click="rotate(90)"
              :aria-label="t('accessibility.rotateRight')"
              class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
            >
              <RotateCw :size="18" aria-hidden="true" />
            </button>
            <div class="w-px h-6 bg-gray-200 dark:bg-gray-600 mx-2" aria-hidden="true"></div>
            <button
              @click="zoom(0.1)"
              :aria-label="t('accessibility.zoomIn')"
              class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
            >
              <ZoomIn :size="18" aria-hidden="true" />
            </button>
            <button
              @click="zoom(-0.1)"
              :aria-label="t('accessibility.zoomOut')"
              class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
            >
              <ZoomOut :size="18" aria-hidden="true" />
            </button>
            <div class="w-px h-6 bg-gray-200 dark:bg-gray-600 mx-2" aria-hidden="true"></div>
            <button
              @click="reset"
              :aria-label="t('accessibility.resetImage')"
              class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-500"
            >
              <RefreshCw :size="18" aria-hidden="true" />
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex items-center justify-end gap-3 p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            @click="cancel"
            class="px-4 py-2.5 min-h-[44px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-gray-500"
          >
            Cancel
          </button>
          <button
            @click="cropImage"
            :disabled="!cropperReady"
            class="px-4 py-2.5 min-h-[44px] bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-purple-400"
          >
            <Check :size="18" aria-hidden="true" />
            Apply
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, Crop, RotateCcw, RotateCw, ZoomIn, ZoomOut, RefreshCw, Check } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  imageSrc: {
    type: String,
    default: ''
  },
  aspectRatio: {
    type: Number,
    default: 1 // Square by default for icons
  },
  outputSize: {
    type: Number,
    default: 256 // Output size in pixels
  },
  outputQuality: {
    type: Number,
    default: 0.9
  }
})

const emit = defineEmits(['update:modelValue', 'cropped'])

const containerRef = ref(null)
const cropperWrapperRef = ref(null)
const cropperReady = ref(false)

// Canvas-based cropper state
const image = ref(null)
const canvas = ref(null)
const ctx = ref(null)
const cropState = ref({
  x: 0,
  y: 0,
  scale: 1,
  rotation: 0
})
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })

async function initCropper() {
  await nextTick()

  // Create canvas element
  const canvasEl = document.createElement('canvas')
  canvasEl.width = containerRef.value?.clientWidth || 480
  canvasEl.height = 320
  canvasEl.style.cursor = 'move'
  canvas.value = canvasEl
  ctx.value = canvasEl.getContext('2d')

  // Load image
  const img = new Image()
  img.crossOrigin = 'anonymous'
  img.onload = () => {
    image.value = img

    // Calculate initial scale to fit image
    const containerWidth = canvasEl.width
    const containerHeight = canvasEl.height
    const imgRatio = img.width / img.height
    const containerRatio = containerWidth / containerHeight

    let scale
    if (imgRatio > containerRatio) {
      scale = containerWidth / img.width * 0.8
    } else {
      scale = containerHeight / img.height * 0.8
    }

    cropState.value = {
      x: containerWidth / 2,
      y: containerHeight / 2,
      scale: scale,
      rotation: 0
    }

    // Add canvas to wrapper
    if (cropperWrapperRef.value) {
      cropperWrapperRef.value.innerHTML = ''
      cropperWrapperRef.value.appendChild(canvasEl)
    }

    // Add event listeners
    canvasEl.addEventListener('mousedown', startDrag)
    canvasEl.addEventListener('mousemove', onDrag)
    canvasEl.addEventListener('mouseup', endDrag)
    canvasEl.addEventListener('mouseleave', endDrag)
    canvasEl.addEventListener('wheel', onWheel)

    // Touch events
    canvasEl.addEventListener('touchstart', startDragTouch)
    canvasEl.addEventListener('touchmove', onDragTouch)
    canvasEl.addEventListener('touchend', endDrag)

    drawCanvas()
    cropperReady.value = true
  }
  img.src = props.imageSrc
}

function drawCanvas() {
  if (!ctx.value || !image.value || !canvas.value) return

  const { x, y, scale, rotation } = cropState.value
  const c = ctx.value
  const canvasEl = canvas.value
  const img = image.value

  // Clear canvas
  c.fillStyle = '#111827'
  c.fillRect(0, 0, canvasEl.width, canvasEl.height)

  // Draw image
  c.save()
  c.translate(x, y)
  c.rotate((rotation * Math.PI) / 180)
  c.scale(scale, scale)
  c.drawImage(img, -img.width / 2, -img.height / 2)
  c.restore()

  // Draw crop overlay
  const cropSize = Math.min(canvasEl.width, canvasEl.height) * 0.7
  const cropX = (canvasEl.width - cropSize) / 2
  const cropY = (canvasEl.height - cropSize) / 2

  // Semi-transparent overlay
  c.fillStyle = 'rgba(0, 0, 0, 0.5)'
  c.fillRect(0, 0, canvasEl.width, cropY)
  c.fillRect(0, cropY + cropSize, canvasEl.width, canvasEl.height - cropY - cropSize)
  c.fillRect(0, cropY, cropX, cropSize)
  c.fillRect(cropX + cropSize, cropY, canvasEl.width - cropX - cropSize, cropSize)

  // Crop border
  c.strokeStyle = 'rgba(139, 92, 246, 0.8)'
  c.lineWidth = 2
  c.strokeRect(cropX, cropY, cropSize, cropSize)

  // Grid lines
  c.strokeStyle = 'rgba(139, 92, 246, 0.3)'
  c.lineWidth = 1
  const third = cropSize / 3
  c.beginPath()
  c.moveTo(cropX + third, cropY)
  c.lineTo(cropX + third, cropY + cropSize)
  c.moveTo(cropX + third * 2, cropY)
  c.lineTo(cropX + third * 2, cropY + cropSize)
  c.moveTo(cropX, cropY + third)
  c.lineTo(cropX + cropSize, cropY + third)
  c.moveTo(cropX, cropY + third * 2)
  c.lineTo(cropX + cropSize, cropY + third * 2)
  c.stroke()

  // Corner handles
  const handleSize = 12
  c.fillStyle = '#8b5cf6'
  // Top-left
  c.fillRect(cropX - 2, cropY - 2, handleSize, 3)
  c.fillRect(cropX - 2, cropY - 2, 3, handleSize)
  // Top-right
  c.fillRect(cropX + cropSize - handleSize + 2, cropY - 2, handleSize, 3)
  c.fillRect(cropX + cropSize - 1, cropY - 2, 3, handleSize)
  // Bottom-left
  c.fillRect(cropX - 2, cropY + cropSize - 1, handleSize, 3)
  c.fillRect(cropX - 2, cropY + cropSize - handleSize + 2, 3, handleSize)
  // Bottom-right
  c.fillRect(cropX + cropSize - handleSize + 2, cropY + cropSize - 1, handleSize, 3)
  c.fillRect(cropX + cropSize - 1, cropY + cropSize - handleSize + 2, 3, handleSize)
}

function startDrag(e) {
  isDragging.value = true
  dragStart.value = { x: e.clientX - cropState.value.x, y: e.clientY - cropState.value.y }
}

function startDragTouch(e) {
  if (e.touches.length === 1) {
    isDragging.value = true
    dragStart.value = {
      x: e.touches[0].clientX - cropState.value.x,
      y: e.touches[0].clientY - cropState.value.y
    }
  }
}

function onDrag(e) {
  if (!isDragging.value) return
  cropState.value.x = e.clientX - dragStart.value.x
  cropState.value.y = e.clientY - dragStart.value.y
  drawCanvas()
}

function onDragTouch(e) {
  if (!isDragging.value || e.touches.length !== 1) return
  e.preventDefault()
  cropState.value.x = e.touches[0].clientX - dragStart.value.x
  cropState.value.y = e.touches[0].clientY - dragStart.value.y
  drawCanvas()
}

function endDrag() {
  isDragging.value = false
}

function onWheel(e) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? -0.05 : 0.05
  zoom(delta)
}

function rotate(degree) {
  cropState.value.rotation = (cropState.value.rotation + degree) % 360
  drawCanvas()
}

function zoom(delta) {
  cropState.value.scale = Math.max(0.1, Math.min(5, cropState.value.scale + delta))
  drawCanvas()
}

function reset() {
  if (!image.value || !canvas.value) return

  const containerWidth = canvas.value.width
  const containerHeight = canvas.value.height
  const imgRatio = image.value.width / image.value.height
  const containerRatio = containerWidth / containerHeight

  let scale
  if (imgRatio > containerRatio) {
    scale = containerWidth / image.value.width * 0.8
  } else {
    scale = containerHeight / image.value.height * 0.8
  }

  cropState.value = {
    x: containerWidth / 2,
    y: containerHeight / 2,
    scale: scale,
    rotation: 0
  }
  drawCanvas()
}

function cropImage() {
  if (!image.value || !canvas.value) {
    return
  }

  const canvasEl = canvas.value
  const img = image.value
  const { x, y, scale, rotation } = cropState.value

  const cropSize = Math.min(canvasEl.width, canvasEl.height) * 0.7
  const cropX = (canvasEl.width - cropSize) / 2
  const cropY = (canvasEl.height - cropSize) / 2

  // Step 1: Draw the transformed image to a temp canvas (full preview size)
  const tempCanvas = document.createElement('canvas')
  tempCanvas.width = canvasEl.width
  tempCanvas.height = canvasEl.height
  const tempCtx = tempCanvas.getContext('2d')

  // Draw image with transformations
  tempCtx.save()
  tempCtx.translate(x, y)
  tempCtx.rotate((rotation * Math.PI) / 180)
  tempCtx.scale(scale, scale)
  tempCtx.drawImage(img, -img.width / 2, -img.height / 2)
  tempCtx.restore()

  // Step 2: Extract only the crop region to output canvas
  const outputCanvas = document.createElement('canvas')
  outputCanvas.width = props.outputSize
  outputCanvas.height = props.outputSize
  const outputCtx = outputCanvas.getContext('2d')

  // Fill with white background (no transparency)
  outputCtx.fillStyle = '#FFFFFF'
  outputCtx.fillRect(0, 0, props.outputSize, props.outputSize)

  // Draw the cropped region scaled to output size
  outputCtx.drawImage(
    tempCanvas,
    cropX, cropY, cropSize, cropSize,  // Source: crop region from temp canvas
    0, 0, props.outputSize, props.outputSize  // Dest: full output canvas
  )

  const dataUrl = outputCanvas.toDataURL('image/png', props.outputQuality)
  emit('cropped', dataUrl)
  close()
}

function cancel() {
  close()
}

function close() {
  // Clean up event listeners
  if (canvas.value) {
    canvas.value.removeEventListener('mousedown', startDrag)
    canvas.value.removeEventListener('mousemove', onDrag)
    canvas.value.removeEventListener('mouseup', endDrag)
    canvas.value.removeEventListener('mouseleave', endDrag)
    canvas.value.removeEventListener('wheel', onWheel)
    canvas.value.removeEventListener('touchstart', startDragTouch)
    canvas.value.removeEventListener('touchmove', onDragTouch)
    canvas.value.removeEventListener('touchend', endDrag)
  }

  canvas.value = null
  ctx.value = null
  image.value = null
  cropperReady.value = false
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (val) => {
  if (!val) {
    close()
  }
})

onBeforeUnmount(() => {
  close()
})
</script>

<style scoped>
.cropper-container {
  display: flex;
  align-items: center;
  justify-content: center;
}

.cropper-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cropper-wrapper canvas {
  max-width: 100%;
  max-height: 100%;
}
</style>
