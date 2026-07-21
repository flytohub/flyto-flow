<template>
  <nav
    v-if="breadcrumbs.length > 1"
    class="subflow-breadcrumbs"
    :aria-label="$t('aria.subflowNavigation')"
  >
    <ol class="breadcrumb-list">
      <li
        v-for="(item, index) in breadcrumbs"
        :key="item.id"
        class="breadcrumb-item"
        :class="{ 'is-current': index === breadcrumbs.length - 1 }"
      >
        <!-- Separator -->
        <ChevronRight
          v-if="index > 0"
          :size="12"
          class="breadcrumb-separator"
        />

        <!-- Breadcrumb link/text -->
        <button
          v-if="index < breadcrumbs.length - 1"
          type="button"
          class="breadcrumb-link"
          @click="emit('navigate', item.id)"
          :title="item.label"
        >
          <Home v-if="index === 0" :size="12" class="breadcrumb-icon" />
          <Layers v-else :size="12" class="breadcrumb-icon" />
          <span class="breadcrumb-text">{{ truncate(item.label, 20) }}</span>
        </button>

        <!-- Current (non-clickable) -->
        <span v-else class="breadcrumb-current">
          <Layers :size="12" class="breadcrumb-icon" />
          <span class="breadcrumb-text">{{ truncate(item.label, 20) }}</span>
        </span>
      </li>
    </ol>

    <!-- Quick actions -->
    <div class="breadcrumb-actions">
      <button
        v-if="breadcrumbs.length > 2"
        type="button"
        class="action-btn"
        @click="emit('navigate-up')"
        :title="$t('subflow.navigateUp')"
      >
        <ArrowUp :size="14" />
      </button>

      <button
        type="button"
        class="action-btn"
        @click="emit('navigate-root')"
        :title="$t('subflow.navigateRoot')"
      >
        <Home :size="14" />
      </button>
    </div>
  </nav>
</template>

<script setup>
import { Home, Layers, ChevronRight, ArrowUp } from 'lucide-vue-next'

defineProps({
  breadcrumbs: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits([
  'navigate',
  'navigate-up',
  'navigate-root'
])

function truncate(text, maxLength) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength - 1) + '...'
}
</script>

<style scoped>
.subflow-breadcrumbs {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid #334155;
  backdrop-filter: blur(8px);
}

.breadcrumb-list {
  display: flex;
  align-items: center;
  gap: 4px;
  list-style: none;
  margin: 0;
  padding: 0;
  overflow-x: auto;
  flex: 1;
}

.breadcrumb-item {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
}

.breadcrumb-separator {
  color: #475569;
  flex-shrink: 0;
}

.breadcrumb-link {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: #94A3B8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.breadcrumb-link:hover {
  background: rgba(139, 92, 246, 0.15);
  color: #A78BFA;
}

.breadcrumb-current {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  color: #E2E8F0;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.breadcrumb-icon {
  flex-shrink: 0;
  opacity: 0.7;
}

.breadcrumb-text {
  overflow: hidden;
  text-overflow: ellipsis;
}

.breadcrumb-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-left: 8px;
  flex-shrink: 0;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid #475569;
  border-radius: 6px;
  color: #94A3B8;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8B5CF6;
  color: #A78BFA;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 640px) {
  .subflow-breadcrumbs {
    padding: 6px 8px;
  }

  .breadcrumb-text {
    max-width: 80px;
  }

  .breadcrumb-link,
  .breadcrumb-current {
    padding: 3px 6px;
    font-size: 11px;
  }
}
</style>
