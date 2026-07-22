<template>
  <div
    v-if="isOpen"
    class="fixed inset-0 z-[1200] flex items-center justify-center bg-black/50"
    @click.self="$emit('close')"
  >
    <div class="w-full max-w-lg bg-gray-800 rounded-xl shadow-2xl overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-gray-700 bg-purple-900/20">
        <div class="flex items-center gap-3">
          <div class="p-2 bg-purple-600/20 rounded-lg">
            <Hand :size="24" class="text-purple-400" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-white">{{ breakpoint?.title || 'Approval Required' }}</h3>
            <p class="text-sm text-gray-400">{{ $t('breakpoint.waitingApproval') }}</p>
          </div>
        </div>
        <button
          @click="$emit('close')"
          class="p-1 text-gray-400 hover:text-white transition-colors"
          aria-label="Close"
        >
          <X :size="20" />
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-12">
        <Loader :size="32" class="text-purple-400 animate-spin" />
      </div>

      <!-- Content -->
      <div v-else-if="breakpoint" class="p-6">
        <!-- Description -->
        <div v-if="breakpoint.description" class="mb-6">
          <p class="text-gray-300 whitespace-pre-wrap">{{ breakpoint.description }}</p>
        </div>

        <!-- Info Grid -->
        <div class="grid grid-cols-2 gap-4 mb-6 text-sm">
          <div class="bg-gray-900/50 rounded-lg p-3">
            <p class="text-gray-500 text-xs mb-1">{{ $t('breakpoint.workflow') }}</p>
            <p class="text-white font-medium">{{ breakpoint.workflowId || 'Unknown' }}</p>
          </div>
          <div class="bg-gray-900/50 rounded-lg p-3">
            <p class="text-gray-500 text-xs mb-1">{{ $t('breakpoint.step') }}</p>
            <p class="text-white font-medium">{{ breakpoint.stepId }}</p>
          </div>
          <div class="bg-gray-900/50 rounded-lg p-3">
            <p class="text-gray-500 text-xs mb-1">{{ $t('breakpoint.createdAt') }}</p>
            <p class="text-white font-medium">{{ formatTime(breakpoint.createdAt) }}</p>
          </div>
          <div class="bg-gray-900/50 rounded-lg p-3">
            <p class="text-gray-500 text-xs mb-1">{{ $t('breakpoint.expires') }}</p>
            <p class="text-white font-medium" :class="{ 'text-yellow-400': isExpiringSoon }">
              {{ breakpoint.expiresAt ? formatTimeRemaining(breakpoint.expiresAt) : 'Never' }}
            </p>
          </div>
        </div>

        <!-- Context Preview -->
        <div v-if="breakpoint.contextSnapshot && Object.keys(breakpoint.contextSnapshot).length" class="mb-6">
          <button
            @click="contextExpanded = !contextExpanded"
            class="flex items-center justify-between w-full text-left mb-2"
          >
            <span class="text-sm font-medium text-gray-300 flex items-center gap-2">
              <Database :size="14" />
              {{ $t('breakpoint.contextSnapshot') }}
            </span>
            <ChevronDown
              :size="16"
              class="text-gray-500 transition-transform"
              :class="{ 'rotate-180': contextExpanded }"
            />
          </button>
          <div v-if="contextExpanded" class="bg-gray-900 rounded-lg p-3 max-h-48 overflow-auto">
            <pre class="text-xs text-gray-300">{{ JSON.stringify(breakpoint.contextSnapshot, null, 2) }}</pre>
          </div>
        </div>

        <!-- Custom Input Fields -->
        <div v-if="breakpoint.customFields?.length" class="mb-6 space-y-4">
          <h4 class="text-sm font-medium text-gray-300 flex items-center gap-2">
            <Edit3 :size="14" />
            {{ $t('breakpoint.additionalInput') }}
          </h4>
          <div v-for="field in breakpoint.customFields" :key="field.name" class="space-y-1">
            <label class="text-sm text-gray-400">
              {{ field.label || field.name }}
              <span v-if="field.required" class="text-red-400">*</span>
            </label>
            <input
              v-if="field.type === 'string' || field.type === 'number'"
              v-model="customInputs[field.name]"
              :type="field.type === 'number' ? 'number' : 'text'"
              :placeholder="field.label || field.name"
              class="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:border-purple-500 focus:outline-none"
            />
            <AppTextarea
              v-else-if="field.type === 'text'"
              v-model="customInputs[field.name]"
              :placeholder="field.label || field.name"
              :rows="3"
            />
            <label v-else-if="field.type === 'boolean'" class="flex items-center gap-2 cursor-pointer">
              <input
                v-model="customInputs[field.name]"
                type="checkbox"
                class="w-4 h-4 rounded border-gray-600 text-purple-600 focus:ring-purple-500"
              />
              <span class="text-sm text-gray-300">{{ field.label || field.name }}</span>
            </label>
          </div>
        </div>

        <!-- Comment -->
        <div class="mb-6">
          <label class="text-sm text-gray-400 mb-1 block">
            {{ $t('breakpoint.comment') }}
          </label>
          <AppTextarea
            v-model="comment"
            :placeholder="$t('breakpoint.commentPlaceholder')"
            :rows="2"
          />
        </div>

        <!-- Actions -->
        <div class="flex gap-3">
          <button
            @click="handleReject"
            :disabled="submitting"
            class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-red-600/20 hover:bg-red-600/30 border border-red-600/50 text-red-400 rounded-lg transition-colors disabled:opacity-50"
            aria-label="Reject"
          >
            <XCircle :size="18" />
            {{ $t('breakpoint.reject') }}
          </button>
          <button
            @click="handleApprove"
            :disabled="submitting || !canApprove"
            class="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors disabled:opacity-50"
            aria-label="Approve"
          >
            <CheckCircle :size="18" />
            {{ $t('breakpoint.approve') }}
          </button>
        </div>

        <!-- Validation Error -->
        <p v-if="validationError" class="mt-3 text-sm text-red-400 text-center">
          {{ validationError }}
        </p>
      </div>

      <!-- Empty State -->
      <div v-else class="flex flex-col items-center justify-center py-12 text-gray-400">
        <Hand :size="48" class="mb-3 opacity-50" />
        <p>{{ $t('breakpoint.noBreakpoint') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Hand,
  X,
  Loader,
  CheckCircle,
  XCircle,
  ChevronDown,
  Database,
  Edit3
} from 'lucide-vue-next'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  breakpoint: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'approve', 'reject'])
const { t } = useI18n()

const contextExpanded = ref(false)
const comment = ref('')
const customInputs = ref({})
const submitting = ref(false)
const validationError = ref('')

// Reset form when breakpoint changes
watch(() => props.breakpoint, (newBreakpoint) => {
  comment.value = ''
  validationError.value = ''
  customInputs.value = {}

  // Initialize custom inputs with defaults
  if (newBreakpoint?.customFields) {
    for (const field of newBreakpoint.customFields) {
      customInputs.value[field.name] = field.default ?? (field.type === 'boolean' ? false : '')
    }
  }
}, { immediate: true })

const isExpiringSoon = computed(() => {
  if (!props.breakpoint?.expiresAt) return false
  const remaining = new Date(props.breakpoint.expiresAt) - new Date()
  return remaining < 5 * 60 * 1000 // Less than 5 minutes
})

const canApprove = computed(() => {
  if (!props.breakpoint?.customFields) return true

  for (const field of props.breakpoint.customFields) {
    if (field.required && !customInputs.value[field.name]) {
      return false
    }
  }
  return true
})

function formatTime(timestamp) {
  if (!timestamp) return '-'
  return new Date(timestamp).toLocaleString()
}

function formatTimeRemaining(expiresAt) {
  const remaining = new Date(expiresAt) - new Date()
  if (remaining <= 0) return 'Expired'

  const minutes = Math.floor(remaining / 60000)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    return `${hours}h ${minutes % 60}m`
  }
  return `${minutes}m`
}

function validateInputs() {
  if (!props.breakpoint?.customFields) return true

  for (const field of props.breakpoint.customFields) {
    if (field.required && !customInputs.value[field.name]) {
      validationError.value = `${field.label || field.name} is required`
      return false
    }
  }
  validationError.value = ''
  return true
}

async function handleApprove() {
  if (!validateInputs()) return

  submitting.value = true
  try {
    await emit('approve', {
      breakpointId: props.breakpoint.breakpointId,
      comment: comment.value,
      customInputs: customInputs.value
    })
  } finally {
    submitting.value = false
  }
}

async function handleReject() {
  submitting.value = true
  try {
    await emit('reject', {
      breakpointId: props.breakpoint.breakpointId,
      comment: comment.value
    })
  } finally {
    submitting.value = false
  }
}
</script>
