<template>
  <div class="relative p-6 border-b border-white/5">
    <!-- Header glow -->
    <div class="absolute inset-0 bg-gradient-to-r from-purple-500/10 via-transparent to-blue-500/10"></div>

    <div class="relative flex items-center justify-between">
      <div class="flex items-center gap-4">
        <!-- Icon with glow -->
        <div class="relative">
          <div
            class="absolute inset-0 rounded-xl blur-lg opacity-60"
            :class="iconGlowClass"
          ></div>
          <div
            class="relative w-12 h-12 rounded-xl flex items-center justify-center"
            :class="iconBgClass"
          >
            <component :is="headerIcon" :size="22" class="text-white" />
          </div>
        </div>

        <div>
          <h2 class="text-xl font-semibold text-white">{{ headerTitle }}</h2>
          <p class="text-sm text-gray-400 mt-0.5">{{ headerSubtitle }}</p>
        </div>
      </div>

      <button
        @click="$emit('close')"
        class="p-2.5 hover:bg-white/10 rounded-xl transition-all text-gray-400 hover:text-white group"
      >
        <X :size="20" class="transition-transform group-hover:rotate-90" />
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Blocks, X, Plus, RefreshCw } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps({
  isInsertionMode: {
    type: Boolean,
    default: false
  },
  isReplaceMode: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])

const headerIcon = computed(() => {
  if (props.isReplaceMode) return RefreshCw
  if (props.isInsertionMode) return Plus
  return Blocks
})

const iconGlowClass = computed(() => {
  if (props.isReplaceMode) return 'bg-cyan-500'
  if (props.isInsertionMode) return 'bg-emerald-500'
  return 'bg-purple-500'
})

const iconBgClass = computed(() => {
  if (props.isReplaceMode) return 'bg-gradient-to-br from-cyan-400 to-blue-500'
  if (props.isInsertionMode) return 'bg-gradient-to-br from-emerald-400 to-teal-500'
  return 'bg-gradient-to-br from-purple-400 to-blue-500'
})

const headerTitle = computed(() => {
  if (props.isReplaceMode) return t('workflow.replaceNode.title', 'Replace Node')
  if (props.isInsertionMode) return t('workflow.insertNode.title', 'Insert Node')
  return t('workflow.addNode.title')
})

const headerSubtitle = computed(() => {
  if (props.isReplaceMode) return t('workflow.replaceNode.subtitle', 'Replace this node with another module')
  if (props.isInsertionMode) return t('workflow.insertNode.subtitle', 'Insert a node between two connected nodes')
  return t('workflow.addNode.subtitle')
})
</script>
