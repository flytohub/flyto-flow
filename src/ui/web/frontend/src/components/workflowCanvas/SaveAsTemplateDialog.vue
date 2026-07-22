<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      role="dialog"
      aria-modal="true"
      aria-labelledby="save-template-title"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      @keydown.esc="close"
    >
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-black/50 backdrop-blur-sm"
        @click="close"
      />

      <!-- Modal -->
      <div ref="modalRef" tabindex="-1" class="relative w-full max-w-lg bg-white dark:bg-gray-800 rounded-2xl shadow-2xl">
        <!-- Header -->
        <div class="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div>
            <h2 id="save-template-title" class="text-xl font-bold text-gray-900 dark:text-white">
              {{ $t('workflow.saveAsTemplate', 'Save as Template') }}
            </h2>
            <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {{ $t('workflow.saveAsTemplateDesc', 'Share this node configuration as a reusable template') }}
            </p>
          </div>
          <button
            @click="close"
            aria-label="Close"
            class="p-2.5 min-w-[44px] min-h-[44px] flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- Body -->
        <form @submit.prevent="submit" class="p-6 space-y-5">
          <!-- Module info preview -->
          <div class="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-xl">
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center text-white"
              :style="{ background: moduleGradient }"
            >
              <component :is="moduleIcon" :size="20" />
            </div>
            <div>
              <div class="font-medium text-gray-900 dark:text-white text-sm">{{ moduleLabel }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-400">{{ moduleId }}</div>
            </div>
          </div>

          <!-- Name -->
          <div>
            <label for="tpl-name" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('createModal.name.label', 'Template Name') }}
              <span class="text-red-500">*</span>
            </label>
            <AppInput
              id="tpl-name"
              v-model="form.name"
              :placeholder="$t('createModal.name.placeholder', 'My API Connector')"
              required
              autofocus
            />
          </div>

          <!-- Description -->
          <div>
            <label for="tpl-desc" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              {{ $t('createModal.description.label', 'Description') }}
            </label>
            <AppTextarea
              v-model="form.description"
              :rows="2"
              :placeholder="$t('createModal.description.placeholder', 'What does this template do?')"
            />
          </div>

          <!-- Error Message -->
          <div
            v-if="errorMessage"
            role="alert"
            class="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-sm text-red-600 dark:text-red-400"
          >
            {{ errorMessage }}
          </div>

          <!-- Actions -->
          <div class="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              @click="close"
              class="px-5 py-2.5 min-h-[44px] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 font-medium rounded-lg transition-colors"
            >
              {{ $t('common.cancel', 'Cancel') }}
            </button>
            <button
              type="submit"
              :disabled="!form.name.trim() || isSubmitting"
              class="px-5 py-2.5 min-h-[44px] bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <Loader2 v-if="isSubmitting" :size="18" class="animate-spin" />
              <BookTemplate v-else :size="18" />
              <span>{{ isSubmitting ? $t('createModal.creating', 'Creating...') : $t('workflow.saveAsTemplate', 'Save as Template') }}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { X, Loader2, BookTemplate } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'
import { templatesAPI } from '@/api/templates'
import { useNodeStyles } from '@/composables/useNodeStyles'
import { useToast } from '@/composables/useToast'

const { t } = useI18n()
const toast = useToast()
const { getGradient, getNodeIcon, getNodeLabel } = useNodeStyles()

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  node: { type: Object, default: null }
})

const emit = defineEmits(['update:modelValue', 'created'])

const form = reactive({
  name: '',
  description: '',
  category: 'connector'
})

const isSubmitting = ref(false)
const errorMessage = ref('')

// Derive module info from node
const moduleId = computed(() => {
  if (!props.node?.data) return ''
  const mod = props.node.data.module
  return typeof mod === 'string' ? mod : (mod?.moduleId || mod?.id || '')
})

const moduleLabel = computed(() => {
  if (!moduleId.value) return ''
  return getNodeLabel(moduleId.value) || moduleId.value.split('.').pop()
})

const moduleGradient = computed(() => getGradient(moduleId.value))
const moduleIcon = computed(() => getNodeIcon(moduleId.value))

// Pre-fill form when node changes
watch(() => props.node, (node) => {
  if (!node) return
  const label = moduleLabel.value
  form.name = label ? `${label} Connector` : ''
  form.description = ''

  // Auto-select connector category if module is http.request
  if (moduleId.value === 'http.request') {
    form.category = 'connector'
  } else {
    form.category = ''
  }
})

function close() {
  emit('update:modelValue', false)
  errorMessage.value = ''
}

/**
 * Build UI sections from node params for params_schema generation.
 * Each param becomes a form input in a single section.
 */
function buildUiFromParams(params) {
  if (!params || typeof params !== 'object') return { sections: [] }

  const components = []
  for (const [key, value] of Object.entries(params)) {
    // Skip internal/hidden params
    if (key.startsWith('_')) continue

    const compType = guessComponentType(key, value)
    components.push({
      id: key,
      type: compType,
      label: formatLabel(key),
      params: {
        variableName: key,
        label: formatLabel(key),
        default: value,
        required: isLikelyRequired(key)
      }
    })
  }

  if (components.length === 0) return { sections: [] }

  return {
    sections: [{
      id: 'params',
      label: 'Parameters',
      columnsData: [{
        id: 'col-1',
        components
      }]
    }]
  }
}

function guessComponentType(key, value) {
  if (typeof value === 'boolean') return 'checkbox'
  if (typeof value === 'number') return 'number'
  const k = key.toLowerCase()
  if (k.includes('password') || k.includes('secret') || k.includes('api_key') || k.includes('token')) return 'password'
  if (k.includes('url') || k.includes('endpoint')) return 'text'
  if (k.includes('body') || k.includes('content') || k.includes('message')) return 'textarea'
  if (typeof value === 'string' && value.length > 100) return 'textarea'
  return 'text'
}

function formatLabel(key) {
  return key
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^\w/, c => c.toUpperCase())
    .trim()
}

function isLikelyRequired(key) {
  const k = key.toLowerCase()
  return k === 'url' || k === 'method' || k === 'endpoint'
}

async function submit() {
  if (!form.name.trim() || isSubmitting.value) return

  isSubmitting.value = true
  errorMessage.value = ''

  try {
    const nodeData = props.node?.data || {}
    const params = nodeData.params || {}

    // Build a single step from the node
    const step = {
      id: 'step-1',
      module: moduleId.value,
      params: { ...params }
    }

    // Build UI sections from params for params_schema generation
    const ui = buildUiFromParams(params)

    const payload = {
      name: form.name.trim(),
      templateName: form.name.trim(),
      description: form.description.trim() || undefined,
      templateDescription: form.description.trim() || undefined,
      category: form.category || 'connector',
      steps: [step],
      ui
    }

    const result = await templatesAPI.createTemplate(payload)

    if (!result.ok) {
      throw new Error(result.error || t('createModal.errors.createFailed', 'Failed to create template'))
    }

    toast.success(t('workflow.templateCreated', 'Template created successfully'))
    close()
    emit('created', result.template?.id)
  } catch (err) {
    errorMessage.value = err.message || t('createModal.errors.createFailed', 'Failed to create template')
  } finally {
    isSubmitting.value = false
  }
}
</script>
