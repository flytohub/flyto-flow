<script setup>
/**
 * ProgressiveForm - Progressive Disclosure Form Container
 *
 * Implements three-level progressive disclosure UI pattern:
 * - Level 1: Basic (always visible) - Essential fields only
 * - Level 2: Standard (collapsible) - Common options
 * - Level 3: Advanced (collapsible) - Expert settings
 *
 * Design Philosophy:
 * "Simplicity by Default, Power When Needed"
 *
 * @example
 * <ProgressiveForm
 *   :standard-title="$t('form.moreOptions')"
 *   :advanced-title="$t('form.advanced')"
 *   :standard-badge="headerCount"
 *   v-model:standard-open="showStandard"
 *   v-model:advanced-open="showAdvanced"
 * >
 *   <template #basic>
 *     <FormInput v-model="url" label="URL" />
 *   </template>
 *
 *   <template #standard>
 *     <KeyValueEditor v-model="headers" />
 *   </template>
 *
 *   <template #advanced>
 *     <NumberInput v-model="timeout" label="Timeout" />
 *   </template>
 * </ProgressiveForm>
 */
import { ref, computed, useSlots, watch } from 'vue'
import DisclosureSection from './DisclosureSection.vue'

const props = defineProps({
  // === Section Titles ===
  /** Title for basic section (optional, usually just content) */
  basicTitle: {
    type: String,
    default: ''
  },
  /** Title for standard options section */
  standardTitle: {
    type: String,
    default: 'More Options'
  },
  /** Title for advanced settings section */
  advancedTitle: {
    type: String,
    default: 'Advanced Settings'
  },

  // === Badges (item counts) ===
  /** Badge for standard section */
  standardBadge: {
    type: [Number, String],
    default: null
  },
  /** Badge for advanced section */
  advancedBadge: {
    type: [Number, String],
    default: null
  },

  // === Open State (v-model) ===
  /** v-model:standard-open */
  standardOpen: {
    type: Boolean,
    default: false
  },
  /** v-model:advanced-open */
  advancedOpen: {
    type: Boolean,
    default: false
  },

  // === Visibility Control ===
  /** Hide standard section entirely */
  hideStandard: {
    type: Boolean,
    default: false
  },
  /** Hide advanced section entirely */
  hideAdvanced: {
    type: Boolean,
    default: false
  },

  // === Layout Options ===
  /** Gap between sections */
  gap: {
    type: String,
    default: '12px'
  },
  /** Compact mode (less padding) */
  compact: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:standardOpen',
  'update:advancedOpen'
])

const slots = useSlots()

// Check which slots are provided
const hasBasicSlot = computed(() => !!slots.basic)
const hasStandardSlot = computed(() => !!slots.standard && !props.hideStandard)
const hasAdvancedSlot = computed(() => !!slots.advanced && !props.hideAdvanced)

// Controlled open state
const isStandardOpen = computed({
  get: () => props.standardOpen,
  set: (val) => emit('update:standardOpen', val)
})

const isAdvancedOpen = computed({
  get: () => props.advancedOpen,
  set: (val) => emit('update:advancedOpen', val)
})

// Computed styles
const containerStyle = computed(() => ({
  '--pf-gap': props.gap
}))
</script>

<template>
  <div
    class="progressive-form"
    :class="{ compact }"
    :style="containerStyle"
  >
    <!-- Level 1: Basic (Always Visible) -->
    <section v-if="hasBasicSlot" class="pf-section pf-basic">
      <h3 v-if="basicTitle" class="pf-section-title">{{ basicTitle }}</h3>
      <div class="pf-section-content">
        <slot name="basic" />
      </div>
    </section>

    <!-- Level 2: Standard (Collapsible) -->
    <DisclosureSection
      v-if="hasStandardSlot"
      v-model="isStandardOpen"
      :title="standardTitle"
      :badge="standardBadge"
      level="standard"
      class="pf-disclosure"
    >
      <slot name="standard" />
    </DisclosureSection>

    <!-- Level 3: Advanced (Collapsible) -->
    <DisclosureSection
      v-if="hasAdvancedSlot"
      v-model="isAdvancedOpen"
      :title="advancedTitle"
      :badge="advancedBadge"
      level="advanced"
      class="pf-disclosure"
    >
      <slot name="advanced" />
    </DisclosureSection>

    <!-- Extra slot for custom content after all sections -->
    <slot name="footer" />
  </div>
</template>

<style scoped>
.progressive-form {
  display: flex;
  flex-direction: column;
  gap: var(--pf-gap, 12px);
}

.progressive-form.compact {
  gap: 8px;
}

.progressive-form.compact .pf-section-content {
  padding: 8px 0;
}

.pf-section {
  /* Basic section has no special styling */
}

.pf-section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted, #64748b);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 0 8px 0;
}

.pf-section-content {
  /* Content flows naturally */
}

.pf-disclosure {
  /* Disclosure sections get spacing from DisclosureSection component */
}
</style>
