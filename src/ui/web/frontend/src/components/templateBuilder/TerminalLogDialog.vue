<template>
  <Teleport to="body">
    <Transition name="terminal-fade">
      <div
        v-if="show"
        role="dialog"
        aria-modal="true"
        aria-labelledby="terminal-dialog-title"
        class="terminal-overlay"
        @click.self="$emit('close')"
        @keydown.esc="$emit('close')"
      >
        <div class="terminal-dialog">
          <!-- Terminal Header -->
          <div class="terminal-header">
            <div class="terminal-header-left">
              <div class="terminal-icon" aria-hidden="true">
                <Terminal :size="20" />
              </div>
              <div class="terminal-title">
                <h3 id="terminal-dialog-title">{{ $t('terminal.title') }}</h3>
                <span class="terminal-status" :class="{ connected: isConnected }">
                  <span class="status-indicator"></span>
                  {{ isConnected ? $t('terminal.connected') : $t('terminal.disconnected') }}
                </span>
              </div>
            </div>
            <div class="terminal-header-right">
              <!-- Search -->
              <div class="terminal-search" :class="{ active: showSearch }">
                <Search :size="14" aria-hidden="true" />
                <AppInput
                  v-model="searchQuery"
                  :placeholder="$t('terminal.searchPlaceholder')"
                  @keydown="$event.key === 'Escape' && (showSearch = false)"
                  size="sm"
                />
                <span v-if="filteredLogs.length !== logs.length" class="search-count">
                  {{ filteredLogs.length }}/{{ logs.length }}
                </span>
              </div>
              <!-- Filter Buttons -->
              <div class="terminal-filters" role="toolbar" aria-label="Log level filters">
                <button
                  v-for="level in levels"
                  :key="level.name"
                  :class="['filter-btn', level.name.toLowerCase(), { active: activeFilters.includes(level.name) }]"
                  @click="toggleFilter(level.name)"
                  :aria-label="activeFilters.includes(level.name) ? $t('terminal.hideLogs', { level: level.name }) : $t('terminal.showLogs', { level: level.name })"
                  :aria-pressed="activeFilters.includes(level.name)"
                >
                  <component :is="level.icon" :size="14" aria-hidden="true" />
                </button>
              </div>
              <!-- Actions -->
              <div class="terminal-actions" role="toolbar" aria-label="Terminal actions">
                <button
                  class="action-btn"
                  @click="toggleAutoScroll"
                  :class="{ active: autoScroll }"
                  :aria-label="autoScroll ? $t('terminal.disableAutoScroll') : $t('terminal.enableAutoScroll')"
                  :aria-pressed="autoScroll"
                >
                  <ArrowDownToLine :size="16" aria-hidden="true" />
                </button>
                <button class="action-btn" @click="clearLogs" :aria-label="$t('terminal.clearLogs')">
                  <Trash2 :size="16" aria-hidden="true" />
                </button>
                <button class="action-btn close" @click="$emit('close')" :aria-label="$t('terminal.closeTerminal')">
                  <X :size="18" aria-hidden="true" />
                </button>
              </div>
            </div>
          </div>

          <!-- Terminal Body -->
          <div class="terminal-body" ref="terminalBody" @scroll="handleScroll" role="log" aria-live="polite" aria-label="Log output">
            <!-- Scan Line Effect -->
            <div class="scan-line" aria-hidden="true"></div>

            <!-- Log Entries -->
            <div v-if="filteredLogs.length === 0" class="terminal-empty">
              <MonitorDot :size="48" aria-hidden="true" />
              <p>{{ $t('terminal.waitingForLogs') }}</p>
              <span>{{ $t('terminal.logsWillAppear') }}</span>
            </div>
            <div
              v-for="(log, index) in filteredLogs"
              :key="index"
              :class="['log-entry', log.level.toLowerCase()]"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span :class="['log-level', log.level.toLowerCase()]">{{ log.level }}</span>
              <span class="log-logger">{{ formatLogger(log.logger) }}</span>
              <span class="log-message" v-html="highlightSearch(log.message)"></span>
            </div>
          </div>

          <!-- Terminal Footer -->
          <div class="terminal-footer">
            <div class="footer-stats">
              <span class="stat">
                <Activity :size="12" aria-hidden="true" />
                {{ logs.length }} entries
              </span>
              <span class="stat">
                <Clock :size="12" aria-hidden="true" />
                {{ connectionTime }}
              </span>
            </div>
            <div class="footer-info">
              <span class="system-info">FLYTO SYSTEM v2.0</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, toRef } from 'vue'
import {
  Terminal, Search, X, Trash2, ArrowDownToLine,
  AlertCircle, AlertTriangle, Info, Bug, Activity, Clock, MonitorDot
} from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import { useTerminalLogs } from '@/composables/useTerminalLogs'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close'])

// Template ref
const terminalBody = ref(null)

// Use composable with show ref and terminalBody ref
const {
  logs,
  searchQuery,
  showSearch,
  autoScroll,
  isConnected,
  activeFilters,
  connectionTime,
  filteredLogs,
  formatTime,
  formatLogger,
  highlightSearch,
  toggleFilter,
  toggleAutoScroll,
  clearLogs,
  handleScroll
} = useTerminalLogs({
  show: toRef(props, 'show'),
  terminalBody
})

// Log levels config with icons
const levels = [
  { name: 'ERROR', icon: AlertCircle },
  { name: 'WARNING', icon: AlertTriangle },
  { name: 'INFO', icon: Info },
  { name: 'DEBUG', icon: Bug }
]
</script>

<style scoped>
.terminal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.terminal-dialog {
  width: 90vw;
  max-width: 1200px;
  height: 80vh;
  max-height: 800px;
  background: linear-gradient(180deg, #0a0f1a 0%, #050810 100%);
  border: 1px solid rgba(16, 185, 129, 0.4);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow:
    0 0 60px rgba(16, 185, 129, 0.15),
    0 0 120px rgba(6, 182, 212, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* Terminal Header */
.terminal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(6, 182, 212, 0.05) 100%);
  border-bottom: 1px solid rgba(16, 185, 129, 0.3);
}

.terminal-header-left {
  display: flex;
  align-items: center;
  gap: 14px;
}

.terminal-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
}

.terminal-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.terminal-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 600;
  color: #ef4444;
  letter-spacing: 1px;
}

.terminal-status.connected {
  color: #10B981;
}

.status-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 8px currentColor;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.terminal-header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* Search */
.terminal-search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #64748b;
  transition: all 0.2s;
}

.terminal-search:focus-within {
  border-color: #10B981;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.terminal-search input {
  width: 180px;
  background: transparent;
  border: none;
  outline: none;
  color: #e2e8f0;
  font-size: 12px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

.terminal-search input::placeholder {
  color: #475569;
}

.search-count {
  font-size: 10px;
  color: #10B981;
  padding: 2px 6px;
  background: rgba(16, 185, 129, 0.15);
  border-radius: 4px;
}

/* Filters */
.terminal-filters {
  display: flex;
  gap: 4px;
}

.filter-btn {
  min-width: 44px;
  min-height: 44px;
  border-radius: 8px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.4);
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-btn:focus-visible {
  outline: 2px solid #10B981;
  outline-offset: 2px;
}

.filter-btn.active.error {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.5);
  color: #f87171;
}

.filter-btn.active.warning {
  background: rgba(245, 158, 11, 0.2);
  border-color: rgba(245, 158, 11, 0.5);
  color: #fbbf24;
}

.filter-btn.active.info {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  color: #60a5fa;
}

.filter-btn.active.debug {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
  color: #a78bfa;
}

/* Actions */
.terminal-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  min-width: 44px;
  min-height: 44px;
  border-radius: 8px;
  background: rgba(71, 85, 105, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.4);
  color: #94a3b8;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:focus-visible {
  outline: 2px solid #10B981;
  outline-offset: 2px;
}

.action-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.action-btn.active {
  background: rgba(16, 185, 129, 0.2);
  border-color: rgba(16, 185, 129, 0.5);
  color: #34d399;
}

.action-btn.close:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

/* Terminal Body */
.terminal-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.6;
  position: relative;
  background:
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(16, 185, 129, 0.02) 2px,
      rgba(16, 185, 129, 0.02) 4px
    );
}

/* Scan Line Effect */
.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(
    180deg,
    rgba(16, 185, 129, 0.3) 0%,
    transparent 100%
  );
  animation: scan 4s linear infinite;
  pointer-events: none;
  z-index: 10;
}

@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}

/* Empty State */
.terminal-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #475569;
  text-align: center;
}

.terminal-empty p {
  margin: 16px 0 8px;
  font-size: 16px;
  color: #64748b;
}

.terminal-empty span {
  font-size: 12px;
  color: #475569;
}

/* Log Entry */
.log-entry {
  display: flex;
  gap: 12px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(71, 85, 105, 0.15);
  transition: background 0.15s;
}

.log-entry:hover {
  background: rgba(16, 185, 129, 0.05);
}

.log-time {
  color: #475569;
  flex-shrink: 0;
  font-size: 11px;
}

.log-level {
  flex-shrink: 0;
  width: 60px;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.log-level.error { color: #f87171; }
.log-level.warning { color: #fbbf24; }
.log-level.info { color: #60a5fa; }
.log-level.debug { color: #a78bfa; }

.log-logger {
  color: #10B981;
  flex-shrink: 0;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11px;
}

.log-message {
  color: #e2e8f0;
  word-break: break-word;
  flex: 1;
}

.log-message :deep(mark) {
  background: rgba(16, 185, 129, 0.4);
  color: white;
  padding: 0 2px;
  border-radius: 2px;
}

/* Error/Warning row highlight */
.log-entry.error {
  background: rgba(239, 68, 68, 0.05);
  border-left: 2px solid #ef4444;
  padding-left: 10px;
}

.log-entry.warning {
  background: rgba(245, 158, 11, 0.05);
  border-left: 2px solid #f59e0b;
  padding-left: 10px;
}

/* Terminal Footer */
.terminal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  background: rgba(15, 23, 42, 0.8);
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.footer-stats {
  display: flex;
  gap: 20px;
}

.stat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #64748b;
}

.system-info {
  font-size: 10px;
  font-weight: 600;
  color: #10B981;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(16, 185, 129, 0.5);
}

/* Scrollbar */
.terminal-body::-webkit-scrollbar {
  width: 8px;
}

.terminal-body::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}

.terminal-body::-webkit-scrollbar-thumb {
  background: rgba(16, 185, 129, 0.3);
  border-radius: 4px;
}

.terminal-body::-webkit-scrollbar-thumb:hover {
  background: rgba(16, 185, 129, 0.5);
}

/* Transitions */
.terminal-fade-enter-active,
.terminal-fade-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.terminal-fade-enter-from,
.terminal-fade-leave-to {
  opacity: 0;
}

.terminal-fade-enter-from .terminal-dialog,
.terminal-fade-leave-to .terminal-dialog {
  transform: scale(0.95) translateY(20px);
}
</style>
