<template>
  <div class="space-y-4">
    <!-- Filters -->
    <div class="flex items-center justify-between gap-4">
      <div class="flex items-center gap-2">
        <button
          v-for="s in statusOptions"
          :key="s.value"
          @click="$emit('filterStatus', s.value)"
          :class="[
            'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
            statusFilter === s.value
              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
              : 'text-gray-400 hover:text-white hover:bg-white/5'
          ]"
        >
          {{ s.label }}
        </button>
      </div>

      <button
        @click="$emit('create')"
        aria-label="Create issue"
        class="px-3 py-1.5 bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 border border-emerald-500/30 rounded-lg text-sm font-medium transition-all flex items-center gap-1"
      >
        <Plus :size="14" />
        {{ $t('templateCollaboration.templateIssues.create') }}
      </button>
    </div>

    <!-- Type Filter -->
    <div class="flex items-center gap-2">
      <button
        v-for="t in typeOptions"
        :key="t.value"
        @click="$emit('filterType', t.value)"
        :class="[
          'px-2.5 py-1 rounded-lg text-xs transition-all',
          typeFilter === t.value
            ? t.activeClass
            : 'text-gray-500 hover:text-gray-300'
        ]"
      >
        {{ t.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="w-8 h-8 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin"></div>
    </div>

    <!-- List -->
    <template v-else>
      <TransitionGroup name="list" tag="div" class="space-y-3">
        <TemplateIssueCard
          v-for="(issue, i) in issues"
          :key="issue.id"
          :issue="issue"
          :style="{ animationDelay: `${i * 50}ms` }"
          @select="$emit('select', $event)"
        />
      </TransitionGroup>

      <div v-if="!issues.length" class="text-center py-12">
        <CircleDot :size="32" class="mx-auto mb-2 text-gray-600" />
        <p class="text-gray-400">{{ $t('templateCollaboration.templateIssues.noIssues') }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CircleDot, Plus } from 'lucide-vue-next'
import TemplateIssueCard from './TemplateIssueCard.vue'

const { t } = useI18n()

defineProps({
  issues: { type: Array, default: () => [] },
  statusFilter: { type: String, default: null },
  typeFilter: { type: String, default: null },
  loading: { type: Boolean, default: false },
})

defineEmits(['select', 'create', 'filterStatus', 'filterType'])

const statusOptions = computed(() => [
  { value: null, label: t('templateCollaboration.filters.all') },
  { value: 'open', label: t('templateCollaboration.pullRequests.statusOpen') },
  { value: 'closed', label: t('templateCollaboration.pullRequests.statusClosed') },
])

const typeOptions = computed(() => [
  { value: null, label: t('templateCollaboration.filters.allTypes'), activeClass: 'bg-gray-500/20 text-gray-300' },
  { value: 'bug', label: t('templateCollaboration.templateIssues.typeBug'), activeClass: 'bg-red-500/20 text-red-400' },
  { value: 'feature', label: t('templateCollaboration.templateIssues.typeFeature'), activeClass: 'bg-blue-500/20 text-blue-400' },
  { value: 'question', label: t('templateCollaboration.templateIssues.typeQuestion'), activeClass: 'bg-amber-500/20 text-amber-400' },
])
</script>

<style scoped>
.list-enter-active {
  animation: list-in 0.3s ease-out both;
}
.list-leave-active {
  animation: list-in 0.2s ease reverse both;
}
.list-move {
  transition: transform 0.3s ease;
}
@keyframes list-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
