<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen && breakpoint"
        class="interact-overlay"
        @click.self="$emit('close')"
      >
        <Transition
          enter-active-class="transition-all duration-400 ease-out"
          enter-from-class="opacity-0 scale-95 translate-y-4"
          enter-to-class="opacity-100 scale-100 translate-y-0"
          leave-active-class="transition-all duration-200 ease-in"
          leave-from-class="opacity-100 scale-100"
          leave-to-class="opacity-0 scale-95"
        >
          <div v-if="isOpen" class="interact-dialog">
            <!-- Header -->
            <div class="dialog-header">
              <div class="header-glow"></div>
              <div class="header-content">
                <div class="header-icon">
                  <MousePointerClick :size="20" />
                  <span class="icon-pulse"></span>
                </div>
                <div class="header-text">
                  <h2>{{ breakpoint.title || t('browserInteract.title') }}</h2>
                  <p class="header-url">{{ contextSnapshot.url || '' }}</p>
                </div>
                <button class="close-btn" @click="$emit('close')" aria-label="Close">
                  <X :size="18" />
                </button>
              </div>
            </div>

            <!-- Description -->
            <p v-if="breakpoint.description" class="dialog-desc">{{ breakpoint.description }}</p>

            <!-- Elements -->
            <div class="elements-container custom-scrollbar">
              <!-- Screenshot thumbnail inside scroll area -->
              <div v-if="screenshotSrc" class="screenshot-thumb" @click="screenshotExpanded = !screenshotExpanded">
                <img
                  :src="screenshotSrc"
                  :class="{ expanded: screenshotExpanded }"
                />
                <span class="screenshot-toggle">{{ screenshotExpanded ? '▲' : '▼' }} {{ t('browserInteract.pagePreview') }}</span>
              </div>
              <template v-if="elementRows.length">
                <div v-for="(row, ri) in elementRows" :key="ri" class="element-row">
                  <template v-for="(el, ei) in row" :key="ei">

                    <!-- SELECT -->
                    <div v-if="el._type === 'select'" class="el-card el-select" :class="{ selected: isSelected(el) }">
                      <label class="el-label">{{ el.label || 'Dropdown' }}</label>
                      <select
                        class="el-native-select"
                        :value="el.current_value"
                        @change="selectDropdownOption(el, $event)"
                      >
                        <option v-for="opt in (el.options || [])" :key="opt.value" :value="opt.value">
                          {{ opt.label || opt.value }}
                        </option>
                      </select>
                    </div>

                    <!-- INPUT -->
                    <div v-else-if="el._type === 'input'" class="el-card el-input" :class="{ selected: isSelected(el) }">
                      <label class="el-label">{{ el.label || el.placeholder || 'Input' }}</label>
                      <div class="el-input-row">
                        <input
                          type="text"
                          class="el-text-input"
                          :placeholder="el.placeholder || ''"
                          :value="inputValues[el.selector] ?? el.value"
                          @input="setInputValue(el, $event.target.value)"
                          @keydown.enter="selectInputAction(el)"
                        />
                        <button class="el-input-submit" @click="selectInputAction(el)" aria-label="Submit input">
                          <ArrowRight :size="14" />
                        </button>
                      </div>
                    </div>

                    <!-- BUTTON -->
                    <button
                      v-else-if="el._type === 'button'"
                      class="el-card el-button"
                      :class="{ selected: isSelected(el) }"
                      @click="selectAction('click', el.selector)"
                      :aria-label="el.label || 'Button'"
                    >
                      <MousePointerClick :size="14" class="el-icon" />
                      <span>{{ el.label || 'Button' }}</span>
                    </button>

                    <!-- LINK -->
                    <button
                      v-else-if="el._type === 'link'"
                      class="el-card el-link"
                      :class="{ selected: isSelected(el) }"
                      @click="selectAction('click', el.selector)"
                      :aria-label="el.label || 'Link'"
                    >
                      <ExternalLink :size="14" class="el-icon" />
                      <span>{{ el.label || 'Link' }}</span>
                    </button>

                    <!-- CHECKBOX / SWITCH -->
                    <button
                      v-else-if="el._type === 'checkbox' || el._type === 'switch'"
                      class="el-card el-toggle"
                      :class="{ selected: isSelected(el), checked: el.checked }"
                      @click="selectAction('toggle', el.selector)"
                      :aria-label="el.label || 'Toggle'"
                    >
                      <div class="toggle-indicator" :class="{ on: el.checked }"></div>
                      <span>{{ el.label || el._type }}</span>
                    </button>

                    <!-- RADIO -->
                    <div v-else-if="el._type === 'radio'" class="el-card el-radio">
                      <label class="el-label">{{ el.label || 'Radio' }}</label>
                      <div class="el-radio-options">
                        <button
                          v-for="opt in (el.options || [])"
                          :key="opt.selector"
                          class="radio-opt"
                          :class="{ active: opt.selected || selectedSelector === opt.selector }"
                          @click="selectAction('click', opt.selector)"
                        >
                          {{ opt.label || opt.value }}
                        </button>
                      </div>
                    </div>
                  </template>
                </div>
              </template>

              <!-- Empty -->
              <div v-else class="empty-state">
                <MousePointerClick :size="40" />
                <p>{{ t('browserInteract.noElements') }}</p>
              </div>
            </div>

            <!-- Footer -->
            <div class="dialog-footer">
              <div class="footer-status">
                <template v-if="selectedAction">
                  <span class="status-action">{{ selectedAction }}</span>
                  <ChevronRight :size="14" />
                  <span class="status-selector">{{ selectedSelector?.substring(0, 50) }}</span>
                </template>
                <template v-else>
                  <span class="status-hint">{{ t('browserInteract.selectHint') }}</span>
                </template>
              </div>
              <div class="footer-actions">
                <button class="btn-skip" :disabled="submitting" @click="handleSkip" aria-label="Skip">
                  {{ t('browserInteract.skip') }}
                </button>
                <button class="btn-execute" :disabled="submitting || !selectedAction" @click="handleConfirm" aria-label="Execute">
                  <Play :size="14" />
                  {{ t('browserInteract.execute') }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { MousePointerClick, X, Play, ExternalLink, ArrowRight, ChevronRight } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
  breakpoint: { type: Object, default: null },
})

const emit = defineEmits(['close', 'approve', 'reject'])

const selectedAction = ref('')
const selectedSelector = ref('')
const selectedValue = ref('')
const inputValues = ref({})
const submitting = ref(false)
const screenshotExpanded = ref(false)

const contextSnapshot = computed(() => {
  return props.breakpoint?.contextSnapshot || props.breakpoint?.context_snapshot || {}
})

// Support both stored URL and inline base64 screenshots.
const screenshotSrc = computed(() => {
  const ctx = contextSnapshot.value
  if (ctx.screenshot_url) return ctx.screenshot_url
  if (ctx.screenshot_base64) {
    return `data:${ctx.screenshot_media_type || 'image/jpeg'};base64,${ctx.screenshot_base64}`
  }
  return ''
})

const elements = computed(() => contextSnapshot.value.elements || [])

const elementRows = computed(() => {
  if (!elements.value.length) return []
  const rows = []
  let currentRow = []
  let currentTop = -Infinity
  for (const el of elements.value) {
    const top = el.rect?.top ?? 0
    if (top - currentTop > 30 && currentRow.length > 0) {
      rows.push(currentRow)
      currentRow = []
    }
    currentRow.push(el)
    if (currentRow.length === 1) currentTop = top
  }
  if (currentRow.length > 0) rows.push(currentRow)
  return rows
})

watch(() => props.breakpoint, () => {
  selectedAction.value = ''
  selectedSelector.value = ''
  selectedValue.value = ''
  inputValues.value = {}
  submitting.value = false
}, { immediate: true })

function isSelected(el) { return selectedSelector.value === el.selector }

function selectAction(action, selector, value = '') {
  selectedAction.value = action
  selectedSelector.value = selector
  selectedValue.value = value
}

function selectDropdownOption(el, event) {
  const value = event.target.value
  if (el.kind === 'native') {
    selectAction('select', el.selector, value)
  } else {
    const opt = (el.options || []).find(o => o.value === value)
    selectAction('select', el.selector, opt?.option_selector || value)
  }
}

function setInputValue(el, value) { inputValues.value[el.selector] = value }

function selectInputAction(el) {
  selectAction('type', el.selector, inputValues.value[el.selector] || '')
}

function getBpId() {
  return props.breakpoint?.breakpointId || props.breakpoint?.breakpoint_id || ''
}

async function handleConfirm() {
  if (!selectedAction.value || !selectedSelector.value) return
  submitting.value = true
  try {
    emit('approve', {
      breakpointId: getBpId(),
      comment: '',
      customInputs: {
        action: selectedAction.value,
        selector: selectedSelector.value,
        value: selectedValue.value,
      }
    })
  } finally {
    submitting.value = false
  }
}

async function handleSkip() {
  submitting.value = true
  try {
    emit('reject', {
      breakpointId: getBpId(),
      comment: 'Skipped locally',
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.interact-overlay {
  position: fixed;
  inset: 0;
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
}

.interact-dialog {
  width: 90vw;
  max-width: 720px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(180deg, #0f172a 0%, #020617 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 16px;
  box-shadow:
    0 0 60px rgba(139, 92, 246, 0.15),
    0 25px 50px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  overflow: hidden;
}

/* Header */
.dialog-header {
  position: relative;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(139, 92, 246, 0.15);
}

.header-glow {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 100%;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
  pointer-events: none;
}

.header-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px; height: 40px;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(99, 102, 241, 0.1));
  border: 1px solid rgba(139, 92, 246, 0.3);
  border-radius: 10px;
  color: #a78bfa;
}

.icon-pulse {
  position: absolute;
  inset: -2px;
  border-radius: 12px;
  border: 2px solid rgba(139, 92, 246, 0.4);
  animation: pulse-ring 2s ease-out infinite;
}

@keyframes pulse-ring {
  0% { opacity: 1; transform: scale(1); }
  100% { opacity: 0; transform: scale(1.3); }
}

.header-text {
  flex: 1;
  min-width: 0;
}

.header-text h2 {
  font-size: 16px;
  font-weight: 600;
  color: #f1f5f9;
  margin: 0;
}

.header-url {
  font-size: 12px;
  color: #64748b;
  margin: 2px 0 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.close-btn {
  width: 32px; height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

/* Screenshot thumbnail (inside scroll area) */
.screenshot-thumb {
  cursor: pointer;
  border: 1px solid #1e293b;
  border-radius: 8px;
  overflow: hidden;
  transition: border-color 0.2s;
}

.screenshot-thumb:hover { border-color: #334155; }

.screenshot-thumb img {
  width: 100%;
  max-height: 60px;
  object-fit: cover;
  object-position: top;
  opacity: 0.5;
  transition: all 0.3s;
}

.screenshot-thumb img.expanded {
  max-height: 300px;
  opacity: 0.8;
}

.screenshot-toggle {
  display: block;
  padding: 4px 10px;
  font-size: 10px;
  color: #475569;
  background: rgba(15, 23, 42, 0.8);
}

/* Description */
.dialog-desc {
  padding: 12px 24px 0;
  font-size: 13px;
  color: #94a3b8;
}

/* Elements */
.elements-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.element-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

/* Element cards */
.el-card {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.el-card.selected {
  box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.5), 0 0 20px rgba(139, 92, 246, 0.15);
}

/* SELECT */
.el-select {
  flex: 1;
  min-width: 180px;
}

.el-label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
}

.el-native-select {
  width: 100%;
  padding: 8px 32px 8px 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid #334155;
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 13px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2'%3E%3Cpath d='m6 9 6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  transition: all 0.2s;
}

.el-native-select:hover { border-color: #475569; }
.el-native-select:focus { border-color: #8b5cf6; outline: none; box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2); }
.el-native-select option { background: #1e293b; color: #e2e8f0; }
.el-select.selected .el-native-select { border-color: #8b5cf6; }

/* INPUT */
.el-input {
  flex: 1;
  min-width: 180px;
}

.el-input-row {
  display: flex;
  gap: 0;
}

.el-text-input {
  flex: 1;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid #334155;
  border-radius: 8px 0 0 8px;
  color: #e2e8f0;
  font-size: 13px;
  outline: none;
  transition: all 0.2s;
}

.el-text-input::placeholder { color: #475569; }
.el-text-input:focus { border-color: #8b5cf6; }
.el-input.selected .el-text-input { border-color: #8b5cf6; }

.el-input-submit {
  padding: 8px 12px;
  background: rgba(139, 92, 246, 0.15);
  border: 1px solid #334155;
  border-left: none;
  border-radius: 0 8px 8px 0;
  color: #a78bfa;
  cursor: pointer;
  transition: all 0.2s;
}

.el-input-submit:hover { background: rgba(139, 92, 246, 0.3); color: #c4b5fd; }

/* BUTTON */
.el-button {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.el-button:hover { background: rgba(139, 92, 246, 0.1); border-color: rgba(139, 92, 246, 0.3); color: #e2e8f0; }
.el-button.selected { background: rgba(139, 92, 246, 0.15); border-color: #8b5cf6; color: #e2e8f0; }
.el-icon { color: #64748b; flex-shrink: 0; }
.el-button.selected .el-icon { color: #a78bfa; }

/* LINK */
.el-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  color: #60a5fa;
  font-size: 13px;
  cursor: pointer;
  text-align: left;
}

.el-link:hover { background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.3); }
.el-link.selected { background: rgba(139, 92, 246, 0.15); border-color: #8b5cf6; color: #c4b5fd; }
.el-link.selected .el-icon { color: #a78bfa; }

/* TOGGLE */
.el-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #334155;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 13px;
  cursor: pointer;
}

.el-toggle:hover { border-color: #475569; }
.el-toggle.selected { border-color: #8b5cf6; }

.toggle-indicator {
  width: 32px; height: 18px;
  border-radius: 9px;
  background: #334155;
  position: relative;
  transition: background 0.2s;
}

.toggle-indicator::after {
  content: '';
  position: absolute;
  top: 2px; left: 2px;
  width: 14px; height: 14px;
  border-radius: 50%;
  background: #64748b;
  transition: all 0.2s;
}

.toggle-indicator.on { background: #8b5cf6; }
.toggle-indicator.on::after { left: 16px; background: #e2e8f0; }

/* RADIO */
.el-radio { width: 100%; }

.el-radio-options {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.radio-opt {
  padding: 6px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid #334155;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.radio-opt:hover { border-color: #475569; color: #e2e8f0; }
.radio-opt.active { background: rgba(139, 92, 246, 0.15); border-color: #8b5cf6; color: #c4b5fd; }

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #475569;
  gap: 12px;
}

/* Footer */
.dialog-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-top: 1px solid rgba(139, 92, 246, 0.1);
  background: rgba(15, 23, 42, 0.5);
}

.footer-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #475569;
  min-width: 0;
  overflow: hidden;
}

.status-action {
  color: #a78bfa;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-selector {
  font-family: 'SF Mono', Monaco, monospace;
  font-size: 11px;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-hint { color: #475569; }

.footer-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.btn-skip {
  padding: 8px 18px;
  background: transparent;
  border: 1px solid #334155;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-skip:hover { background: rgba(71, 85, 105, 0.3); color: #e2e8f0; }
.btn-skip:disabled { opacity: 0.4; cursor: not-allowed; }

.btn-execute {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 20px;
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.btn-execute:hover { background: linear-gradient(135deg, #8b5cf6, #7c3aed); box-shadow: 0 6px 20px rgba(124, 58, 237, 0.4); transform: translateY(-1px); }
.btn-execute:active { transform: translateY(0); }
.btn-execute:disabled { opacity: 0.4; cursor: not-allowed; transform: none; box-shadow: none; }

/* Scrollbar */
.custom-scrollbar::-webkit-scrollbar { width: 5px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(139, 92, 246, 0.3); border-radius: 3px; }
</style>
