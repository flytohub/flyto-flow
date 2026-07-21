<template>
  <div class="space-y-4">
    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="w-8 h-8 border-2 border-purple-500/20 border-t-purple-500 rounded-full animate-spin"></div>
    </div>

    <template v-else>
      <!-- Timeline -->
      <div v-if="commits.length" class="relative">
        <!-- Vertical line -->
        <div class="absolute left-4 top-2 bottom-2 w-px bg-white/10"></div>

        <div
          v-for="(commit, i) in commits"
          :key="commit.id"
          class="relative pl-10 pb-6 last:pb-0 animate-slide-in"
          :style="{ animationDelay: `${i * 60}ms` }"
        >
          <!-- Dot -->
          <div :class="[
            'absolute left-2.5 w-3 h-3 rounded-full border-2',
            commit.mergedFromPr
              ? 'bg-purple-500 border-purple-400'
              : 'bg-gray-600 border-gray-500'
          ]"></div>

          <div class="bg-gray-800/30 rounded-2xl border border-white/5 p-4 hover:border-purple-500/20 hover:shadow-md hover:shadow-purple-500/5 transition-all duration-200">
            <div class="flex items-start justify-between">
              <div>
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs font-mono text-gray-500">v{{ commit.versionNumber }}</span>
                  <span v-if="commit.versionTag" class="px-1.5 py-0.5 bg-blue-500/20 text-blue-400 rounded text-xs">
                    {{ commit.versionTag }}
                  </span>
                  <span v-if="commit.mergedFromPr" class="px-1.5 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs flex items-center gap-1">
                    <GitMerge :size="10" />
                    PR
                  </span>
                </div>
                <p class="text-sm text-white">
                  {{ commit.changeSummary || $t('templateCollaboration.commitHistory.noSummary') }}
                </p>
                <p class="text-xs text-gray-500 mt-1">
                  <span v-if="commit.prAuthor">{{ commit.prAuthor }}</span>
                  <span v-else>{{ commit.createdBy || $t('templateCollaboration.commitHistory.unknownAuthor') }}</span>
                  &middot;
                  {{ formatDate(commit.createdAt) }}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div v-else class="text-center py-12">
        <History :size="32" class="mx-auto mb-2 text-gray-600" />
        <p class="text-gray-400">{{ $t('templateCollaboration.commitHistory.noHistory') }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { GitMerge, History } from 'lucide-vue-next'

defineProps({
  commits: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

function formatDate(dateStr) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
  })
}
</script>

<style scoped>
.animate-slide-in {
  animation: slide-in 0.35s ease-out both;
}
@keyframes slide-in {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>
