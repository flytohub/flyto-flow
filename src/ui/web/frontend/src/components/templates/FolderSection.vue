<template>
  <div class="folder-section" :class="{ 'is-expanded': expanded }">
    <!-- Header Row -->
    <div class="folder-header-wrap">
      <button
        class="folder-header"
        @click="$emit('toggle', folder.id)"
      >
        <!-- Chevron -->
        <div class="folder-chevron" :class="{ 'rotate-90': expanded }">
          <ChevronRight :size="16" />
        </div>

        <!-- Color Dot -->
        <span
          class="folder-dot"
          :style="{ background: folder.color || '#8B5CF6' }"
        />

        <!-- Folder Name -->
        <span class="folder-name">{{ folder.name }}</span>

        <!-- Template Count -->
        <span class="folder-count">{{ templates.length }}</span>
      </button>

      <!-- Actions (non-default folders only) -->
      <div v-if="folder.id !== '__default__'" class="folder-actions">
        <button
          @click.stop="$emit('rename', folder)"
          class="folder-action-btn"
          :title="$t('templateFolders.rename')"
        >
          <Pencil :size="13" />
        </button>
        <button
          @click.stop="$emit('delete', folder)"
          class="folder-action-btn folder-action-delete"
          :title="$t('templateFolders.delete')"
        >
          <Trash2 :size="13" />
        </button>
      </div>
    </div>

    <!-- Body (animated expand/collapse) -->
    <Transition
      name="folder-expand"
      @before-enter="onBeforeEnter"
      @enter="onEnter"
      @after-enter="onAfterEnter"
      @before-leave="onBeforeLeave"
      @leave="onLeave"
      @after-leave="onAfterLeave"
    >
      <div v-if="expanded" class="folder-body">
        <!-- Empty state -->
        <div v-if="!templates.length" class="folder-empty">
          <Folder :size="20" class="text-gray-500" />
          <span class="text-sm text-gray-500">{{ $t('templateFolders.emptyFolder') }}</span>
        </div>

        <!-- Grid View -->
        <div
          v-else-if="viewMode === 'grid'"
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5"
        >
          <slot name="template-card" v-for="tpl in templates" :template="tpl" :key="tpl.templateId || tpl.id" />
        </div>

        <!-- List View -->
        <div v-else class="space-y-2">
          <slot name="template-list" v-for="tpl in templates" :template="tpl" :key="tpl.templateId || tpl.id" />
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ChevronRight, Folder, Pencil, Trash2 } from 'lucide-vue-next'

defineProps({
  folder: {
    type: Object,
    required: true
  },
  templates: {
    type: Array,
    default: () => []
  },
  expanded: {
    type: Boolean,
    default: false
  },
  viewMode: {
    type: String,
    default: 'grid'
  },
})

defineEmits(['toggle', 'rename', 'delete'])

// Smooth height animation helpers
function onBeforeEnter(el) {
  el.style.height = '0'
  el.style.opacity = '0'
}
function onEnter(el) {
  el.style.transition = 'height 0.3s ease, opacity 0.3s ease'
  el.style.height = el.scrollHeight + 'px'
  el.style.opacity = '1'
}
function onAfterEnter(el) {
  el.style.height = 'auto'
}
function onBeforeLeave(el) {
  el.style.height = el.scrollHeight + 'px'
  el.style.opacity = '1'
}
function onLeave(el) {
  // Force reflow
  el.offsetHeight // eslint-disable-line no-unused-expressions
  el.style.transition = 'height 0.25s ease, opacity 0.2s ease'
  el.style.height = '0'
  el.style.opacity = '0'
}
function onAfterLeave(el) {
  el.style.height = ''
  el.style.opacity = ''
}
</script>

<style scoped>
.folder-section {
  border: 1px solid rgba(107, 114, 128, 0.2);
  border-radius: 12px;
  overflow: visible;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
  background: rgba(255, 255, 255, 0.02);
}

.folder-section.is-expanded {
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.06);
}

.folder-header-wrap {
  display: flex;
  align-items: center;
}

.folder-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  padding: 12px 16px;
  background: transparent;
  border: none;
  cursor: pointer;
  color: inherit;
  font-size: 14px;
  transition: background 0.2s ease;
}

.folder-header:hover {
  background: rgba(139, 92, 246, 0.06);
}

.folder-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  padding-right: 12px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.folder-header-wrap:hover .folder-actions {
  opacity: 1;
}

.folder-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: #6B7280;
  cursor: pointer;
  transition: all 0.15s ease;
}

.folder-action-btn:hover {
  color: #A78BFA;
  background: rgba(139, 92, 246, 0.1);
}

.folder-action-delete:hover {
  color: #F87171;
  background: rgba(239, 68, 68, 0.1);
}

.folder-chevron {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9CA3AF;
  transition: transform 0.25s ease, color 0.2s ease;
  flex-shrink: 0;
}

.is-expanded .folder-chevron {
  color: #8B5CF6;
}

.folder-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.15);
}

.folder-name {
  font-weight: 600;
  color: #E5E7EB;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.folder-count {
  font-size: 12px;
  color: #6B7280;
  background: rgba(107, 114, 128, 0.15);
  padding: 1px 8px;
  border-radius: 10px;
  flex-shrink: 0;
}

.folder-body {
  padding: 8px 16px 16px;
}

.folder-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 24px;
  opacity: 0.6;
}
</style>
