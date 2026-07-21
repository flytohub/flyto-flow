<script setup>
/**
 * DisclosureSection - Collapsible section with smooth animation
 *
 * Part of Progressive Disclosure UI pattern.
 * Uses native <details>/<summary> for accessibility + custom styling.
 *
 * @example
 * <DisclosureSection
 *   v-model="isOpen"
 *   :title="$t('form.advanced')"
 *   :badge="3"
 *   level="advanced"
 * >
 *   <template #default>
 *     <!-- Content here -->
 *   </template>
 * </DisclosureSection>
 */
import { computed } from 'vue'
import { ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  /** v-model binding for open state */
  modelValue: {
    type: Boolean,
    default: false
  },
  /** Section title */
  title: {
    type: String,
    required: true
  },
  /** Optional badge count (e.g., "3 items") */
  badge: {
    type: [Number, String],
    default: null
  },
  /** Disclosure level: 'standard' | 'advanced' */
  level: {
    type: String,
    default: 'standard',
    validator: (v) => ['standard', 'advanced'].includes(v)
  },
  /** Disable interaction */
  disabled: {
    type: Boolean,
    default: false
  },
  /** Default open state (uncontrolled mode) */
  defaultOpen: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = computed({
  get: () => props.modelValue ?? props.defaultOpen,
  set: (val) => emit('update:modelValue', val)
})

function toggle(e) {
  if (props.disabled) {
    e.preventDefault()
    return
  }
  // Prevent default to control state ourselves
  e.preventDefault()
  isOpen.value = !isOpen.value
}

const levelClass = computed(() => `level-${props.level}`)
</script>

<template>
  <details
    class="disclosure-section"
    :class="[levelClass, { disabled }]"
    :open="isOpen"
  >
    <summary
      class="disclosure-header"
      @click="toggle"
      :tabindex="disabled ? -1 : 0"
    >
      <ChevronRight
        :size="14"
        class="disclosure-chevron"
        :class="{ open: isOpen }"
      />
      <span class="disclosure-title">{{ title }}</span>
      <span v-if="badge != null" class="disclosure-badge">
        {{ badge }}
      </span>
    </summary>
    <div class="disclosure-content" v-show="isOpen">
      <slot />
    </div>
  </details>
</template>

<style scoped>
.disclosure-section {
  border: 1px solid var(--border-secondary, #334155);
  border-radius: 8px;
  overflow: hidden;
  background: var(--bg-secondary, rgba(30, 41, 59, 0.3));
}

.disclosure-section.disabled {
  opacity: 0.6;
  pointer-events: none;
}

/* Level styling */
.disclosure-section.level-standard {
  border-color: var(--border-secondary, #334155);
}

.disclosure-section.level-advanced {
  border-color: var(--border-muted, #475569);
  background: var(--bg-tertiary, rgba(30, 41, 59, 0.2));
}

.disclosure-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  background: var(--bg-secondary, rgba(30, 41, 59, 0.5));
  transition: background 0.15s ease;
  list-style: none; /* Remove default marker */
}

.disclosure-header::-webkit-details-marker {
  display: none; /* Remove Safari marker */
}

.disclosure-header:hover {
  background: var(--bg-hover, rgba(139, 92, 246, 0.1));
}

.disclosure-header:focus-visible {
  outline: 2px solid var(--primary, #8B5CF6);
  outline-offset: -2px;
}

.disclosure-chevron {
  color: var(--text-muted, #64748b);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}

.disclosure-chevron.open {
  transform: rotate(90deg);
}

.disclosure-title {
  flex: 1;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary, #94a3b8);
}

.disclosure-badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 10px;
  background: var(--bg-tertiary, rgba(139, 92, 246, 0.15));
  color: var(--text-muted, #94a3b8);
}

.disclosure-content {
  padding: 12px;
  border-top: 1px solid var(--border-secondary, #334155);
}

/* Animation for content */
.disclosure-section[open] .disclosure-content {
  animation: slideDown 0.2s ease-out;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
