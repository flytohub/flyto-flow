<template>
  <div class="participants-list">
    <div
      v-for="participant in sortedParticipants"
      :key="participant.participantId"
      class="participant-item"
      :class="{ 'is-you': participant.isCurrentUser }"
    >
      <div class="avatar-wrapper" :class="{ 'is-active': participant.presence === 'active' }">
        <div class="avatar-ring"></div>
        <div class="avatar-inner">
          <img
            v-if="participant.avatarUrl"
            :src="participant.avatarUrl"
            :alt="participant.displayName"
          />
          <div v-else class="avatar-initials">
            {{ getInitials(participant.displayName) }}
          </div>
        </div>
        <div class="presence-indicator" :class="participant.presence"></div>
      </div>

      <div class="participant-info">
        <div class="participant-name">
          {{ participant.displayName }}
          <span v-if="participant.isCurrentUser" class="you-badge">
            {{ $t('collaboration.you', 'You') }}
          </span>
        </div>
        <div class="participant-status">
          <span class="status-dot" :class="participant.presence"></span>
          <span class="status-text" :class="participant.presence">
            {{ getPresenceText(participant.presence) }}
          </span>
          <span v-if="participant.cursor" class="editing-indicator">
            <Edit3 :size="10" />
            {{ $t('collaboration.editing', 'Editing') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Edit3 } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  participants: { type: Array, default: () => [] },
  currentUserId: { type: String, default: null },
})

const sortedParticipants = computed(() => {
  return [...props.participants]
    .map(p => ({ ...p, isCurrentUser: p.userId === props.currentUserId }))
    .sort((a, b) => {
      if (a.isCurrentUser) return -1
      if (b.isCurrentUser) return 1
      const order = { active: 0, idle: 1, away: 2, offline: 3 }
      return (order[a.presence] || 3) - (order[b.presence] || 3)
    })
})

function getInitials(name) {
  if (!name) return '?'
  const parts = name.split(' ')
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.substring(0, 2).toUpperCase()
}

function getPresenceText(presence) {
  const texts = {
    active: t('collaboration.presence.active', 'Active'),
    idle: t('collaboration.presence.idle', 'Idle'),
    away: t('collaboration.presence.away', 'Away'),
    offline: t('collaboration.presence.offline', 'Offline'),
  }
  return texts[presence] || presence
}
</script>

<style scoped>
/* Participants list */
.participants-list {
  flex-shrink: 0;
  overflow-y: auto;
  padding: 10px 12px;
  max-height: 180px;
}

.participant-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  margin-bottom: 4px;
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.05);
}

.participant-item:last-child { margin-bottom: 0; }

.participant-item.is-you {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border-color: rgba(6, 182, 212, 0.2);
}

/* Avatar */
.avatar-wrapper {
  position: relative;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
}

.avatar-ring {
  position: absolute;
  inset: -2px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #06b6d4, #8b5cf6, #ec4899, #f59e0b, #22c55e, #06b6d4);
  opacity: 0.5;
  animation: rotate-ring 4s linear infinite;
}

.avatar-wrapper.is-active .avatar-ring { opacity: 1; }

@keyframes rotate-ring {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.avatar-ring::before {
  content: '';
  position: absolute;
  inset: 2px;
  border-radius: 50%;
  background: #1e293b;
}

.avatar-inner {
  position: absolute;
  inset: 2px;
  border-radius: 50%;
  overflow: hidden;
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
}

.avatar-inner img { width: 100%; height: 100%; object-fit: cover; }

.avatar-initials {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  font-size: 12px;
  font-weight: 700;
  color: #e2e8f0;
  background: linear-gradient(135deg, #475569 0%, #334155 100%);
}

.presence-indicator {
  position: absolute;
  bottom: 1px;
  right: 1px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid #1e293b;
  z-index: 10;
}

.presence-indicator.active { background: #22c55e; }
.presence-indicator.idle { background: #eab308; }
.presence-indicator.away { background: #f97316; }
.presence-indicator.offline { background: #64748b; }

/* Participant info */
.participant-info { flex: 1; min-width: 0; }

.participant-name {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #f1f5f9;
}

.you-badge {
  padding: 1px 6px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(139, 92, 246, 0.2) 100%);
  border: 1px solid rgba(6, 182, 212, 0.3);
  border-radius: 4px;
  font-size: 9px;
  font-weight: 700;
  color: #06b6d4;
  text-transform: uppercase;
}

.participant-status {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 2px;
}

.status-dot { width: 5px; height: 5px; border-radius: 50%; }
.status-dot.active { background: #22c55e; }
.status-dot.idle { background: #eab308; }
.status-dot.away { background: #f97316; }
.status-dot.offline { background: #64748b; }

.status-text { font-size: 11px; font-weight: 500; }
.status-text.active { color: #22c55e; }
.status-text.idle { color: #eab308; }
.status-text.away { color: #f97316; }
.status-text.offline { color: #64748b; }

.editing-indicator {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 1px 5px;
  background: rgba(167, 139, 250, 0.15);
  border-radius: 4px;
  font-size: 9px;
  font-weight: 500;
  color: #a78bfa;
}

/* Scrollbar */
.participants-list::-webkit-scrollbar { width: 4px; }
.participants-list::-webkit-scrollbar-track { background: transparent; }
.participants-list::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 2px; }
</style>
