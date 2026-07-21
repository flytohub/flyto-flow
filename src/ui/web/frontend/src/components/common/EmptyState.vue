<template>
  <div class="empty-state" :class="[`size-${size}`]">
    <div class="empty-icon-wrapper">
      <component :is="icon" :size="iconSize" class="empty-icon" aria-hidden="true" />
    </div>
    <h3 v-if="title" class="empty-title">{{ title }}</h3>
    <p v-if="description" class="empty-description">{{ description }}</p>
    <div v-if="$slots.default || actionText" class="empty-actions">
      <slot>
        <LoadingButton
          v-if="actionText"
          :variant="actionVariant"
          :icon="actionIcon"
          :loading="actionLoading"
          @click="$emit('action')"
        >
          {{ actionText }}
        </LoadingButton>
      </slot>
    </div>
    <p v-if="hint" class="empty-hint">{{ hint }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Inbox } from 'lucide-vue-next'
import LoadingButton from './LoadingButton.vue'

const props = defineProps({
  icon: {
    type: [Object, Function],
    default: () => Inbox
  },
  title: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  },
  actionText: {
    type: String,
    default: ''
  },
  actionIcon: {
    type: [Object, Function],
    default: null
  },
  actionVariant: {
    type: String,
    default: 'primary'
  },
  actionLoading: {
    type: Boolean,
    default: false
  },
  hint: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  }
})

defineEmits(['action'])

const iconSize = computed(() => {
  const sizes = { sm: 32, md: 48, lg: 64 }
  return sizes[props.size]
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

/* Sizes */
.size-sm {
  padding: 24px 16px;
  gap: 8px;
}

.size-md {
  padding: 48px 24px;
  gap: 12px;
}

.size-lg {
  padding: 80px 32px;
  gap: 16px;
}

/* Icon */
.empty-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}

.empty-icon {
  color: rgba(255, 255, 255, 0.2);
}

/* Text */
.empty-title {
  color: white;
  font-weight: 600;
  margin: 0;
}

.size-sm .empty-title { font-size: 14px; }
.size-md .empty-title { font-size: 18px; }
.size-lg .empty-title { font-size: 24px; }

.empty-description {
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
  max-width: 400px;
}

.size-sm .empty-description { font-size: 12px; }
.size-md .empty-description { font-size: 14px; }
.size-lg .empty-description { font-size: 16px; }

/* Actions */
.empty-actions {
  margin-top: 8px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

/* Hint */
.empty-hint {
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
  margin: 8px 0 0;
}
</style>
