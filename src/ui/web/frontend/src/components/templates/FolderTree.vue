<template>
  <div class="finder-sidebar">
    <div class="px-3 pt-2 pb-1">
      <p class="finder-sidebar-label">{{ $t('templateFolders.manageFolders') }}</p>
    </div>

    <!-- All folders (default + user, all reorderable) -->
    <div
      v-for="(folder, idx) in allSidebarFolders"
      :key="folder.id"
      class="group relative"
      @dragover.prevent="$emit('drag-over-sidebar', $event, folder.id, idx)"
      @dragleave="$emit('drag-leave-sidebar')"
      @drop.prevent="$emit('drop-sidebar', folder.id, idx)"
    >
      <!-- Drop indicator line -->
      <div
        v-if="folderDropIdx === idx && dragType === 'folder'"
        class="finder-drop-line"
      />

      <!-- Delete confirm mode -->
      <div v-if="deletingId === folder.id" class="finder-delete-confirm">
        <p class="text-[12px] text-red-300/80 text-center truncate">{{ $t('templateFolders.delete') }}{{ folder.name }}</p>
        <div class="flex items-center justify-center gap-3">
          <button @click="$emit('confirm-delete', folder)" aria-label="Confirm delete" class="p-1 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded transition-colors">
            <Check :size="14" />
          </button>
          <button @click="$emit('cancel-delete')" aria-label="Cancel delete" class="p-1 text-gray-500 hover:text-gray-300 hover:bg-white/5 rounded transition-colors">
            <X :size="14" />
          </button>
        </div>
      </div>

      <!-- Rename mode -->
      <div v-else-if="editingId === folder.id" class="flex items-center gap-1 px-3 py-1">
        <span class="finder-sidebar-dot" :style="{ background: folder.color || '#8B5CF6' }" />
        <input
          ref="editInput"
          :value="editName"
          type="text"
          class="flex-1 min-w-0 px-1.5 py-0.5 text-[13px] bg-gray-700 border border-purple-500 rounded text-white focus:outline-none"
          @input="$emit('update:edit-name', $event.target.value)"
          @keydown.enter="$emit('confirm-rename', folder)"
          @keydown.escape="$emit('cancel-edit')"
        />
        <button @click="$emit('confirm-rename', folder)" aria-label="Confirm rename" class="p-0.5 text-emerald-400 hover:text-emerald-300">
          <Check :size="12" />
        </button>
        <button @click="$emit('cancel-edit')" aria-label="Cancel rename" class="p-0.5 text-gray-500 hover:text-gray-300">
          <X :size="12" />
        </button>
      </div>

      <!-- Normal mode -->
      <button
        v-else
        class="finder-sidebar-item"
        :class="{
          'is-active': selectedFolderId === folder.id,
          'is-drop-target': dragOverFolderId === folder.id && dragType === 'template'
        }"
        draggable="true"
        @click="$emit('select-folder', folder.id)"
        @dblclick="folder.id !== '__default__' && $emit('start-edit', folder)"
        @dragstart="$emit('folder-drag-start', $event, folder.id, idx)"
        @dragend="$emit('folder-drag-end')"
      >
        <!-- Drag handle -->
        <GripVertical :size="12" class="folder-grip" />
        <span class="finder-sidebar-dot" :style="{ background: folder.color || '#8B5CF6' }" />
        <span class="truncate">{{ folder.name }}</span>
        <span class="finder-sidebar-count">{{ getFolderCount(folder) }}</span>

        <!-- Hover actions (not for default) -->
        <div v-if="folder.id !== '__default__'" class="finder-sidebar-actions">
          <button
            @click.stop="$emit('start-edit', folder)"
            class="p-0.5 text-gray-500 hover:text-purple-400"
            :title="$t('templateFolders.rename')"
          >
            <Pencil :size="11" />
          </button>
          <button
            @click.stop="$emit('start-delete', folder.id)"
            class="p-0.5 text-gray-500 hover:text-red-400"
            :title="$t('templateFolders.delete')"
          >
            <Trash2 :size="11" />
          </button>
        </div>
      </button>

      <!-- Drop indicator line (after last item) -->
      <div
        v-if="folderDropIdx === idx + 1 && dragType === 'folder' && idx === allSidebarFolders.length - 1"
        class="finder-drop-line"
      />
    </div>

    <!-- Inline New Folder -->
    <div class="mt-auto border-t border-white/5">
      <div v-if="creatingNew" class="px-2 py-3 space-y-3">
        <!-- Input -->
        <input
          ref="newFolderInput"
          :value="newFolderName"
          type="text"
          :placeholder="$t('templateFolders.folderName')"
          class="w-full px-3 py-1.5 text-[13px] bg-gray-700/80 border border-purple-500/40 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-400 focus:ring-1 focus:ring-purple-500/30 transition-all"
          @input="$emit('update:new-folder-name', $event.target.value)"
          @keydown.enter="$emit('confirm-create')"
          @keydown.escape="$emit('cancel-create')"
        />
        <!-- Color picker -->
        <div class="flex items-center justify-center gap-2">
          <button
            v-for="c in folderColors"
            :key="c"
            class="color-dot"
            :class="{ 'is-selected': newFolderColor === c }"
            :style="{ '--dot-color': c }"
            @click="$emit('update:new-folder-color', c)"
          >
            <Check v-if="newFolderColor === c" :size="9" class="text-white" />
          </button>
        </div>
        <!-- Confirm / Cancel -->
        <div class="flex items-center justify-center gap-3">
          <button @click="$emit('confirm-create')" aria-label="Confirm create" class="p-1.5 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 rounded-lg transition-colors" :disabled="!newFolderName.trim()">
            <Check :size="16" />
          </button>
          <button @click="$emit('cancel-create')" aria-label="Cancel create" class="p-1.5 text-gray-500 hover:text-gray-300 hover:bg-white/5 rounded-lg transition-colors">
            <X :size="16" />
          </button>
        </div>
      </div>
      <button
        v-else
        @click="$emit('start-create')"
        aria-label="New folder"
        class="finder-sidebar-item text-gray-500 hover:text-purple-400"
        style="width: calc(100% - 16px); margin: 6px 8px;"
      >
        <FolderPlus :size="14" />
        <span>{{ $t('templateFolders.newFolder') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Check, X, GripVertical, Pencil, Trash2, FolderPlus } from 'lucide-vue-next'

defineProps({
  allSidebarFolders: { type: Array, default: () => [] },
  selectedFolderId: { type: String, default: '__default__' },
  editingId: { type: [String, null], default: null },
  editName: { type: String, default: '' },
  deletingId: { type: [String, null], default: null },
  dragType: { type: [String, null], default: null },
  folderDropIdx: { type: [Number, null], default: null },
  dragOverFolderId: { type: [String, null], default: null },
  creatingNew: { type: Boolean, default: false },
  newFolderName: { type: String, default: '' },
  newFolderColor: { type: String, default: '#8B5CF6' },
  folderColors: { type: Array, default: () => [] },
  getFolderCount: { type: Function, required: true },
})

defineEmits([
  'select-folder', 'start-edit', 'confirm-rename', 'cancel-edit',
  'start-delete', 'confirm-delete', 'cancel-delete',
  'folder-drag-start', 'folder-drag-end',
  'drag-over-sidebar', 'drag-leave-sidebar', 'drop-sidebar',
  'start-create', 'confirm-create', 'cancel-create',
  'update:edit-name', 'update:new-folder-name', 'update:new-folder-color',
])
</script>

<style scoped>
/* ========== Sidebar ========== */
.finder-sidebar {
  width: 240px;
  min-width: 240px;
  background: rgba(28, 26, 36, 0.8);
  border-right: 1px solid rgba(139, 92, 246, 0.08);
  overflow-y: auto;
  padding: 4px 0;
  display: flex;
  flex-direction: column;
}

.finder-sidebar-label {
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: rgba(216, 200, 255, 0.8);
  font-weight: 600;
  padding: 0 8px;
  margin-bottom: 4px;
}

.finder-sidebar-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: calc(100% - 12px);
  margin: 0 6px;
  padding: 5px 8px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  text-align: left;
}

.finder-sidebar-item:hover {
  background: rgba(139, 92, 246, 0.08);
}

.finder-sidebar-item.is-active {
  background: rgba(139, 92, 246, 0.2);
  color: #fff;
}

.finder-sidebar-item.is-drop-target {
  background: rgba(139, 92, 246, 0.3);
  outline: 2px solid rgba(139, 92, 246, 0.6);
  outline-offset: -2px;
}

.finder-sidebar-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 4px rgba(0, 0, 0, 0.2);
}

.finder-sidebar-count {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.25);
  margin-left: auto;
  flex-shrink: 0;
}

.finder-sidebar-actions {
  display: none;
  align-items: center;
  gap: 2px;
  margin-left: auto;
  flex-shrink: 0;
}

.group:hover .finder-sidebar-actions {
  display: flex;
}

.group:hover .finder-sidebar-count {
  display: none;
}

/* Drag handle */
.folder-grip {
  color: rgba(255, 255, 255, 0.12);
  flex-shrink: 0;
  cursor: grab;
  transition: color 0.15s;
}

.finder-sidebar-item:hover .folder-grip {
  color: rgba(255, 255, 255, 0.35);
}

.finder-sidebar-item:active .folder-grip {
  cursor: grabbing;
}

/* Inline delete confirm */
.finder-delete-confirm {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 1px 6px;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.12);
}

/* Drop indicator line */
.finder-drop-line {
  height: 2px;
  margin: 0 10px;
  background: linear-gradient(90deg, #8B5CF6, #3B82F6);
  border-radius: 1px;
  box-shadow: 0 0 6px rgba(139, 92, 246, 0.4);
  pointer-events: none;
}

/* ========== Color Picker ========== */
.color-dot {
  width: 20px;
  height: 20px;
  min-width: 20px;
  min-height: 20px;
  aspect-ratio: 1;
  border-radius: 50%;
  background: var(--dot-color);
  border: 2.5px solid transparent;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.color-dot:hover {
  transform: scale(1.15);
  box-shadow: 0 0 10px rgba(139, 92, 246, 0.3);
}

.color-dot.is-selected {
  border-color: rgba(255, 255, 255, 0.85);
  transform: scale(1.15);
  box-shadow: 0 0 12px rgba(139, 92, 246, 0.4);
}
</style>
