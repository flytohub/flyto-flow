<template>
  <div
    :class="[
      'relative rounded-xl border-2 transition-all duration-300 cursor-pointer overflow-hidden',
      decisionStyles.container,
      isExpanded ? 'shadow-lg' : 'hover:shadow-md'
    ]"
    @click="$emit('click', decision)"
  >
    <!-- Glow Effect -->
    <div
      :class="['absolute inset-0 pointer-events-none', decisionStyles.glow]"
    />

    <!-- Main Content -->
    <div class="relative p-4">
      <!-- Header Row -->
      <div class="flex items-center gap-3">
        <!-- Decision Icon -->
        <div
          :class="[
            'w-10 h-10 rounded-lg flex items-center justify-center',
            decisionStyles.iconBg
          ]"
        >
          <component
            :is="decisionIcon"
            :size="20"
            :class="decisionStyles.iconColor"
          />
        </div>

        <!-- Decision Info -->
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <span class="font-semibold text-white">{{ decisionLabel }}</span>
            <!-- Confidence Badge -->
            <div
              :class="[
                'px-2 py-0.5 text-xs font-bold rounded-full',
                confidenceStyles
              ]"
            >
              {{ Math.round(decision.confidence * 100) }}%
            </div>
          </div>
          <p class="text-xs text-gray-400 truncate mt-0.5">
            {{ decision.reason }}
          </p>
        </div>

        <!-- Expand Chevron -->
        <ChevronDown
          :size="20"
          :class="[
            'transition-transform duration-200 text-gray-400',
            isExpanded ? 'rotate-180' : ''
          ]"
        />
      </div>

      <!-- Confidence Bar -->
      <div class="mt-3 h-1.5 bg-gray-800 rounded-full overflow-hidden">
        <div
          :class="['h-full rounded-full transition-all duration-500', decisionStyles.bar]"
          :style="{ width: `${decision.confidence * 100}%` }"
        />
      </div>

      <!-- Expanded Content -->
      <Transition
        enter-active-class="transition-all duration-200 ease-out"
        enter-from-class="opacity-0 max-h-0"
        enter-to-class="opacity-100 max-h-96"
        leave-active-class="transition-all duration-150 ease-in"
        leave-from-class="opacity-100 max-h-96"
        leave-to-class="opacity-0 max-h-0"
      >
        <div v-if="isExpanded" class="mt-4 space-y-3 overflow-hidden">
          <!-- Full Reason -->
          <div class="p-3 bg-gray-900/50 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <MessageSquare :size="14" class="text-gray-400" />
              <span class="text-xs font-medium text-gray-300">{{ $t('lineage.decision.reason') }}</span>
            </div>
            <p class="text-sm text-gray-300">{{ decision.reason }}</p>
          </div>

          <!-- Evidence -->
          <div v-if="decision.evidence?.length" class="p-3 bg-gray-900/50 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <FileText :size="14" class="text-gray-400" />
              <span class="text-xs font-medium text-gray-300">{{ $t('lineage.decision.evidence') }}</span>
              <span class="text-xs text-gray-500">({{ decision.evidence.length }})</span>
            </div>
            <div class="flex flex-wrap gap-2">
              <button
                v-for="artifactId in decision.evidence.slice(0, 5)"
                :key="artifactId"
                class="px-2 py-1 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded border border-gray-700 transition-colors"
                @click.stop="$emit('view-artifact', artifactId)"
              >
                {{ formatArtifactId(artifactId) }}
              </button>
              <span v-if="decision.evidence.length > 5" class="text-xs text-gray-500 self-center">
                +{{ decision.evidence.length - 5 }} more
              </span>
            </div>
          </div>

          <!-- Alternatives -->
          <div v-if="decision.alternatives?.length" class="p-3 bg-gray-900/50 rounded-lg">
            <div class="flex items-center gap-2 mb-2">
              <GitBranch :size="14" class="text-gray-400" />
              <span class="text-xs font-medium text-gray-300">{{ $t('lineage.decision.alternatives') }}</span>
            </div>
            <div class="space-y-2">
              <div
                v-for="(alt, idx) in decision.alternatives.slice(0, 3)"
                :key="idx"
                class="text-xs text-gray-400 flex items-center gap-2"
              >
                <div class="w-1.5 h-1.5 rounded-full bg-gray-600" />
                <span>{{ alt.action || alt.description || JSON.stringify(alt) }}</span>
              </div>
            </div>
          </div>

          <!-- Metadata -->
          <div v-if="hasMetadata" class="flex flex-wrap gap-2">
            <div
              v-for="(value, key) in displayMetadata"
              :key="key"
              class="px-2 py-1 text-xs bg-gray-800/50 text-gray-400 rounded"
            >
              <span class="text-gray-500">{{ key }}:</span>
              <span class="ml-1 text-gray-300">{{ value }}</span>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  HelpCircle,
  Flag,
  ChevronDown,
  MessageSquare,
  FileText,
  GitBranch
} from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  decision: {
    type: Object,
    required: true
  },
  isExpanded: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click', 'view-artifact'])

// Decision type mapping
const DECISION_TYPES = {
  pass: {
    label: 'Pass',
    icon: CheckCircle,
    color: 'emerald',
    container: 'bg-gradient-to-r from-emerald-950/50 to-emerald-900/20 border-emerald-500/40',
    glow: 'bg-gradient-to-r from-emerald-500/5 to-transparent',
    iconBg: 'bg-emerald-500/20',
    iconColor: 'text-emerald-400',
    bar: 'bg-emerald-500'
  },
  fail: {
    label: 'Fail',
    icon: XCircle,
    color: 'red',
    container: 'bg-gradient-to-r from-red-950/50 to-red-900/20 border-red-500/40',
    glow: 'bg-gradient-to-r from-red-500/5 to-transparent',
    iconBg: 'bg-red-500/20',
    iconColor: 'text-red-400',
    bar: 'bg-red-500'
  },
  need_fix: {
    label: 'Needs Fix',
    icon: AlertTriangle,
    color: 'amber',
    container: 'bg-gradient-to-r from-amber-950/50 to-amber-900/20 border-amber-500/40',
    glow: 'bg-gradient-to-r from-amber-500/5 to-transparent',
    iconBg: 'bg-amber-500/20',
    iconColor: 'text-amber-400',
    bar: 'bg-amber-500'
  },
  retry: {
    label: 'Retry',
    icon: RefreshCw,
    color: 'blue',
    container: 'bg-gradient-to-r from-blue-950/50 to-blue-900/20 border-blue-500/40',
    glow: 'bg-gradient-to-r from-blue-500/5 to-transparent',
    iconBg: 'bg-blue-500/20',
    iconColor: 'text-blue-400',
    bar: 'bg-blue-500'
  },
  complete: {
    label: 'Complete',
    icon: Flag,
    color: 'violet',
    container: 'bg-gradient-to-r from-violet-950/50 to-violet-900/20 border-violet-500/40',
    glow: 'bg-gradient-to-r from-violet-500/5 to-transparent',
    iconBg: 'bg-violet-500/20',
    iconColor: 'text-violet-400',
    bar: 'bg-violet-500'
  },
  ask_user: {
    label: 'Ask User',
    icon: HelpCircle,
    color: 'cyan',
    container: 'bg-gradient-to-r from-cyan-950/50 to-cyan-900/20 border-cyan-500/40',
    glow: 'bg-gradient-to-r from-cyan-500/5 to-transparent',
    iconBg: 'bg-cyan-500/20',
    iconColor: 'text-cyan-400',
    bar: 'bg-cyan-500'
  }
}

const DEFAULT_STYLE = {
  label: 'Decision',
  icon: HelpCircle,
  container: 'bg-gradient-to-r from-gray-900/80 to-gray-800/40 border-gray-700/40',
  glow: 'bg-transparent',
  iconBg: 'bg-gray-700/50',
  iconColor: 'text-gray-400',
  bar: 'bg-gray-500'
}

const decisionType = computed(() => props.decision.decision?.toLowerCase() || 'unknown')

const decisionStyles = computed(() => {
  return DECISION_TYPES[decisionType.value] || DEFAULT_STYLE
})

const decisionLabel = computed(() => {
  return DECISION_TYPES[decisionType.value]?.label || props.decision.decision || 'Decision'
})

const decisionIcon = computed(() => {
  return DECISION_TYPES[decisionType.value]?.icon || HelpCircle
})

const confidenceStyles = computed(() => {
  const confidence = props.decision.confidence || 0
  if (confidence >= 0.8) return 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
  if (confidence >= 0.6) return 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
  return 'bg-red-500/20 text-red-400 border border-red-500/30'
})

const hasMetadata = computed(() => {
  const meta = props.decision.metadata
  return meta && Object.keys(meta).length > 0
})

const displayMetadata = computed(() => {
  const meta = props.decision.metadata || {}
  // Filter out complex objects and limit to simple values
  const result = {}
  for (const [key, value] of Object.entries(meta)) {
    if (typeof value !== 'object' && value !== null && value !== undefined) {
      result[key] = value
    }
  }
  return result
})

function formatArtifactId(id) {
  // Shorten artifact IDs for display
  if (id.startsWith('artifact_')) {
    return id.replace('artifact_', '').slice(0, 12)
  }
  return id.slice(0, 15)
}
</script>
