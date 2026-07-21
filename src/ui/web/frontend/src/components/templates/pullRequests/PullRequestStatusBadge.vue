<template>
  <span :class="badgeClass" class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium">
    <component :is="icon" :size="12" />
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { GitPullRequest, GitMerge, X, Ban, FileEdit } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  status: { type: String, required: true },
  isDraft: { type: Boolean, default: false },
})

const config = computed(() => ({
  draft: { label: t('templateCollaboration.pullRequests.statusDraft'), class: 'bg-amber-500/20 text-amber-400 border border-amber-500/30', icon: FileEdit },
  open: { label: t('templateCollaboration.pullRequests.statusOpen'), class: 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30', icon: GitPullRequest },
  merged: { label: t('templateCollaboration.pullRequests.statusMerged'), class: 'bg-purple-500/20 text-purple-400 border border-purple-500/30', icon: GitMerge },
  rejected: { label: t('templateCollaboration.pullRequests.statusRejected'), class: 'bg-red-500/20 text-red-400 border border-red-500/30', icon: X },
  closed: { label: t('templateCollaboration.pullRequests.statusClosed'), class: 'bg-gray-500/20 text-gray-400 border border-gray-500/30', icon: Ban },
}))

const effectiveStatus = computed(() => {
  if (props.isDraft && props.status === 'open') return 'draft'
  return props.status
})

const badgeClass = computed(() => config.value[effectiveStatus.value]?.class || config.value.closed.class)
const label = computed(() => config.value[effectiveStatus.value]?.label || props.status)
const icon = computed(() => config.value[effectiveStatus.value]?.icon || Ban)
</script>
