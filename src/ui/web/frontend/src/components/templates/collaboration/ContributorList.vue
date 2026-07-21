<template>
  <div>
    <h3 class="font-semibold text-white mb-3 flex items-center gap-2">
      <Users :size="16" class="text-purple-400" />
      {{ $t('templateCollaboration.contributors.title') }}
      <span class="text-gray-500 font-normal text-sm">({{ contributors.length }})</span>
    </h3>

    <div v-if="contributors.length" class="space-y-2">
      <div
        v-for="contributor in contributors"
        :key="contributor.userId"
        class="flex items-center gap-3 p-2 -mx-2 rounded-xl hover:bg-white/5 hover:translate-x-0.5 transition-all duration-200"
      >
        <img
          v-if="contributor.avatar"
          :src="contributor.avatar"
          :alt="contributor.userName"
          class="w-8 h-8 rounded-full object-cover"
        />
        <div
          v-else
          class="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-xs"
        >
          {{ (contributor.userName || 'A').charAt(0).toUpperCase() }}
        </div>
        <div class="flex-1 min-w-0">
          <div class="text-sm font-medium text-white truncate">{{ contributor.userName }}</div>
          <div class="text-xs text-gray-500">
            {{ contributor.mergedCount }} {{ $t('templateCollaboration.contributors.mergedPRs') }}
          </div>
        </div>
      </div>
    </div>

    <p v-else class="text-sm text-gray-500">
      {{ $t('templateCollaboration.contributors.noContributors') }}
    </p>
  </div>
</template>

<script setup>
import { Users } from 'lucide-vue-next'

defineProps({
  contributors: { type: Array, default: () => [] },
})
</script>
