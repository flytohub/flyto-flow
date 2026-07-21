<template>
  <button
    @click="$emit('select', module)"
    class="group relative flex items-start gap-4 p-4 rounded-xl text-left overflow-hidden transition-all duration-300 hover:scale-[1.02] module-card"
    :class="{ 'expert-card': isExpert }"
    :title="localizedDescription"
  >
    <!-- Background -->
    <div class="absolute inset-0 bg-white/5 border border-white/10 rounded-xl transition-all duration-300 group-hover:bg-white/10 group-hover:border-white/20"></div>

    <!-- Glow effect on hover -->
    <div
      class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"
      :style="{ background: `radial-gradient(circle at 50% 50%, ${moduleColor}20, transparent 70%)` }"
    ></div>

    <!-- Left accent line -->
    <div
      class="absolute left-0 top-2 bottom-2 w-0.5 rounded-full opacity-0 group-hover:opacity-100 transition-all duration-300"
      :style="{ backgroundColor: moduleColor }"
    ></div>

    <!-- Icon -->
    <div class="relative flex-shrink-0">
      <div
        class="icon-container w-11 h-11 rounded-xl flex items-center justify-center transition-all duration-300 group-hover:scale-110 overflow-hidden"
        :style="{
          backgroundColor: isIconUrl(resolvedIcon) ? 'transparent' : (moduleColor) + '20',
          boxShadow: isIconUrl(resolvedIcon) ? 'none' : `0 0 0 1px ${moduleColor}30`,
          '--icon-color': (moduleColor) + '40'
        }"
      >
        <!-- URL icon (uploaded image or iconify) -->
        <img
          v-if="isIconUrl(resolvedIcon)"
          :src="resolvedIcon.url"
          class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          :alt="localizedLabel"
        />
        <!-- Lucide component icon -->
        <component
          v-else
          :is="resolvedIcon"
          :size="20"
          :style="{ color: moduleColor }"
          class="transition-transform duration-300 group-hover:scale-110"
        />
      </div>
    </div>

    <!-- Content -->
    <div class="relative flex-1 min-w-0">
      <div class="flex items-center gap-2 mb-1.5">
        <span class="font-medium text-sm text-white group-hover:text-white transition-colors truncate">
          {{ localizedLabel }}
        </span>
        <!-- Expert badge -->
        <span
          v-if="isExpert"
          class="px-1.5 py-0.5 text-[10px] font-medium rounded bg-amber-500/20 text-amber-400 border border-amber-500/30"
        >
          PRO
        </span>
        <!-- Category tag -->
        <span
          v-else-if="module.tags && module.tags.length > 0"
          class="px-1.5 py-0.5 text-[10px] font-medium rounded"
          :style="{
            backgroundColor: moduleColor + '20',
            color: moduleColor,
            border: `1px solid ${moduleColor}30`
          }"
        >
          {{ module.tags[0] }}
        </span>
      </div>

      <p class="text-xs text-gray-400 line-clamp-2 leading-relaxed group-hover:text-gray-300 transition-colors">
        {{ localizedDescription || $t('moduleCard.noDescription') }}
      </p>

      <!-- Input/Output Type Badges -->
      <div v-if="hasIOTypes" class="mt-2.5 flex flex-wrap items-center gap-1.5">
        <div
          v-for="inputType in displayInputTypes"
          :key="'in-' + inputType"
          class="io-badge input-badge"
          :title="getInputTypeDescription(inputType)"
        >
          <ArrowDownToLine :size="10" />
          <span>{{ getInputTypeLabel(inputType) }}</span>
        </div>
        <ArrowRight
          v-if="displayInputTypes.length > 0 && displayOutputTypes.length > 0"
          :size="10"
          class="text-gray-600 mx-0.5"
        />
        <div
          v-for="outputType in displayOutputTypes"
          :key="'out-' + outputType"
          class="io-badge output-badge"
          :title="getOutputTypeDescription(outputType)"
        >
          <ArrowUpFromLine :size="10" />
          <span>{{ getOutputTypeLabel(outputType) }}</span>
        </div>
      </div>
    </div>

    <!-- Arrow indicator -->
    <div class="relative flex-shrink-0 self-center opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
      <ArrowRight :size="16" class="text-gray-500" />
    </div>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowRight, ArrowDownToLine, ArrowUpFromLine } from 'lucide-vue-next'
import { useModuleIcons } from '@/composables/useModuleIcons'

const { t, te } = useI18n()
const { getModuleIcon, isIconUrl } = useModuleIcons()

const props = defineProps({
  module: {
    type: Object,
    required: true
  },
  isExpert: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

const localizedLabel = computed(() => {
  const labelKey = props.module.labelKey
  if (labelKey && te(labelKey)) {
    return t(labelKey)
  }
  return props.module.label || props.module.moduleId
})

// Use custom color if set, otherwise default
const moduleColor = computed(() => {
  return props.module.customColor || props.module.color || '#6B7280'
})

// Resolve icon - convert string name to Lucide component or URL object
const resolvedIcon = computed(() => getModuleIcon(props.module))


const localizedDescription = computed(() => {
  const descKey = props.module.descriptionKey
  if (descKey && te(descKey)) {
    return t(descKey)
  }
  return props.module.description || ''
})

const hasIOTypes = computed(() => {
  const inputTypes = props.module.inputTypes || []
  const outputTypes = props.module.outputTypes || []
  return inputTypes.length > 0 || outputTypes.length > 0
})

const displayInputTypes = computed(() => (props.module.inputTypes || []).slice(0, 2))
const displayOutputTypes = computed(() => (props.module.outputTypes || []).slice(0, 2))

function getInputTypeLabel(type) {
  const labels = props.module.inputTypeLabels || {}
  return labels[type] || formatTypeLabel(type)
}

function getOutputTypeLabel(type) {
  const labels = props.module.outputTypeLabels || {}
  return labels[type] || formatTypeLabel(type)
}

function getInputTypeDescription(type) {
  const descriptions = props.module.inputTypeDescriptions || {}
  return descriptions[type] || t('moduleCard.inputType', { type })
}

function getOutputTypeDescription(type) {
  const descriptions = props.module.outputTypeDescriptions || {}
  return descriptions[type] || t('moduleCard.outputType', { type })
}

function formatTypeLabel(type) {
  if (!type) return ''
  return type.charAt(0).toUpperCase() + type.slice(1)
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.module-card {
  will-change: transform;
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.module-card:hover {
  transform: translateY(-4px) scale(1.02);
}

.module-card:active {
  transform: translateY(-2px) scale(1.01);
  transition-duration: 0.1s;
}

.expert-card {
  border-color: rgba(245, 158, 11, 0.2);
}

/* IO Type Badges */
.io-badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 500;
  white-space: nowrap;
  transition: all 0.2s ease;
}

.module-card:hover .io-badge {
  transform: translateY(-1px);
}

.input-badge {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.output-badge {
  background: rgba(16, 185, 129, 0.15);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.25);
}

/* Icon glow on hover */
.module-card:hover .icon-container {
  box-shadow: 0 0 20px var(--icon-color, #6B7280);
}
</style>
