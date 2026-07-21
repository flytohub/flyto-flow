<template>
  <Transition
    enter-active-class="transition-all duration-150 ease-out"
    enter-from-class="opacity-0 scale-95"
    enter-to-class="opacity-100 scale-100"
    leave-active-class="transition-all duration-100 ease-in"
    leave-from-class="opacity-100 scale-100"
    leave-to-class="opacity-0 scale-95"
  >
    <div
      v-if="isOpen && filteredSuggestions.length > 0"
      ref="dropdownRef"
      class="picker-dropdown"
      :class="dropDirection === 'drop-up' ? 'bottom-full mb-1' : 'top-full mt-1'"
    >
      <!-- Select mode: flat option list (no group headers) -->
      <template v-if="isSelectMode">
        <button
          v-for="(item, idx) in filteredSuggestions"
          :key="idx"
          type="button"
          class="picker-option"
          :class="{ 'is-focused': focusedIndex === idx, 'is-selected': isItemSelected(item) }"
          @click="$emit('select-item', item)"
          @mouseenter="$emit('update:focused-index', idx)"
        >
          <span class="option-text">{{ item.displayText }}</span>
          <Check v-if="isItemSelected(item)" :size="14" class="option-check-icon" />
        </button>
      </template>

      <!-- Normal mode: grouped by type -->
      <template v-else>
        <template v-for="group in groupedSuggestions" :key="group.type">
          <div v-if="group.items.length > 0" class="picker-group">
            <div class="picker-group-label">{{ group.label }}</div>
            <button
              v-for="item in group.items"
              :key="item._globalIdx"
              type="button"
              class="picker-option"
              :class="{ 'is-focused': focusedIndex === item._globalIdx }"
              @click="$emit('select-item', item)"
              @mouseenter="$emit('update:focused-index', item._globalIdx)"
            >
              <component :is="group.iconComponent" :size="13" class="option-icon" />
              <span class="option-text">{{ item.displayText }}</span>
              <span v-if="item.badge" class="option-badge">{{ item.badge }}</span>
            </button>
          </div>
        </template>
      </template>
    </div>
  </Transition>
</template>

<script setup>
import { Check } from 'lucide-vue-next'

defineProps({
  isOpen: { type: Boolean, default: false },
  isSelectMode: { type: Boolean, default: false },
  filteredSuggestions: { type: Array, default: () => [] },
  groupedSuggestions: { type: Array, default: () => [] },
  focusedIndex: { type: Number, default: -1 },
  dropDirection: { type: String, default: 'drop-down' },
  isItemSelected: { type: Function, required: true },
})

defineEmits(['select-item', 'update:focused-index'])
</script>

<style scoped>
/* Dropdown */
.picker-dropdown {
  position: absolute;
  left: 0;
  right: 0;
  z-index: 50;
  max-height: 240px;
  overflow-y: auto;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgb(0 0 0 / 0.3);
  padding: 4px;
}

.picker-group {
  padding: 2px 0;
}

.picker-group + .picker-group {
  border-top: 1px solid rgb(51 65 85 / 0.5);
  margin-top: 2px;
  padding-top: 4px;
}

.picker-group-label {
  padding: 4px 10px 2px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #64748b;
}

.picker-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 10px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #cbd5e1;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: background 0.1s;
}

.picker-option:hover,
.picker-option.is-focused {
  background: rgb(139 92 246 / 0.15);
  color: #e2e8f0;
}

.option-icon {
  flex-shrink: 0;
  color: #64748b;
}

.option-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.picker-option.is-selected {
  background: rgb(139 92 246 / 0.1);
  color: #a78bfa;
}

.option-check-icon {
  flex-shrink: 0;
  color: #8B5CF6;
}

.option-badge {
  flex-shrink: 0;
  padding: 1px 6px;
  font-size: 10px;
  font-weight: 500;
  background: rgb(139 92 246 / 0.2);
  color: #a78bfa;
  border-radius: 4px;
}

/* Scrollbar */
.picker-dropdown::-webkit-scrollbar {
  width: 6px;
}

.picker-dropdown::-webkit-scrollbar-track {
  background: transparent;
}

.picker-dropdown::-webkit-scrollbar-thumb {
  background: rgb(71 85 105 / 0.5);
  border-radius: 3px;
}
</style>
