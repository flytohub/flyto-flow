<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="show"
        class="fixed inset-0 z-50 flex items-center justify-center p-4"
        @click.self="$emit('cancel')"
      >
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" />

        <!-- Dialog -->
        <div class="move-dialog animate-scale-in">
          <!-- Header -->
          <div class="move-header">
            <div class="flex items-center gap-3">
              <div class="move-header-icon">
                <FolderInput :size="18" />
              </div>
              <h3 class="text-base font-semibold text-white">
                {{ $t('templateFolders.moveToFolder') }}
              </h3>
            </div>
            <button @click="$emit('cancel')" aria-label="Close" class="move-close-btn">
              <X :size="16" />
            </button>
          </div>

          <!-- Folder List -->
          <div class="move-body">
            <!-- Root option -->
            <button
              @click="selected = null"
              class="move-folder-item"
              :class="{ 'is-active': selected === null }"
            >
              <div class="move-folder-dot" style="background: #8B5CF6" />
              <Home :size="16" class="text-gray-400" />
              <span class="move-folder-name">{{ $t('templateFolders.root') }}</span>
              <ChevronRight v-if="selected === null" :size="14" class="ml-auto text-purple-400" />
            </button>

            <!-- Divider -->
            <div v-if="flatFolders.length" class="move-divider" />

            <!-- Folders -->
            <template v-for="folder in flatFolders" :key="folder.id">
              <button
                @click="selected = folder.id"
                class="move-folder-item"
                :class="{ 'is-active': selected === folder.id }"
                :style="{ '--folder-depth': folder.depth }"
                :title="folder.pathLabel"
              >
                <div class="move-folder-dot" :style="{ background: folder.color || '#8B5CF6' }" />
                <Folder :size="folder.depth > 0 ? 14 : 16" class="text-gray-400" />
                <span class="move-folder-name">{{ folder.name }}</span>
                <ChevronRight v-if="selected === folder.id" :size="14" class="ml-auto text-purple-400" />
              </button>
            </template>

            <!-- Empty -->
            <div v-if="!folders.length" class="move-empty">
              <FolderPlus :size="20" class="text-gray-600" />
              <p class="text-sm text-gray-500">{{ $t('templateFolders.emptyFolder') }}</p>
            </div>
          </div>

          <!-- Footer -->
          <div class="move-footer">
            <button @click="$emit('cancel')" class="move-btn-cancel">
              {{ $t('common.cancel') }}
            </button>
            <button @click="$emit('confirm', selected)" class="move-btn-confirm">
              <FolderInput :size="15" />
              {{ selected === null ? $t('templateFolders.moveToRoot') : $t('templateFolders.moveToFolder') }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { X, Home, Folder, FolderInput, FolderPlus, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  show: Boolean,
  folders: { type: Array, default: () => [] }
})

defineEmits(['confirm', 'cancel'])

const selected = ref(null)

watch(() => props.show, (v) => {
  if (v) selected.value = null
})

function sortFolders(items) {
  return [...items].sort((a, b) => {
    const order = (a.order ?? 0) - (b.order ?? 0)
    if (order !== 0) return order
    return String(a.name || '').localeCompare(String(b.name || ''))
  })
}

function folderParentId(folder) {
  return folder?.parent_id ?? folder?.parentId ?? null
}

const flatFolders = computed(() => {
  const childrenByParent = new Map()
  props.folders.forEach(folder => {
    const parentId = folderParentId(folder)
    if (!childrenByParent.has(parentId)) childrenByParent.set(parentId, [])
    childrenByParent.get(parentId).push(folder)
  })
  childrenByParent.forEach((children, parentId) => {
    childrenByParent.set(parentId, sortFolders(children))
  })

  const flatten = (parentId = null, depth = 0, parentPath = []) => {
    const children = childrenByParent.get(parentId) || []
    return children.flatMap(folder => {
      const path = Array.isArray(folder.path) && folder.path.length
        ? folder.path
        : [...parentPath, folder.name].filter(Boolean)
      return [
        {
          ...folder,
          depth,
          path,
          pathLabel: path.join(' / '),
        },
        ...flatten(folder.id, depth + 1, path),
      ]
    })
  }
  return flatten()
})
</script>

<style scoped>
.move-dialog {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  background: #111827;
  border: 1px solid rgba(139, 92, 246, 0.15);
  border-radius: 16px;
  overflow: hidden;
  box-shadow:
    0 25px 60px rgba(0, 0, 0, 0.5),
    0 0 40px rgba(139, 92, 246, 0.08);
}

/* Header */
.move-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.move-header-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: rgba(139, 92, 246, 0.15);
  color: #A78BFA;
}

.move-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: rgba(156, 163, 175, 0.6);
  cursor: pointer;
  transition: all 0.2s ease;
}

.move-close-btn:hover {
  color: #F87171;
  background: rgba(239, 68, 68, 0.1);
}

/* Body */
.move-body {
  padding: 12px;
  max-height: 360px;
  overflow-y: auto;
}

.move-body::-webkit-scrollbar { width: 4px; }
.move-body::-webkit-scrollbar-track { background: transparent; }
.move-body::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.2); border-radius: 4px; }

/* Folder items */
.move-folder-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px 10px calc(14px + (var(--folder-depth, 0) * 22px));
  border-radius: 10px;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  color: #D1D5DB;
  font-size: 14px;
}

.move-folder-item:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(255, 255, 255, 0.06);
}

.move-folder-item.is-active {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.25);
  color: #E9D5FF;
}

.move-folder-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px rgba(0, 0, 0, 0.2);
}

.move-folder-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.move-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.04);
  margin: 6px 14px;
}

.move-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 32px 16px;
}

/* Footer */
.move-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.move-btn-cancel {
  padding: 8px 16px;
  font-size: 13px;
  font-weight: 500;
  color: #9CA3AF;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.move-btn-cancel:hover {
  color: #D1D5DB;
  border-color: rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.03);
}

.move-btn-confirm {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 18px;
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #7C3AED, #6D28D9);
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.move-btn-confirm:hover {
  background: linear-gradient(135deg, #8B5CF6, #7C3AED);
  box-shadow: 0 4px 16px rgba(139, 92, 246, 0.3);
  transform: translateY(-1px);
}

/* Animations */
.animate-scale-in {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-enter-active { transition: opacity 0.2s ease; }
.modal-leave-active { transition: opacity 0.15s ease; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
</style>
