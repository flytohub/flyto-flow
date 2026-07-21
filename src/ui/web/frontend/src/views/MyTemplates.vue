<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
    <!-- Hero Section -->
    <WaveHero size="medium">
      <div class="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
        <div>
          <h1 class="text-3xl sm:text-4xl font-bold text-white mb-2">{{ $t('myTemplates.title') }}</h1>
          <p class="text-gray-300">{{ $t('myTemplates.subtitle') }}</p>
        </div>
        <div class="flex items-center gap-3">
          <!-- Join Collaboration -->
          <div class="relative">
            <!-- Trigger Button (invisible when panel open, keeps layout size) -->
            <button
              @click="joinCollab.showJoinInput.value = true"
              class="join-trigger-btn group"
              :class="{ 'invisible': joinCollab.showJoinInput.value }"
            >
              <span class="join-trigger-glow" />
              <UserPlus :size="16" class="relative z-10" />
              <span class="relative z-10">{{ $t('myTemplates.joinCollaboration') }}</span>
            </button>

            <!-- Expanded Panel (overlays the button position) -->
            <Transition name="join-panel">
              <div v-if="joinCollab.showJoinInput.value" class="join-panel">
                <div class="join-panel-inner">
                  <!-- Input with glow -->
                  <div class="join-input-wrap" :class="{ 'has-error': joinCollab.joinError.value, 'is-success': joinCollab.joinSuccess.value }">
                    <UserPlus :size="14" class="join-input-icon" />
                    <AppInput
                      :ref="el => joinCollab.joinInputRef.value = el"
                      v-model="joinCollab.joinCode.value"
                      @keydown="e => { if (e.key === 'Enter') joinCollab.handleJoinCollaboration() }"
                      :placeholder="$t('collaboration.invite.enterCode')"
                      class="join-input"
                      :disabled="joinCollab.isJoiningCollab.value"
                    />
                  </div>

                  <!-- Submit -->
                  <button
                    @click="joinCollab.handleJoinCollaboration()"
                    :disabled="!joinCollab.joinCode.value.trim() || joinCollab.isJoiningCollab.value"
                    class="join-submit-btn"
                  >
                    <Loader2 v-if="joinCollab.isJoiningCollab.value" :size="16" class="animate-spin" />
                    <CheckCircle2 v-else-if="joinCollab.joinSuccess.value" :size="16" />
                    <ArrowRight v-else :size="16" />
                  </button>

                  <!-- Close -->
                  <button
                    @click="joinCollab.closeJoinPanel()"
                    class="join-close-btn"
                    aria-label="Close"
                  >
                    <X :size="14" />
                  </button>
                </div>

                <!-- Feedback message -->
                <Transition name="join-msg">
                  <p v-if="joinCollab.joinError.value" class="join-feedback join-feedback-error">
                    <AlertCircle :size="12" />
                    <span>{{ joinCollab.joinError.value }}</span>
                  </p>
                  <p v-else-if="joinCollab.joinSuccess.value" class="join-feedback join-feedback-success">
                    <CheckCircle2 :size="12" />
                    <span>{{ $t('myTemplates.join.success') }}</span>
                  </p>
                </Transition>
              </div>
            </Transition>
          </div>
          <!-- Import Warroom Recipes -->
          <button
            @click="warroomImport.openDialog"
            class="px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white font-medium rounded-lg transition-all flex items-center gap-2 w-fit"
          >
            <FolderInput :size="18" />
            Import Warroom Recipes
          </button>
          <!-- Import YAML -->
          <button
            @click="triggerImportYAML"
            class="px-5 py-2.5 bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 hover:text-white font-medium rounded-lg transition-all flex items-center gap-2 w-fit"
          >
            <FileUp :size="18" />
            {{ $t('myTemplates.importYaml', 'Import YAML') }}
          </button>
          <input
            ref="yamlFileInput"
            type="file"
            accept=".yaml,.yml"
            class="hidden"
            @change="handleImportYAML"
          />
          <!-- New Template -->
          <button
            @click="actions.createTemplate"
            class="px-5 py-2.5 bg-gradient-to-r from-purple-600 to-blue-600 text-white font-medium rounded-lg transition-all hover:shadow-lg hover:shadow-purple-500/30 flex items-center gap-2 w-fit"
          >
            <Plus :size="18" />
            {{ $t('myTemplates.newTemplate') }}
          </button>
        </div>
      </div>

      <!-- Stats -->
      <div class="flex flex-wrap items-center gap-6 mt-8 pt-6 border-t border-white/10">
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-purple-400"></div>
          <span class="text-sm text-gray-400">{{ $t('myTemplates.stats.total') }}</span>
          <span class="text-lg font-semibold text-white">{{ store.stats.totalCount }}</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-emerald-400"></div>
          <span class="text-sm text-gray-400">{{ $t('myTemplates.stats.published') }}</span>
          <span class="text-lg font-semibold text-emerald-400">{{ store.stats.publishedCount }}</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-amber-400"></div>
          <span class="text-sm text-gray-400">{{ $t('myTemplates.stats.drafts') }}</span>
          <span class="text-lg font-semibold text-amber-400">{{ store.stats.draftCount }}</span>
        </div>
        <div class="flex items-center gap-2">
          <div class="w-2 h-2 rounded-full bg-blue-400"></div>
          <span class="text-sm text-gray-400">{{ $t('myTemplates.stats.installed') }}</span>
          <span class="text-lg font-semibold text-blue-400">{{ store.stats.installedCount }}</span>
        </div>
      </div>
    </WaveHero>

    <!-- File Manager Layout -->
    <main class="container px-4 py-6">
      <div class="fm-layout">
        <!-- Left: Folder Sidebar -->
        <aside class="fm-sidebar">
          <div class="fm-sidebar-header">
            <span class="fm-sidebar-title">{{ $t('templateFolders.folders', 'Folders') }}</span>
            <button
              @click="folderActions.showCreateFolderDialog.value = true"
              class="fm-sidebar-add"
              :title="$t('templateFolders.newFolder')"
            >
              <FolderPlus :size="14" />
            </button>
          </div>

          <nav class="fm-folder-list">
            <button
              v-for="folder in store.folderList"
              :key="folder.id"
              class="fm-folder-item"
              :class="{ 'fm-folder-active': store.selectedFolderId === folder.id }"
              :style="{ '--folder-depth': folder.depth || 0 }"
              :title="folder.pathLabel || folder.name"
              @click="store.selectFolder(folder.id)"
              @contextmenu.prevent="!folder.isVirtual && handleFolderRename(folder)"
            >
              <span
                class="fm-folder-tree-glyph"
                role="button"
                :tabindex="folder.hasChildren ? 0 : -1"
                :aria-label="folder.hasChildren ? `${store.expandedFolders.has(folder.id) ? 'Collapse' : 'Expand'} ${folder.name}` : undefined"
                @click.stop="folder.hasChildren && store.toggleFolder(folder.id)"
                @keydown.enter.stop.prevent="folder.hasChildren && store.toggleFolder(folder.id)"
                @keydown.space.stop.prevent="folder.hasChildren && store.toggleFolder(folder.id)"
              >
                <ChevronDown v-if="folder.hasChildren && store.expandedFolders.has(folder.id)" :size="13" />
                <ChevronRight v-else-if="folder.hasChildren" :size="13" />
              </span>
              <div class="fm-folder-icon" :style="{ color: folder.color || '#8B5CF6' }">
                <FolderOpen v-if="store.selectedFolderId === folder.id" :size="16" />
                <Folder v-else :size="16" />
              </div>
              <span class="fm-folder-name">{{ folder.name }}</span>
              <span class="fm-folder-count">{{ folder.count ?? 0 }}</span>
              <button
                v-if="!folder.isVirtual"
                class="fm-folder-menu"
                @click.stop="handleFolderRename(folder)"
              >
                <MoreHorizontal :size="14" />
              </button>
            </button>
          </nav>

          <!-- Sidebar Footer -->
          <div class="fm-sidebar-footer">
            <button
              @click="openManageDialog"
              class="fm-manage-btn"
            >
              <Settings :size="14" />
              {{ $t('templateFolders.manageFolders') }}
            </button>
          </div>
        </aside>

        <!-- Right: Template Content -->
        <section class="fm-content">
          <!-- Toolbar -->
          <div class="fm-toolbar">
            <TemplateToolbar
              v-model:search-query="store.searchQuery"
              v-model:sort-by="store.sortBy"
              v-model:view-mode="viewMode"
              :selection-mode="selection.isSelectionMode.value"
              :show-select-button="store.allTemplates.length > 0"
              @enter-selection-mode="selection.enterSelectionMode"
              @select-all="selection.selectAll"
            />
          </div>

          <!-- Tag Filter Bar -->
          <TemplateFilters
            :available-tags="availableTags"
            :selected-tags="selectedTags"
            @toggle-tag="toggleTagFilter"
            @clear-tags="selectedTags = []"
          />

          <!-- Loading -->
          <div v-if="store.loading" class="fm-loading">
            <Loader2 :size="24" class="animate-spin text-purple-400" />
          </div>

          <!-- Error -->
          <div v-else-if="store.error" class="fm-error">
            <AlertCircle :size="20" />
            <span>{{ store.error }}</span>
            <button @click="store.fetchTemplates()" class="fm-retry-btn">Retry</button>
          </div>

          <!-- Empty -->
          <div v-else-if="store.templates.length === 0" class="fm-empty">
            <FolderOpen :size="48" class="text-gray-600" />
            <p class="text-gray-400">{{ store.searchQuery ? $t('common.noSearchResults') : $t('myTemplates.emptyState') }}</p>
            <div class="flex gap-3 mt-4">
              <button @click="actions.createTemplate()" class="fm-action-btn fm-action-primary">
                <Plus :size="16" /> {{ $t('myTemplates.newTemplate') }}
              </button>
              <button @click="actions.goToMarketplace()" class="fm-action-btn">
                {{ $t('myTemplates.browseMarketplace') }}
              </button>
            </div>
          </div>

          <!-- Template Grid -->
          <TemplateGrid
            v-else
            :error="null"
            :loading="false"
            :view-mode="viewMode"
            :folder-sections="flatSection"
            :expanded-folders="alwaysExpanded"
            :search-query="store.searchQuery"
            :open-menu-id="actions.openMenuId.value"
            :selection-mode="selection.isSelectionMode.value"
            :selected-ids="selection.selectedIds.value"
            @retry="store.fetchTemplates()"
            @toggle-folder="() => {}"
            @folder-rename="handleFolderRename"
            @folder-delete="handleFolderDelete"
            @open="actions.openTemplate"
            @edit="actions.editTemplate"
            @duplicate="actions.duplicateTemplate"
            @run="actions.runTemplate"
            @delete="actions.deleteTemplate"
            @toggle-menu="actions.toggleMenu"
            @publish="actions.publishTemplate"
            @manage-keys="actions.manageKeys"
            @toggle-select="selection.toggleSelect"
            @fork="actions.forkTemplate"
            @sync="actions.syncTemplate"
            @update-auto-update="actions.handleUpdateAutoUpdate"
            @submit-pr="openPRForm"
            @move-to-folder="(t) => folderActions.openMoveToFolder(t.id)"
            @create="actions.createTemplate()"
            @browse-marketplace="actions.goToMarketplace()"
          />

          <!-- Pagination -->
          <div v-if="store.totalFiltered > store.pageSize" class="fm-pagination">
            <button
              :disabled="store.page <= 1"
              @click="store.prevPage()"
              class="fm-page-btn"
            >
              <ChevronLeft :size="16" />
            </button>
            <span class="fm-page-info">
              {{ (store.page - 1) * store.pageSize + 1 }}–{{ Math.min(store.page * store.pageSize, store.totalFiltered) }}
              / {{ store.totalFiltered }}
            </span>
            <button
              :disabled="!store.hasNext"
              @click="store.nextPage()"
              class="fm-page-btn"
            >
              <ChevronRight :size="16" />
            </button>
          </div>
        </section>
      </div>
    </main>

    <!-- Modals -->
    <CreateTemplateModal
      v-model="actions.showCreateModal.value"
      :folders="store.folders"
      @created="actions.onTemplateCreated"
    />

    <EditTemplateModal
      v-model="actions.showEditModal.value"
      :template="actions.editTarget.value"
      @updated="actions.onTemplateUpdated"
    />

    <ConfirmDialog
      :show="actions.showDeleteDialog.value"
      :title="$t('myTemplates.deleteDialog.title')"
      :message="$t('myTemplates.deleteDialog.message', { name: actions.deleteTarget.value?.templateName || actions.deleteTarget.value?.name || '' })"
      :confirm-text="$t('common.delete')"
      variant="danger"
      :loading="actions.deleting.value"
      @confirm="actions.confirmDelete"
      @cancel="actions.cancelDelete"
    />

    <PublishTemplateModal
      v-model="actions.showPublishModal.value"
      :template="actions.publishTarget.value"
      @published="actions.onTemplatePublished"
    />

    <InviteKeyManager
      v-model="actions.showKeyManager.value"
      :template="actions.keyManagerTarget.value"
    />

    <!-- Batch Delete Confirm -->
    <ConfirmDialog
      :show="selection.showBatchDeleteDialog.value"
      :title="$t('batch.deleteConfirm.title', { count: selection.selectedIds.value.size })"
      :message="$t('batch.deleteConfirm.message', { count: selection.selectedIds.value.size })"
      :confirm-text="$t('common.delete')"
      variant="danger"
      :loading="selection.batchDeleting.value"
      @confirm="selection.confirmBatchDelete"
      @cancel="selection.cancelBatchDelete"
    />

    <!-- Batch Action Bar -->
    <BatchActionBar
      :selected-count="selection.selectedIds.value.size"
      :total-count="store.allTemplates.length"
      :deleting="selection.batchDeleting.value"
      @select-all="selection.selectAll"
      @deselect-all="selection.deselectAll"
      @batch-delete="selection.handleBatchDelete"
      @cancel="selection.cancel"
    />

    <!-- Submit PR Dialog -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="showPRForm"
          class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
          @click.self="showPRForm = false"
        >
          <div class="w-full max-w-lg animate-scale-in">
            <PullRequestForm
              :fork-id="prFormTarget?.forkId || prFormTarget?.id || ''"
              :submitting="prSubmitting"
              @submit="handleSubmitPR"
              @cancel="showPRForm = false; prFormTarget = null"
            />
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Create Folder Dialog -->
    <CreateFolderDialog
      :show="folderActions.showCreateFolderDialog.value"
      :loading="folderActions.creatingFolder.value"
      @confirm="folderActions.handleCreateFolder"
      @cancel="folderActions.showCreateFolderDialog.value = false"
    />

    <!-- Rename Folder Dialog -->
    <ConfirmDialog
      :show="folderActions.showRenameFolderDialog.value"
      :title="$t('templateFolders.rename', 'Rename Folder')"
      message=" "
      :confirm-text="$t('common.save', 'Save')"
      :loading="folderActions.renamingFolder.value"
      @confirm="folderActions.handleRenameFolder"
      @cancel="folderActions.showRenameFolderDialog.value = false"
    >
      <template #body>
        <input
          v-model="folderActions.renameFolderName.value"
          type="text"
          :placeholder="$t('templateFolders.folderName', 'Folder name')"
          class="w-full px-4 py-2.5 bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500"
          @keydown.enter="folderActions.handleRenameFolder"
        />
      </template>
    </ConfirmDialog>

    <!-- Delete Folder Dialog -->
    <ConfirmDialog
      :show="folderActions.showDeleteFolderDialog.value"
      :title="$t('templateFolders.deleteFolder', 'Delete Folder')"
      :message="$t('templateFolders.deleteFolderMessage', 'Templates in this folder will be moved to the root level.')"
      :confirm-text="$t('common.delete')"
      variant="danger"
      :loading="folderActions.deletingFolder.value"
      @confirm="folderActions.handleDeleteFolder"
      @cancel="folderActions.showDeleteFolderDialog.value = false"
    />

    <!-- Move to Folder Dialog -->
    <MoveToFolderDialog
      :show="folderActions.showMoveToFolderDialog.value"
      :folders="store.folders"
      @confirm="folderActions.handleMoveToFolder"
      @cancel="folderActions.showMoveToFolderDialog.value = false"
    />

    <!-- Manage Folders Dialog (Finder-style) -->
    <ManageFoldersDialog
      :show="folderActions.showManageFoldersDialog.value"
      :folders="store.folders"
      :templates="store.allTemplatesFull"
      :default-position="store.defaultFolderPosition"
      @close="handleManageDialogClose"
      @rename="handleManageFolderRename"
      @delete="handleFinderDeleteFolder"
      @create-folder="folderActions.handleCreateFolder"
      @move-templates="handleFinderMoveTemplates"
      @reorder-folders="handleReorderFolders"
    />

    <!-- Success Toast -->
    <PublishSuccessToast
      :message="actions.publishSuccessMessage.value"
      :invite-key="actions.publishedInviteKey.value"
      :copied="actions.copiedKey.value"
      @copy="actions.copyInviteKey"
    />

    <WarroomRecipeBundleDialog
      :show="warroomImport.showDialog.value"
      :project-slug="warroomImport.projectSlug.value"
      :base-url="warroomImport.baseUrl.value"
      :source-path="warroomImport.sourcePath.value"
      :pending-bundles="warroomImport.pendingBundles.value"
      :rejected-bundles="warroomImport.rejectedBundles.value"
      :dry-run-result="warroomImport.dryRunResult.value"
      :import-result="warroomImport.importResult.value"
      :error="warroomImport.error.value"
      :inbox-error="warroomImport.inboxError.value"
      :scanning="warroomImport.scanning.value"
      :dry-running="warroomImport.dryRunning.value"
      :importing="warroomImport.importing.value"
      @update:project-slug="warroomImport.projectSlug.value = $event"
      @update:base-url="warroomImport.baseUrl.value = $event"
      @select-pending="warroomImport.selectPendingBundle"
      @scan-inbox="warroomImport.scanInbox"
      @dry-run="warroomImport.runDryRun"
      @import="warroomImport.confirmImport"
      @close="warroomImport.closeDialog"
    />
  </div>
</template>

<script setup>
import WaveHero from '@/components/common/WaveHero.vue'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'
import AppInput from '@/components/common/AppInput.vue'
import {
  TemplateToolbar,
  CreateTemplateModal,
  EditTemplateModal,
  PublishTemplateModal,
  InviteKeyManager,
  BatchActionBar,
  PublishSuccessToast,
  CreateFolderDialog,
  MoveToFolderDialog,
  ManageFoldersDialog
} from '@/components/templates'
import TemplateGrid from '@/components/templates/TemplateGrid.vue'
import TemplateFilters from '@/components/templates/TemplateFilters.vue'
import WarroomRecipeBundleDialog from '@/components/templates/WarroomRecipeBundleDialog.vue'
import PullRequestForm from '@/components/templates/pullRequests/PullRequestForm.vue'
import { computed } from 'vue'
import {
  Plus, AlertCircle, UserPlus, ArrowRight, X, Loader2, CheckCircle2, FileUp,
  FolderPlus, FolderInput, FolderOpen, Folder, Settings, MoreHorizontal,
  ChevronLeft, ChevronRight, ChevronDown
} from 'lucide-vue-next'
import { useMyTemplates } from '@/composables/useMyTemplates'

const {
  store,
  actions,
  selection,
  folderActions,
  joinCollab,
  warroomImport,
  viewMode,
  showPRForm,
  prFormTarget,
  prSubmitting,
  yamlFileInput,
  selectedTags,
  availableTags,
  triggerImportYAML,
  handleImportYAML,
  toggleTagFilter,
  openPRForm,
  handleSubmitPR,
  handleFolderRename,
  handleFolderDelete,
  handleManageFolderRename,
  handleFinderMoveTemplates,
  handleFinderDeleteFolder,
  handleReorderFolders,
  handleManageDialogClose,
  openManageDialog,
} = useMyTemplates()

// File Manager: wrap current templates as a single flat section (TemplateGrid compat)
const flatSection = computed(() => [{
  folder: { id: '__flat__', name: '', color: 'transparent' },
  templates: store.templates
}])
const alwaysExpanded = computed(() => new Set(['__flat__']))
</script>

<style scoped>
/* ========== Join Collaboration — Trigger Button ========== */
.join-trigger-btn {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(139, 92, 246, 0.12);
  border: 1px solid rgba(139, 92, 246, 0.35);
  border-radius: 12px;
  color: #fff;
  font-weight: 500;
  font-size: 14px;
  cursor: pointer;
  overflow: hidden;
  transition: all 0.3s ease;
}

.join-trigger-btn:hover {
  background: rgba(139, 92, 246, 0.22);
  border-color: rgba(139, 92, 246, 0.6);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.2), inset 0 0 20px rgba(139, 92, 246, 0.06);
  transform: translateY(-1px);
}

.join-trigger-glow {
  position: absolute;
  inset: -1px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.3), rgba(139, 92, 246, 0.3), rgba(236, 72, 153, 0.3));
  background-size: 200% 200%;
  animation: join-glow-shift 4s ease-in-out infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 0;
}

.join-trigger-btn:hover .join-trigger-glow {
  opacity: 1;
}

@keyframes join-glow-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

/* ========== Join Collaboration — Expanded Panel ========== */
.join-panel {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  z-index: 20;
}

.join-panel-inner {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 6px;
  border-radius: 14px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(15, 23, 42, 0.92), rgba(30, 41, 59, 0.88)) padding-box,
    linear-gradient(135deg, rgba(6, 182, 212, 0.6), rgba(139, 92, 246, 0.6), rgba(6, 182, 212, 0.6)) border-box;
  border: 1.5px solid transparent;
  backdrop-filter: blur(20px) saturate(1.4);
  box-shadow:
    0 0 28px rgba(6, 182, 212, 0.12),
    0 0 48px rgba(139, 92, 246, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.join-panel-inner::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(6, 182, 212, 0.06), rgba(139, 92, 246, 0.06), transparent);
  border-radius: 14px;
  animation: join-scan 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes join-scan {
  0% { left: -60%; }
  100% { left: 100%; }
}

.join-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  border-radius: 10px;
  transition: all 0.3s ease;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.8)) padding-box,
    linear-gradient(135deg, rgba(100, 116, 139, 0.4), rgba(139, 92, 246, 0.25)) border-box;
  border: 1px solid transparent;
}

.join-input-wrap:focus-within {
  background:
    linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.85)) padding-box,
    linear-gradient(135deg, rgba(6, 182, 212, 0.7), rgba(139, 92, 246, 0.7)) border-box;
  box-shadow:
    0 0 16px rgba(6, 182, 212, 0.15),
    0 0 4px rgba(139, 92, 246, 0.15);
}

.join-input-wrap.has-error {
  background:
    linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.85)) padding-box,
    linear-gradient(135deg, rgba(239, 68, 68, 0.6), rgba(239, 68, 68, 0.3)) border-box;
  animation: join-shake 0.4s ease;
}

.join-input-wrap.is-success {
  background:
    linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.85)) padding-box,
    linear-gradient(135deg, rgba(16, 185, 129, 0.6), rgba(6, 182, 212, 0.4)) border-box;
}

.join-input-icon {
  display: flex;
  align-items: center;
  padding-left: 10px;
  color: rgba(6, 182, 212, 0.5);
  flex-shrink: 0;
  transition: color 0.3s ease;
}

.join-input-wrap:focus-within .join-input-icon {
  color: #06B6D4;
}

.join-input {
  width: 156px;
  padding: 8px 10px 8px 6px;
  background: transparent;
  border: none;
  color: #E2E8F0;
  font-size: 13px;
  font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
  outline: none;
}

.join-input::placeholder {
  text-transform: none;
  color: rgba(148, 163, 184, 0.5);
  font-family: inherit;
  letter-spacing: 0;
}

.join-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8B5CF6, #06B6D4);
  border: none;
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.join-submit-btn::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: 10px;
  background: linear-gradient(135deg, #A78BFA, #22D3EE);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.join-submit-btn:not(:disabled):hover::before {
  opacity: 1;
}

.join-submit-btn:not(:disabled):hover {
  transform: scale(1.08);
  box-shadow:
    0 0 16px rgba(6, 182, 212, 0.4),
    0 0 32px rgba(139, 92, 246, 0.2);
}

.join-submit-btn > * {
  position: relative;
  z-index: 1;
}

.join-submit-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
  filter: grayscale(0.4);
}

.join-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: rgba(148, 163, 184, 0.4);
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.2s ease;
}

.join-close-btn:hover {
  color: rgba(248, 113, 113, 0.9);
  background: rgba(239, 68, 68, 0.1);
}

.join-feedback {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  backdrop-filter: blur(12px);
}

.join-feedback-error {
  color: #FCA5A5;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.join-feedback-success {
  color: #6EE7B7;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.25);
}

/* ========== Transitions ========== */
.join-panel-enter-active {
  animation: join-panel-in 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.join-panel-leave-active {
  animation: join-panel-in 0.2s ease reverse;
}

@keyframes join-panel-in {
  from {
    opacity: 0;
    transform: translateY(-50%) scale(0.92) translateX(12px);
    filter: blur(6px);
  }
  to {
    opacity: 1;
    transform: translateY(-50%) scale(1) translateX(0);
    filter: blur(0);
  }
}

.join-msg-enter-active {
  animation: join-msg-in 0.25s ease-out;
}
.join-msg-leave-active {
  animation: join-msg-in 0.15s ease reverse;
}

@keyframes join-msg-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes join-shake {
  0%, 100% { transform: translateX(0); }
  20% { transform: translateX(-4px); }
  40% { transform: translateX(4px); }
  60% { transform: translateX(-3px); }
  80% { transform: translateX(2px); }
}

/* ========== File Manager Layout ========== */
.fm-layout {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 24px;
  min-height: 60vh;
}

@media (max-width: 768px) {
  .fm-layout { grid-template-columns: 1fr; }
  .fm-sidebar { display: none; }
}

.fm-sidebar {
  display: flex;
  flex-direction: column;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 12px;
  overflow: hidden;
  position: sticky;
  top: 80px;
  align-self: start;
  max-height: calc(100vh - 100px);
}

.fm-sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.fm-sidebar-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.fm-sidebar-add {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: transparent;
  border: 1px solid transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-sidebar-add:hover {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.fm-folder-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.fm-folder-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 10px 8px calc(10px + (var(--folder-depth, 0) * 16px));
  border-radius: 8px;
  border: 1px solid transparent;
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s;
  text-align: left;
}

.fm-folder-tree-glyph {
  width: 13px;
  min-width: 13px;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fm-folder-item:hover {
  background: rgba(51, 65, 85, 0.4);
  color: #e2e8f0;
}

.fm-folder-active {
  background: rgba(139, 92, 246, 0.1);
  border-color: rgba(139, 92, 246, 0.3);
  color: #e2e8f0;
}

.fm-folder-active .fm-folder-count {
  background: rgba(139, 92, 246, 0.25);
  color: #c4b5fd;
}

.fm-folder-icon { flex-shrink: 0; display: flex; min-width: 16px; }
.fm-folder-name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.fm-folder-count {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 10px;
  background: rgba(51, 65, 85, 0.5);
  color: #64748b;
  flex-shrink: 0;
}

.fm-folder-menu {
  display: none;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: 4px;
  background: transparent;
  border: none;
  color: #64748b;
  cursor: pointer;
  flex-shrink: 0;
}

.fm-folder-item:hover .fm-folder-menu { display: flex; }
.fm-folder-menu:hover { background: rgba(51, 65, 85, 0.6); color: #e2e8f0; }

.fm-sidebar-footer {
  padding: 8px;
  border-top: 1px solid rgba(51, 65, 85, 0.5);
}

.fm-manage-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 8px 12px;
  border-radius: 8px;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-manage-btn:hover { background: rgba(51, 65, 85, 0.4); color: #94a3b8; }

.fm-content { min-width: 0; }
.fm-toolbar { margin-bottom: 12px; }

.fm-loading, .fm-empty, .fm-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 300px;
  text-align: center;
}

.fm-error {
  color: #f87171;
  gap: 8px;
}

.fm-retry-btn {
  padding: 6px 16px;
  border-radius: 6px;
  border: 1px solid rgba(248, 113, 113, 0.3);
  background: transparent;
  color: #f87171;
  font-size: 13px;
  cursor: pointer;
}

.fm-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 10px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  background: transparent;
  color: #94a3b8;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-action-btn:hover { border-color: rgba(139, 92, 246, 0.5); color: #e2e8f0; }

.fm-action-primary {
  background: linear-gradient(135deg, #7c3aed, #3b82f6);
  border-color: transparent;
  color: #fff;
}

.fm-action-primary:hover { box-shadow: 0 4px 16px rgba(124, 58, 237, 0.3); }

.fm-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 20px 0;
}

.fm-page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid rgba(51, 65, 85, 0.5);
  background: rgba(15, 23, 42, 0.5);
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.15s;
}

.fm-page-btn:hover:not(:disabled) { border-color: rgba(139, 92, 246, 0.5); color: #e2e8f0; }
.fm-page-btn:disabled { opacity: 0.3; cursor: not-allowed; }

.fm-page-info {
  font-size: 13px;
  color: #64748b;
}

/* ========== PR Dialog ========== */
.fade-enter-active { transition: opacity 0.2s ease; }
.fade-leave-active { transition: opacity 0.15s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.animate-scale-in {
  animation: scale-in 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.92) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
</style>
