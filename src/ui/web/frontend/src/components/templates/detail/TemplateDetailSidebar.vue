<template>
  <div>
    <!-- Info Card -->
    <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 sticky top-24">
      <h3 class="font-semibold text-white mb-4 flex items-center gap-2">
        <Info :size="16" class="text-purple-400" />
        {{ $t('templateDetail.info.title') }}
      </h3>

      <dl class="space-y-4 text-sm">
        <div class="flex justify-between">
          <dt class="text-gray-500">{{ $t('templateDetail.info.version') }}</dt>
          <dd class="font-medium text-white">{{ version }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500">{{ $t('common.created') }}</dt>
          <dd class="font-medium text-white">{{ formatDate(createdAt) }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500">{{ $t('common.updated') }}</dt>
          <dd class="font-medium text-white">{{ formatDate(updatedAt) }}</dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500">{{ $t('templateDetail.info.license') }}</dt>
          <dd class="font-medium text-white">
            <span :class="mutability === 'locked' ? 'text-amber-400' : 'text-emerald-400'">
              {{ mutability === 'locked' ? $t('templateDetail.info.locked') : $t('templateDetail.info.forkable') }}
            </span>
          </dd>
        </div>
        <div class="flex justify-between">
          <dt class="text-gray-500">{{ $t('templateDetail.info.category') }}</dt>
          <dd class="font-medium text-white">{{ categoryName || $t('templateDetail.info.other') }}</dd>
        </div>
      </dl>

      <hr class="my-6 border-white/10" />

      <!-- Author -->
      <h3 class="font-semibold text-white mb-4 flex items-center gap-2">
        <User :size="16" class="text-purple-400" />
        {{ $t('templateDetail.author.title') }}
      </h3>
      <router-link
        v-if="creatorId"
        :to="`/creators/${creatorId}`"
        class="flex items-center gap-3 p-3 -m-3 rounded-xl hover:bg-white/5 transition-all group"
      >
        <img
          v-if="creatorAvatar"
          :src="creatorAvatar"
          :alt="creatorName"
          class="w-12 h-12 rounded-xl object-cover shadow-lg"
        />
        <div
          v-else
          class="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-purple-500/30"
        >
          {{ (creatorName || 'A').charAt(0).toUpperCase() }}
        </div>
        <div class="flex-1">
          <div class="font-medium text-white group-hover:text-purple-400 transition-colors">
            {{ creatorName || $t('templateDetail.anonymous') }}
          </div>
          <div class="text-sm text-gray-500">{{ $t('templateDetail.author.viewProfile') }}</div>
        </div>
        <ChevronRight :size="16" class="text-gray-500 group-hover:text-purple-400 transition-colors" />
      </router-link>
      <div v-else class="text-gray-500 text-sm">{{ $t('templateDetail.unknownAuthor') }}</div>

      <!-- Chat with Author Button -->
      <button
        v-if="creatorId && !isOwnTemplate"
        @click="$emit('chat')"
        :disabled="chatLoading"
        aria-label="Start chat"
        class="w-full mt-4 py-2.5 text-sm font-medium text-purple-400 hover:text-white hover:bg-purple-500/20 border border-purple-500/30 hover:border-purple-500/50 rounded-xl transition-all flex items-center justify-center gap-2"
      >
        <Loader2 v-if="chatLoading" :size="16" class="animate-spin" />
        <MessageSquareText v-else :size="16" />
        {{ $t('chat.startChat') }}
      </button>

      <!-- Request Collaboration (locked templates, non-owner) -->
      <button
        v-if="mutability === 'locked' && !isOwnTemplate && !isCollaborator && collabRequestStatus !== 'pending'"
        @click="$emit('request-collab')"
        :disabled="collabRequestLoading"
        class="w-full mt-3 py-2.5 text-sm font-medium text-amber-400 hover:text-white hover:bg-amber-500/20 border border-amber-500/30 hover:border-amber-500/50 rounded-xl transition-all flex items-center justify-center gap-2"
      >
        <Loader2 v-if="collabRequestLoading" :size="16" class="animate-spin" />
        <UserPlus v-else :size="16" />
        {{ $t('templateDetail.collabRequest.requestAccess', 'Request Collaboration') }}
      </button>

      <!-- Pending request indicator -->
      <div
        v-if="collabRequestStatus === 'pending'"
        class="w-full mt-3 py-2.5 text-sm text-amber-400/80 bg-amber-500/10 border border-amber-500/20 rounded-xl flex items-center justify-center gap-2"
      >
        <Clock :size="16" />
        {{ $t('templateDetail.collabRequest.pending', 'Request Pending') }}
      </div>

      <!-- Collaborator badge -->
      <div
        v-if="isCollaborator && !isOwnTemplate"
        class="w-full mt-3 py-2.5 text-sm text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 rounded-xl flex items-center justify-center gap-2"
      >
        <UserCheck :size="16" />
        {{ $t('templateDetail.collabRequest.collaborator', 'Collaborator') }}
      </div>

      <hr class="my-6 border-white/10" />

      <!-- Report -->
      <button
        v-if="!isOwnTemplate"
        @click="$emit('report')"
        aria-label="Report template"
        class="w-full py-2.5 text-sm text-gray-500 hover:text-red-400 hover:bg-red-500/10 border border-transparent hover:border-red-500/30 rounded-xl transition-all flex items-center justify-center gap-2"
      >
        <Flag :size="16" />
        {{ $t('templateDetail.reportTemplate') }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { Info, User, ChevronRight, MessageSquareText, Flag, Loader2, UserPlus, UserCheck, Clock } from 'lucide-vue-next'

defineProps({
  version: { type: String, default: '1.0.0' },
  createdAt: { type: String, default: '' },
  updatedAt: { type: String, default: '' },
  mutability: { type: String, default: 'locked' },
  categoryName: { type: String, default: '' },
  creatorId: { type: String, default: '' },
  creatorName: { type: String, default: '' },
  creatorAvatar: { type: String, default: '' },
  isOwnTemplate: { type: Boolean, default: false },
  isCollaborator: { type: Boolean, default: false },
  chatLoading: { type: Boolean, default: false },
  collabRequestStatus: { type: String, default: null },
  collabRequestLoading: { type: Boolean, default: false },
})

defineEmits(['chat', 'report', 'request-collab'])

function formatDate(dateStr) {
  if (!dateStr) return 'Unknown'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  })
}
</script>
