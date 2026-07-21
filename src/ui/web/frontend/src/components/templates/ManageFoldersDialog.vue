<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
        @click.self="$emit('close')"
      >
        <div class="w-full max-w-5xl h-[600px] animate-scale-in">
          <div class="finder-window h-full flex flex-col">
            <!-- Titlebar -->
            <div class="finder-titlebar">
              <button @click="$emit('close')" aria-label="Close" class="finder-close-btn" />
              <span class="finder-title">{{ $t('templateFolders.manageFolders') }}</span>
              <div class="w-6" />
            </div>

            <!-- Body: sidebar + content -->
            <div class="flex flex-1 overflow-hidden">
              <!-- Sidebar (FolderTree) -->
              <FolderTree
                :all-sidebar-folders="fm.allSidebarFolders.value"
                :selected-folder-id="fm.selectedFolderId.value"
                :editing-id="fm.editingId.value"
                :edit-name="fm.editName.value"
                :deleting-id="fm.deletingId.value"
                :drag-type="fm.dragType.value"
                :folder-drop-idx="fm.folderDropIdx.value"
                :drag-over-folder-id="fm.dragOverFolderId.value"
                :creating-new="fm.creatingNew.value"
                :new-folder-name="fm.newFolderName.value"
                :new-folder-color="fm.newFolderColor.value"
                :folder-colors="fm.folderColors"
                :get-folder-count="fm.getFolderCount"
                @select-folder="fm.selectFolder"
                @start-edit="fm.startEdit"
                @confirm-rename="fm.confirmRename"
                @cancel-edit="fm.cancelEdit"
                @update:edit-name="fm.editName.value = $event"
                @start-delete="fm.deletingId.value = $event"
                @confirm-delete="fm.confirmDeleteFolder"
                @cancel-delete="fm.deletingId.value = null"
                @folder-drag-start="fm.onFolderDragStart"
                @folder-drag-end="fm.onFolderDragEnd"
                @drag-over-sidebar="fm.onDragOverSidebar"
                @drag-leave-sidebar="fm.onDragLeaveSidebar"
                @drop-sidebar="fm.onDropSidebar"
                @start-create="fm.startCreateFolder"
                @confirm-create="fm.confirmCreateFolder"
                @cancel-create="fm.cancelCreateFolder"
                @update:new-folder-name="fm.newFolderName.value = $event"
                @update:new-folder-color="fm.newFolderColor.value = $event"
              />

              <!-- Content area -->
              <div class="finder-content">
                <!-- Content toolbar -->
                <div class="finder-toolbar">
                  <div class="flex items-center gap-2">
                    <h4 class="text-sm font-semibold text-gray-200">{{ fm.currentFolderName.value }}</h4>
                    <span class="text-xs text-gray-500">{{ fm.currentTemplates.value.length }}</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <!-- Move selected (visible when templates selected) -->
                    <template v-if="fm.selectedTemplateIds.size">
                      <span class="text-[11px] text-gray-500">{{ fm.selectedTemplateIds.size }} {{ $t('batch.selected') }}</span>
                      <button
                        class="finder-toolbar-btn finder-toolbar-btn-primary"
                        aria-label="Move"
                        @click="fm.showMoveMenu.value = !fm.showMoveMenu.value"
                      >
                        <FolderInput :size="14" />
                        <span>{{ $t('templateFolders.move') }}</span>
                      </button>
                      <button
                        class="finder-toolbar-btn"
                        aria-label="Clear selection"
                        @click="fm.clearSelection"
                      >
                        <X :size="14" />
                      </button>
                    </template>
                  </div>
                </div>

                <!-- Move dropdown -->
                <Transition name="dropdown">
                  <div v-if="fm.showMoveMenu.value" class="finder-move-menu">
                    <button
                      v-if="fm.selectedFolderId.value !== '__default__'"
                      class="finder-move-item"
                      @click="fm.moveSelectedTo(null)"
                    >
                      <span class="w-2 h-2 rounded-full bg-purple-500" />
                      {{ $t('templateFolders.defaultFolder') }}
                    </button>
                    <button
                      v-for="folder in folders"
                      :key="folder.id"
                      class="finder-move-item"
                      :class="{ 'opacity-40 pointer-events-none': folder.id === fm.selectedFolderId.value }"
                      @click="fm.moveSelectedTo(folder.id)"
                    >
                      <span class="w-2 h-2 rounded-full" :style="{ background: folder.color || '#8B5CF6' }" />
                      {{ folder.name }}
                    </button>
                  </div>
                </Transition>

                <!-- Template grid -->
                <div class="finder-content-body" @click.self="fm.clearSelection">
                  <div v-if="fm.currentTemplates.value.length" class="finder-grid">
                    <div
                      v-for="tpl in fm.currentTemplates.value"
                      :key="tpl.id || tpl.templateId"
                      class="finder-grid-item"
                      :class="{ 'is-selected': fm.selectedTemplateIds.has(tpl.id || tpl.templateId) }"
                      draggable="true"
                      @click="fm.handleItemClick($event, tpl)"
                      @dragstart="fm.onDragStart($event, tpl)"
                      @dragend="fm.onDragEnd"
                    >
                      <!-- Template icon with image -->
                      <div class="finder-item-icon">
                        <TemplateIcon
                          :icon-url="tpl.iconUrl || tpl.icon_url || tpl.templateIcon || ''"
                          :color="tpl.color || tpl.templateColor"
                          :category="tpl.categorySlug || 'other'"
                          size="lg"
                        />
                        <!-- Selection check -->
                        <div
                          v-if="fm.selectedTemplateIds.has(tpl.id || tpl.templateId)"
                          class="finder-item-check"
                        >
                          <Check :size="10" class="text-white" />
                        </div>
                      </div>
                      <!-- Name -->
                      <p class="finder-item-name" :title="tpl.templateName || tpl.name">
                        {{ tpl.templateName || tpl.name }}
                      </p>
                      <!-- Source badge -->
                      <span
                        v-if="tpl._source"
                        class="finder-item-badge"
                        :class="tpl._source === 'created' ? 'badge-created' : 'badge-installed'"
                      >
                        {{ tpl._source === 'created' ? $t('templateFolders.created') : $t('templateFolders.installed') }}
                      </span>
                    </div>
                  </div>

                  <!-- Empty folder -->
                  <div v-else class="finder-empty">
                    <FolderOpen :size="40" class="text-gray-700 mb-3" />
                    <p class="text-sm text-gray-600">{{ $t('templateFolders.emptyFolder') }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { X, FolderOpen, FolderInput, Check } from 'lucide-vue-next'
import TemplateIcon from '@/components/common/TemplateIcon.vue'
import FolderTree from '@/components/templates/FolderTree.vue'
import { useFolderManager } from '@/composables/useFolderManager'

const props = defineProps({
  show: { type: Boolean, default: false },
  folders: { type: Array, default: () => [] },
  templates: { type: Array, default: () => [] },
  defaultPosition: { type: Number, default: 0 },
})

const emit = defineEmits(['close', 'rename', 'delete', 'create-folder', 'move-templates', 'reorder-folders'])

const fm = useFolderManager(props, emit)
</script>

<style scoped>
/* ========== Finder Window ========== */
.finder-window {
  background: rgba(22, 20, 30, 0.97);
  border: 1px solid rgba(139, 92, 246, 0.12);
  border-radius: 12px;
  overflow: hidden;
  box-shadow:
    0 25px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(139, 92, 246, 0.06),
    0 0 0 0.5px rgba(139, 92, 246, 0.1) inset;
}

/* ========== Titlebar ========== */
.finder-titlebar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 38px;
  padding: 0 14px;
  background: linear-gradient(180deg, rgba(40, 36, 52, 0.98), rgba(30, 28, 40, 0.98));
  border-bottom: 1px solid rgba(139, 92, 246, 0.1);
  flex-shrink: 0;
}

.finder-title {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: -0.01em;
}

.finder-close-btn {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #FF5F57;
  border: none;
  cursor: pointer;
  transition: filter 0.15s;
}
.finder-close-btn:hover { filter: brightness(1.2); }

/* ========== Content ========== */
.finder-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: rgba(18, 16, 26, 0.6);
  position: relative;
}

/* ========== Toolbar ========== */
.finder-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.06);
  flex-shrink: 0;
  background: rgba(28, 26, 36, 0.5);
}

.finder-toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 5px;
  border: 1px solid rgba(139, 92, 246, 0.12);
  background: rgba(139, 92, 246, 0.05);
  color: rgba(255, 255, 255, 0.55);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.15s;
}

.finder-toolbar-btn:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.12);
  color: rgba(255, 255, 255, 0.85);
  border-color: rgba(139, 92, 246, 0.25);
}

.finder-toolbar-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.finder-toolbar-btn-primary {
  border-color: rgba(139, 92, 246, 0.3);
  color: #C4B5FD;
  background: rgba(139, 92, 246, 0.1);
}

.finder-toolbar-btn-primary:hover {
  background: rgba(139, 92, 246, 0.2) !important;
  border-color: rgba(139, 92, 246, 0.5);
}

/* ========== Move Menu ========== */
.finder-move-menu {
  position: absolute;
  top: 44px;
  right: 12px;
  z-index: 20;
  min-width: 180px;
  padding: 4px;
  background: rgba(30, 28, 40, 0.98);
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 8px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
}

.finder-move-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 10px;
  border-radius: 5px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}

.finder-move-item:hover {
  background: rgba(139, 92, 246, 0.2);
  color: #fff;
}

/* ========== Content Body ========== */
.finder-content-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

/* ========== Grid ========== */
.finder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(110px, 1fr));
  gap: 8px;
}

.finder-grid-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 10px 6px 8px;
  border-radius: 10px;
  cursor: default;
  transition: all 0.15s;
  border: 2px solid transparent;
  user-select: none;
}

.finder-grid-item:hover {
  background: rgba(139, 92, 246, 0.05);
}

.finder-grid-item.is-selected {
  background: rgba(139, 92, 246, 0.12);
  border-color: rgba(139, 92, 246, 0.4);
}

.finder-item-icon {
  position: relative;
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(139, 92, 246, 0.06);
  border: 1px solid rgba(139, 92, 246, 0.1);
}

.finder-item-check {
  position: absolute;
  bottom: 3px;
  right: 3px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #8B5CF6, #6D28D9);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
}

.finder-item-name {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.75);
  text-align: center;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.3;
}

.finder-item-badge {
  font-size: 9px;
  font-weight: 600;
  padding: 0 4px;
  border-radius: 3px;
  line-height: 1.5;
}

.badge-created {
  background: rgba(139, 92, 246, 0.2);
  color: #C4B5FD;
}

.badge-installed {
  background: rgba(59, 130, 246, 0.2);
  color: #93C5FD;
}

/* ========== Empty ========== */
.finder-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}

/* ========== Transitions ========== */
.fade-enter-active { transition: opacity 0.2s ease; }
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.dropdown-enter-active { transition: all 0.15s ease; }
.dropdown-leave-active { transition: all 0.1s ease; }
.dropdown-enter-from, .dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.animate-scale-in {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
