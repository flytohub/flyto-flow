<template>
  <div class="icon-picker">
    <!-- Search input -->
    <div class="search-container">
      <Search :size="16" class="search-icon" />
      <AppInput
        ref="searchInput"
        v-model="searchQuery"
        :placeholder="$t('iconPicker.searchPlaceholder', 'Search icons...')"
        @input="debouncedSearch"
      />
      <button
        v-if="searchQuery"
        @click="clearSearch"
        class="clear-btn"
        type="button"
        aria-label="Clear search"
      >
        <X :size="14" />
      </button>
    </div>

    <!-- Category tabs -->
    <div class="category-tabs">
      <button
        v-for="cat in categories"
        :key="cat.id"
        @click="activeCategory = cat.id"
        class="category-tab"
        :class="{ active: activeCategory === cat.id }"
        type="button"
      >
        {{ cat.label }}
      </button>
    </div>

    <!-- Icons grid -->
    <div class="icons-grid" ref="gridRef">
      <button
        v-for="icon in displayedIcons"
        :key="icon.id"
        @click="selectIcon(icon)"
        class="icon-item"
        :class="{ selected: selectedIconId === icon.id }"
        :title="icon.name"
        type="button"
      >
        <img
          :src="getIconPreviewUrl(icon)"
          :alt="icon.name"
          class="icon-preview"
          loading="lazy"
        />
        <span class="icon-name">{{ icon.name }}</span>
      </button>

      <!-- Empty state -->
      <div v-if="displayedIcons.length === 0" class="empty-state">
        <SearchX :size="32" class="empty-icon" />
        <p>{{ $t('iconPicker.noResults', 'No icons found') }}</p>
      </div>
    </div>

    <!-- Selected icon preview -->
    <div v-if="selectedIcon" class="selected-preview">
      <div class="preview-icon-wrapper" :style="{ backgroundColor: previewColor + '20' }">
        <img
          :src="getIconPreviewUrl(selectedIcon, 32)"
          :alt="selectedIcon.name"
          class="preview-icon"
        />
      </div>
      <div class="preview-info">
        <span class="preview-name">{{ selectedIcon.name }}</span>
        <span class="preview-id">{{ selectedIcon.id }}</span>
      </div>
    </div>

    <!-- Color picker for selected icon -->
    <div v-if="showColorPicker && selectedIcon" class="color-section">
      <label class="color-label">{{ $t('iconPicker.iconColor', 'Icon Color') }}</label>
      <div class="color-presets">
        <button
          v-for="color in colorPresets"
          :key="color"
          @click="previewColor = color"
          class="color-preset"
          :class="{ active: previewColor === color }"
          :style="{ backgroundColor: color }"
          type="button"
        />
        <input
          type="color"
          v-model="previewColor"
          class="color-input"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { Search, X, SearchX } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import { BRAND_ICONS, CATEGORY_ICONS, getIconUrl, searchIcons } from '@/utils/iconify'

const props = defineProps({
  modelValue: {
    type: String,
    default: null
  },
  color: {
    type: String,
    default: '#6B7280'
  },
  showColorPicker: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:modelValue', 'update:color', 'select'])

const searchQuery = ref('')
const activeCategory = ref('brands')
const selectedIconId = ref(props.modelValue)
const previewColor = ref(props.color)
const searchInput = ref(null)
const gridRef = ref(null)

const categories = [
  { id: 'brands', label: 'Brands' },
  { id: 'categories', label: 'Categories' },
  { id: 'all', label: 'All' }
]

const colorPresets = [
  '#6B7280', '#EF4444', '#F59E0B', '#10B981', '#3B82F6',
  '#8B5CF6', '#EC4899', '#06B6D4', '#84CC16', '#000000'
]

// Get icons based on active category and search
const displayedIcons = computed(() => {
  if (searchQuery.value) {
    return searchIcons(searchQuery.value, {
      includeBrands: activeCategory.value !== 'categories',
      includeCategories: activeCategory.value !== 'brands',
      limit: 60
    })
  }

  switch (activeCategory.value) {
    case 'brands':
      return BRAND_ICONS.slice(0, 60)
    case 'categories':
      return CATEGORY_ICONS
    case 'all':
      return [...BRAND_ICONS.slice(0, 40), ...CATEGORY_ICONS.slice(0, 20)]
    default:
      return BRAND_ICONS.slice(0, 60)
  }
})

// Selected icon object
const selectedIcon = computed(() => {
  if (!selectedIconId.value) return null
  return [...BRAND_ICONS, ...CATEGORY_ICONS].find(i => i.id === selectedIconId.value)
})

// Get preview URL for icon
function getIconPreviewUrl(icon, size = 24) {
  // Use icon's default color or current preview color
  const color = icon.color || previewColor.value
  return getIconUrl(icon.id, { color, size })
}

// Select an icon
function selectIcon(icon) {
  selectedIconId.value = icon.id
  previewColor.value = icon.color || previewColor.value
  emit('update:modelValue', icon.id)
  emit('update:color', previewColor.value)
  emit('select', {
    id: icon.id,
    name: icon.name,
    color: previewColor.value,
    url: getIconUrl(icon.id, { color: previewColor.value, size: 48 })
  })
}

// Clear search
function clearSearch() {
  searchQuery.value = ''
  searchInput.value?.focus()
}

// Debounced search
let searchTimeout = null
function debouncedSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    // Search is already reactive via computed
  }, 150)
}

// Watch for color changes
watch(previewColor, (newColor) => {
  emit('update:color', newColor)
  if (selectedIcon.value) {
    emit('select', {
      id: selectedIcon.value.id,
      name: selectedIcon.value.name,
      color: newColor,
      url: getIconUrl(selectedIcon.value.id, { color: newColor, size: 48 })
    })
  }
})

// Watch for external value changes
watch(() => props.modelValue, (newValue) => {
  selectedIconId.value = newValue
})

watch(() => props.color, (newColor) => {
  previewColor.value = newColor
})

onMounted(() => {
  // Focus search input on mount
  setTimeout(() => searchInput.value?.focus(), 100)
})
</script>

<style scoped>
.icon-picker {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.search-container {
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 12px;
  color: #9CA3AF;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 10px 36px;
  background: #1F2937;
  border: 1px solid #374151;
  border-radius: 8px;
  color: #F3F4F6;
  font-size: 14px;
  outline: none;
  transition: border-color 0.2s;
}

.search-input:focus {
  border-color: #6366F1;
}

.search-input::placeholder {
  color: #6B7280;
}

.clear-btn {
  position: absolute;
  right: 8px;
  padding: 4px;
  background: transparent;
  border: none;
  color: #6B7280;
  cursor: pointer;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  color: #F3F4F6;
  background: #374151;
}

.category-tabs {
  display: flex;
  gap: 4px;
  padding: 4px;
  background: #1F2937;
  border-radius: 8px;
}

.category-tab {
  flex: 1;
  padding: 6px 12px;
  background: transparent;
  border: none;
  border-radius: 6px;
  color: #9CA3AF;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.category-tab:hover {
  color: #F3F4F6;
}

.category-tab.active {
  background: #374151;
  color: #F3F4F6;
}

.icons-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(72px, 1fr));
  gap: 8px;
  max-height: 240px;
  overflow-y: auto;
  padding: 4px;
}

.icons-grid::-webkit-scrollbar {
  width: 6px;
}

.icons-grid::-webkit-scrollbar-track {
  background: #1F2937;
  border-radius: 3px;
}

.icons-grid::-webkit-scrollbar-thumb {
  background: #4B5563;
  border-radius: 3px;
}

.icons-grid::-webkit-scrollbar-thumb:hover {
  background: #6B7280;
}

.icon-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 4px;
  background: #1F2937;
  border: 1px solid #374151;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.icon-item:hover {
  background: #374151;
  border-color: #4B5563;
  transform: translateY(-2px);
}

.icon-item.selected {
  background: #312E81;
  border-color: #6366F1;
}

.icon-preview {
  width: 24px;
  height: 24px;
  object-fit: contain;
}

.icon-name {
  font-size: 9px;
  color: #9CA3AF;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.icon-item.selected .icon-name {
  color: #C7D2FE;
}

.empty-state {
  grid-column: 1 / -1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px;
  color: #6B7280;
}

.empty-icon {
  opacity: 0.5;
}

.selected-preview {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #1F2937;
  border: 1px solid #374151;
  border-radius: 8px;
}

.preview-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.preview-icon {
  width: 32px;
  height: 32px;
  object-fit: contain;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.preview-name {
  font-size: 14px;
  font-weight: 500;
  color: #F3F4F6;
}

.preview-id {
  font-size: 11px;
  color: #6B7280;
  font-family: 'SF Mono', Monaco, monospace;
}

.color-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.color-label {
  font-size: 12px;
  font-weight: 500;
  color: #9CA3AF;
}

.color-presets {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.color-preset {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}

.color-preset:hover {
  transform: scale(1.1);
}

.color-preset.active {
  border-color: #F3F4F6;
  box-shadow: 0 0 0 2px #6366F1;
}

.color-input {
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  background: transparent;
}

.color-input::-webkit-color-swatch-wrapper {
  padding: 0;
}

.color-input::-webkit-color-swatch {
  border: 1px solid #4B5563;
  border-radius: 6px;
}
</style>
