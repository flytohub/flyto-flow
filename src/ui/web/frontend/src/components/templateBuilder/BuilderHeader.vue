<template>
  <header class="builder-header">
    <!-- Glow line -->
    <div class="header-glow-line"></div>

    <!-- Left section -->
    <div class="header-left-section">
      <!-- Back button -->
      <button @click="$emit('back')" class="header-back-btn" :title="$t('templateBuilder.toolbar.back')">
        <ArrowLeft :size="18" />
      </button>

      <!-- Template name (display only) -->
      <span class="header-template-name" :title="templateName">
        {{ templateName || $t('templateBuilder.toolbar.templateNamePlaceholder') }}
      </span>
    </div>

    <!-- Right section - Actions -->
    <div class="header-right-section">
      <!-- Collaboration Button (always visible for saved templates) -->
      <button
        v-if="existingTemplateId"
        @click="$emit('toggle-collaboration')"
        class="header-action-btn collab"
        :class="{ active: isCollabConnected, 'has-error': collabError }"
        :title="collabError || $t('collaboration.title', 'Collaboration')"
      >
        <Users :size="16" />
        <span v-if="isCollabConnected && participants.length > 1" class="collab-count">
          {{ participants.length }}
        </span>
        <span v-else-if="collabError" class="collab-error-dot"></span>
      </button>
      <!-- Tidy Nodes button for workflow tab -->
      <button
        v-if="activeTab === 'workflow'"
        @click="$emit('tidy-nodes')"
        class="header-action-btn tidy"
        :title="$t('templateBuilder.header.tidyNodes', 'Tidy Nodes')"
      >
        <LayoutGrid :size="16" />
      </button>
      <!-- Settings icon for workflow tab -->
      <button
        v-if="activeTab === 'workflow'"
        @click="$emit('toggle-settings')"
        class="header-action-btn settings"
        :title="$t('templateBuilder.header.settings', 'Settings')"
      >
        <SettingsIcon :size="16" />
      </button>
      <!-- Record button (desktop only) -->
      <button
        v-if="hasRecording && activeTab === 'workflow'"
        @click="$emit(isRecording ? 'stop-recording' : 'start-recording')"
        class="header-action-btn record"
        :class="{ active: isRecording }"
        :title="isRecording ? 'Stop Recording' : 'Record Browser Actions'"
      >
        <Video :size="16" />
      </button>

      <!-- Divider: canvas tools | execution -->
      <div v-if="showCanvasDivider" class="btn-divider"></div>

      <!-- Execution Controls -->
      <button v-if="isExecuting" @click="$emit('stop')" class="header-action-btn stop">
        <Square :size="16" />
        <span>{{ $t('templateBuilder.header.stop') }}</span>
      </button>
      <button v-else @click="$emit('run')" class="header-action-btn run">
        <Play :size="16" />
        <span>{{ $t('templateBuilder.header.run') }}</span>
      </button>

      <!-- Browser screencast button — always visible when browser is alive -->
      <button
        v-if="hasBrowser"
        @click="$emit('toggle-browser')"
        class="header-action-btn browser"
        :title="$t('templateBuilder.header.browser', 'Live Browser')"
      >
        <Globe :size="16" />
      </button>

      <!-- Breakpoint Approval Badge -->
      <BreakpointBadge
        v-if="isExecuting || hasPendingBreakpoints"
        :user-id="userId"
        @approved="$emit('breakpoint-approved', $event)"
        @rejected="$emit('breakpoint-rejected', $event)"
      />

      <!-- Divider: execution | debug -->
      <div v-if="showDebugToolbar" class="btn-divider"></div>

      <!-- Advanced Mode Toggle + Floating Debug Dock -->
      <div v-if="showDebugToolbar" class="advanced-section" ref="advancedSection">
        <button
          @click="advancedExpanded = !advancedExpanded"
          class="header-action-btn advanced"
          :class="{ active: advancedExpanded }"
          :title="$t('templateBuilder.header.advanced', 'Advanced')"
        >
          <Wrench :size="16" />
          <ChevronDown
            :size="14"
            class="chevron-icon"
            :class="{ rotated: advancedExpanded }"
          />
        </button>

        <!-- Floating Debug Dock -->
        <Transition name="dock-appear">
          <DebugToolbar
            v-if="advancedExpanded"
            class="debug-dock-float"
            :active-panel="activeDebugPanel"
            :can-replay="canReplay"
            :has-timeline="hasTimeline"
            :test-status="testStatus"
            :locked-count="lockedVersionCount"
            :execution-count="executionCount"
            @toggle-evidence="$emit('toggle-debug-panel', 'evidence')"
            @toggle-lineage="$emit('toggle-debug-panel', 'lineage')"
            @toggle-history="$emit('toggle-debug-panel', 'history')"
            @toggle-timeline="$emit('toggle-debug-panel', 'timeline')"
            @toggle-replay="$emit('toggle-debug-panel', 'replay')"
            @toggle-tests="$emit('toggle-debug-panel', 'tests')"
            @toggle-versions="$emit('toggle-debug-panel', 'versions')"
          />
        </Transition>
      </div>

      <!-- Divider: before save -->
      <div class="btn-divider"></div>

      <!-- Save dropdown for existing templates -->
      <div v-if="existingTemplateId" class="save-dropdown" ref="saveDropdown">
        <button @click="$emit('save')" class="header-action-btn save">
          <Save :size="16" />
          <span>{{ $t('templateBuilder.header.updateTemplate') }}</span>
        </button>
        <button @click="toggleSaveMenu" class="header-action-btn save-arrow" aria-label="Save options">
          <ChevronDown :size="14" />
        </button>
        <div v-if="showSaveMenu" class="save-menu">
          <div class="save-menu-section-label">Settings</div>
          <label class="save-menu-checkbox">
            <input
              type="checkbox"
              :checked="autoSaveEnabled"
              @change="$emit('toggle-auto-save')"
            />
            <span>{{ $t('templateBuilder.header.autoSave', 'Auto-save') }}</span>
          </label>
          <div class="save-menu-divider"></div>
          <div class="save-menu-section-label">Actions</div>
          <button @click="handleSaveAsNew" class="save-menu-item">
            <FilePlus :size="14" />
            {{ $t('templateBuilder.header.saveAsNew') }}
          </button>
        </div>
      </div>

      <!-- Simple save for new templates -->
      <button v-else @click="$emit('save')" class="header-action-btn save">
        <Save :size="16" />
        <span>{{ $t('templateBuilder.toolbar.saveTemplate') }}</span>
      </button>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { storeToRefs } from 'pinia'
import { ArrowLeft, Play, Square, Save, ChevronDown, FilePlus, Settings as SettingsIcon, Wrench, LayoutGrid, Users, Globe, Video } from 'lucide-vue-next'
import { BreakpointBadge } from '../execution'
import { DebugToolbar } from '../debug'
import { useCollaborationStore } from '@/stores/collaborationStore'
import { useCapabilitiesStore } from '@/stores/capabilities'

const collaborationStore = useCollaborationStore()
const { participants, isConnected: isCollabConnected, error: collabError } = storeToRefs(collaborationStore)

const capabilitiesStore = useCapabilitiesStore()
const { hasRecording } = storeToRefs(capabilitiesStore)

const props = defineProps({
  templateName: {
    type: String,
    required: true
  },
  activeTab: {
    type: String,
    required: true
  },
  isExecuting: {
    type: Boolean,
    default: false
  },
  existingTemplateId: {
    type: String,
    default: null
  },
  autoSaveEnabled: {
    type: Boolean,
    default: true
  },
  hasPendingBreakpoints: {
    type: Boolean,
    default: false
  },
  userId: {
    type: String,
    default: 'current_user'
  },
  showDebugToolbar: {
    type: Boolean,
    default: false
  },
  activeDebugPanel: {
    type: String,
    default: null
  },
  canReplay: {
    type: Boolean,
    default: true
  },
  hasTimeline: {
    type: Boolean,
    default: false
  },
  testStatus: {
    type: String,
    default: null
  },
  lockedVersionCount: {
    type: Number,
    default: 0
  },
  executionCount: {
    type: Number,
    default: 0
  },
  hasBrowser: {
    type: Boolean,
    default: false
  },
  isRecording: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'back',
  'run',
  'stop',
  'save',
  'save-as-new',
  'toggle-auto-save',
  'toggle-settings',
  'tidy-nodes',
  'breakpoint-approved',
  'breakpoint-rejected',
  'toggle-debug-panel',
  'show-upgrade',
  'toggle-collaboration',
  'toggle-browser',
  'start-recording',
  'stop-recording'
])

const saveDropdown = ref(null)
const advancedSection = ref(null)
const showSaveMenu = ref(false)
const advancedExpanded = ref(false)

const showCanvasDivider = computed(() => !!props.existingTemplateId || props.activeTab === 'workflow')

function toggleSaveMenu() {
  showSaveMenu.value = !showSaveMenu.value
}

function handleSaveAsNew() {
  showSaveMenu.value = false
  emit('save-as-new')
}

function handleClickOutside(event) {
  if (saveDropdown.value && !saveDropdown.value.contains(event.target)) {
    showSaveMenu.value = false
  }
  if (advancedSection.value && !advancedSection.value.contains(event.target)) {
    advancedExpanded.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.builder-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: linear-gradient(180deg, #0c1222 0%, #070b14 100%);
  border-bottom: 1px solid rgba(71, 85, 105, 0.5);
  z-index: 20;
}

.header-glow-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent 0%, #8B5CF6 15%, #06B6D4 50%, #8B5CF6 85%, transparent 100%);
  animation: glow-slide 4s ease-in-out infinite;
}

@keyframes glow-slide {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

/* Left Section */
.header-left-section {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-back-btn {
  width: 38px;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 10px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.header-back-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
  transform: translateX(-2px);
}

.header-template-name {
  font-size: 15px;
  font-weight: 600;
  color: #e2e8f0;
  max-width: 280px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Right Section */
.header-right-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.header-action-btn.collab {
  position: relative;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
  padding: 8px 10px;
}

.header-action-btn.collab:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
}

.header-action-btn.collab.active {
  background: rgba(34, 197, 94, 0.15);
  border-color: rgba(34, 197, 94, 0.5);
  color: #22c55e;
}

.header-action-btn.collab.active:hover {
  background: rgba(34, 197, 94, 0.25);
  border-color: rgba(34, 197, 94, 0.6);
}

.collab-count {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #22c55e;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  color: white;
  padding: 0 4px;
}

.header-action-btn.collab.has-error {
  border-color: rgba(251, 191, 36, 0.4);
}

.collab-error-dot {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  background: #fbbf24;
  border-radius: 50%;
  border: 2px solid #0c1222;
}

.header-action-btn.tidy {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
  padding: 8px 10px;
}

.header-action-btn.tidy:hover {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.4);
  color: #10b981;
}

.header-action-btn.settings {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
  padding: 8px 10px;
}

.header-action-btn.settings:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
}

.header-action-btn.record {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
}

.header-action-btn.record:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.header-action-btn.record.active {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  color: #f87171;
  animation: record-pulse 1.5s ease-in-out infinite;
}

@keyframes record-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.header-action-btn.run {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(6, 182, 212, 0.1) 100%);
  border: 1px solid rgba(6, 182, 212, 0.4);
  color: #22d3ee;
}

.header-action-btn.run:hover {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(6, 182, 212, 0.2) 100%);
  border-color: rgba(6, 182, 212, 0.6);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.2);
}

.header-action-btn.stop {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(239, 68, 68, 0.1) 100%);
  border: 1px solid rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.header-action-btn.stop:hover {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(239, 68, 68, 0.2) 100%);
  border-color: rgba(239, 68, 68, 0.6);
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}

.header-action-btn.browser {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(59, 130, 246, 0.1) 100%);
  border: 1px solid rgba(59, 130, 246, 0.4);
  color: #60a5fa;
  padding: 8px 10px;
}

.header-action-btn.browser:hover {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(59, 130, 246, 0.2) 100%);
  border-color: rgba(59, 130, 246, 0.6);
  box-shadow: 0 0 20px rgba(59, 130, 246, 0.2);
}

.header-action-btn.save {
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: white;
}

.header-action-btn.save:hover {
  background: linear-gradient(135deg, #9F7AEA 0%, #8B5CF6 100%);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
  transform: translateY(-1px);
}

/* Save Dropdown */
.save-dropdown {
  position: relative;
  display: flex;
  align-items: stretch;
}

.save-dropdown .header-action-btn.save,
.save-dropdown .header-action-btn.save-arrow {
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  border: 1px solid rgba(139, 92, 246, 0.5);
  color: white;
}

.save-dropdown .header-action-btn.save {
  border-top-right-radius: 0;
  border-bottom-right-radius: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.2);
}

.save-dropdown .header-action-btn.save-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  border-top-left-radius: 0;
  border-bottom-left-radius: 0;
  border-left: none;
}

.save-dropdown .header-action-btn.save:hover,
.save-dropdown .header-action-btn.save-arrow:hover {
  background: linear-gradient(135deg, #9F7AEA 0%, #8B5CF6 100%);
  box-shadow: 0 0 20px rgba(139, 92, 246, 0.3);
}

.save-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 4px;
  min-width: 160px;
  background: #1e293b;
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  z-index: 200;
  overflow: hidden;
}

.save-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: transparent;
  border: none;
  color: #e2e8f0;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.save-menu-item:hover {
  background: rgba(139, 92, 246, 0.15);
}

.save-menu-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  color: #e2e8f0;
  font-size: 13px;
  cursor: pointer;
  transition: background 0.2s;
}

.save-menu-checkbox:hover {
  background: rgba(139, 92, 246, 0.15);
}

.save-menu-checkbox input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #8B5CF6;
  cursor: pointer;
}

.save-menu-divider {
  height: 1px;
  background: rgba(71, 85, 105, 0.5);
  margin: 4px 0;
}

.save-menu-section-label {
  padding: 6px 14px 2px;
  font-size: 10px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  user-select: none;
}

.btn-divider {
  width: 1px;
  height: 20px;
  background: rgba(71, 85, 105, 0.5);
  margin: 0 2px;
  flex-shrink: 0;
}

/* Advanced Button */
.header-action-btn.advanced {
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.5);
  color: #94a3b8;
  padding: 8px 10px;
  gap: 4px;
}

.header-action-btn.advanced:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.4);
  color: #a78bfa;
}

.header-action-btn.advanced.active {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
  color: #a78bfa;
}

.chevron-icon {
  transition: transform 0.2s ease;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
}

/* Advanced section — relative container for floating dock */
.advanced-section {
  position: relative;
}

.debug-dock-float {
  position: absolute;
  right: 0;
  top: calc(100% + 10px);
  z-index: 100;
}

/* Dock appear transition */
.dock-appear-enter-active {
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.dock-appear-leave-active {
  transition: all 0.15s ease-in;
}

.dock-appear-enter-from {
  opacity: 0;
  transform: scale(0.9) translateY(-6px);
}

.dock-appear-leave-to {
  opacity: 0;
  transform: scale(0.95) translateY(-4px);
}

</style>
