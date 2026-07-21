<template>
  <span
    :class="[
      'inline-flex items-center gap-1 rounded-full text-xs font-medium',
      sizeClasses,
      statusClasses
    ]"
    role="status"
  >
    <span v-if="showDot" :class="dotClasses" aria-hidden="true"></span>
    <component
      v-if="showIcon && iconComponent"
      :is="iconComponent"
      :size="iconSize"
      :class="{ 'animate-spin': status === 'running' || status === 'loading' }"
    />
    <slot>{{ displayLabel }}</slot>
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  AlertCircle,
  Info,
  Clock,
  Loader2
} from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  /**
   * Status type - supports multiple variants
   */
  status: {
    type: String,
    required: true
  },
  /**
   * Variant determines styling theme
   * - default: general purpose
   * - admin: admin panel status (active/hidden/banned)
   * - trace: execution traces (completed/failed/running)
   * - plugin: plugin status (installed/loaded/downloading)
   */
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'admin', 'trace', 'plugin'].includes(v)
  },
  /**
   * Badge size
   */
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  /**
   * Show icon (auto-enabled for trace variant)
   */
  showIcon: {
    type: Boolean,
    default: false
  },
  /**
   * Show animated dot (auto-enabled for plugin variant on certain statuses)
   */
  showDot: {
    type: Boolean,
    default: false
  },
  /**
   * Custom label (overrides auto-generated label)
   */
  label: {
    type: String,
    default: ''
  }
})

// Status configurations per variant
const statusConfigs = computed(() => ({
  default: {
    success: { classes: 'bg-green-500/20 text-green-400 border border-green-500/30', icon: CheckCircle },
    error: { classes: 'bg-red-500/20 text-red-400 border border-red-500/30', icon: XCircle },
    warning: { classes: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30', icon: AlertTriangle },
    info: { classes: 'bg-blue-500/20 text-blue-400 border border-blue-500/30', icon: Info },
    pending: { classes: 'bg-gray-500/20 text-gray-400 border border-gray-500/30', icon: Clock },
    loading: { classes: 'bg-purple-500/20 text-purple-400 border border-purple-500/30', icon: Loader2 }
  },
  admin: {
    active: { classes: 'bg-green-500 text-white', label: t('admin.templates.status.active', 'Active') },
    hidden: { classes: 'bg-yellow-500 text-white', label: t('admin.templates.status.hidden', 'Hidden') },
    banned: { classes: 'bg-red-500 text-white', label: t('admin.templates.status.banned', 'Banned') }
  },
  trace: {
    completed: { classes: 'bg-green-900/30 text-green-400 border border-green-900/50', icon: CheckCircle, label: t('status.completed', 'Completed') },
    success: { classes: 'bg-green-900/30 text-green-400 border border-green-900/50', icon: CheckCircle, label: t('status.success', 'Success') },
    failed: { classes: 'bg-red-900/30 text-red-400 border border-red-900/50', icon: XCircle, label: t('status.failed', 'Failed') },
    error: { classes: 'bg-red-900/30 text-red-400 border border-red-900/50', icon: XCircle, label: t('status.error', 'Error') },
    running: { classes: 'bg-blue-900/30 text-blue-400 border border-blue-900/50', icon: Loader2, label: t('status.running', 'Running') },
    pending: { classes: 'bg-yellow-900/30 text-yellow-400 border border-yellow-900/50', icon: Clock, label: t('status.pending', 'Pending') },
    cancelled: { classes: 'bg-gray-700/30 text-gray-400 border border-gray-600/50', icon: AlertCircle, label: t('status.cancelled', 'Cancelled') }
  },
  plugin: {
    not_installed: { classes: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400', dot: 'bg-gray-400', label: t('pluginStatus.notInstalled', 'Not Installed') },
    downloading: { classes: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300', dot: 'bg-blue-500 animate-pulse', label: t('pluginStatus.downloading', 'Downloading') },
    installed: { classes: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300', dot: 'bg-green-500', label: t('pluginStatus.installed', 'Installed') },
    loading: { classes: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300', dot: 'bg-amber-500 animate-pulse', label: t('pluginStatus.loading', 'Loading') },
    loaded: { classes: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300', dot: 'bg-purple-500', label: t('pluginStatus.loaded', 'Loaded') },
    unloading: { classes: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300', dot: 'bg-orange-500 animate-pulse', label: t('pluginStatus.unloading', 'Unloading') },
    error: { classes: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300', dot: 'bg-red-500', label: t('common.error', 'Error') }
  }
}))

const currentConfig = computed(() => {
  const variantConfigs = statusConfigs.value[props.variant] || statusConfigs.value.default
  return variantConfigs[props.status] || variantConfigs.pending || variantConfigs.info || { classes: '' }
})

const statusClasses = computed(() => currentConfig.value.classes || '')

const sizeClasses = computed(() => {
  const classes = {
    sm: 'px-1.5 py-0.5 text-[10px]',
    md: 'px-2 py-0.5 text-xs',
    lg: 'px-2.5 py-1 text-sm'
  }
  return classes[props.size]
})

const iconComponent = computed(() => {
  // Auto-show icons for trace variant
  if (props.variant === 'trace' || props.showIcon) {
    return currentConfig.value.icon || null
  }
  return props.showIcon ? currentConfig.value.icon : null
})

const iconSize = computed(() => {
  const sizes = { sm: 10, md: 12, lg: 14 }
  return sizes[props.size]
})

const dotClasses = computed(() => {
  if (!currentConfig.value.dot) return ''
  return ['w-2 h-2 rounded-full', currentConfig.value.dot]
})

const displayLabel = computed(() => {
  if (props.label) return props.label
  return currentConfig.value.label || props.status
})
</script>
