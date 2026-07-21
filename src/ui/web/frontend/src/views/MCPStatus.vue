<template>
  <main class="mcp-page">
    <header class="mcp-header">
      <div>
        <p class="mcp-kicker">MCP</p>
        <h1>Workflow Tools</h1>
      </div>
      <button class="mcp-action" type="button" :disabled="loading" @click="loadStatus">
        <RefreshCw :size="16" :class="{ spin: loading }" />
        <span>Refresh</span>
      </button>
    </header>

    <p v-if="error" class="mcp-error">
      <AlertCircle :size="16" />
      <span>{{ error }}</span>
    </p>

    <section class="mcp-grid">
      <div class="mcp-panel">
        <div class="mcp-panel-title">
          <Cable :size="17" />
          Endpoint
        </div>
        <dl class="mcp-facts">
          <div>
            <dt>Transport</dt>
            <dd>{{ status?.transport || 'streamable-http' }}</dd>
          </div>
          <div>
            <dt>Server URL</dt>
            <dd>{{ status?.serverUrl || '-' }}</dd>
          </div>
          <div>
            <dt>Auth</dt>
            <dd>{{ status?.auth?.configured ? 'Bearer token active' : 'Bearer token required' }}</dd>
          </div>
        </dl>
      </div>

      <div class="mcp-panel">
        <div class="mcp-panel-title">
          <Wrench :size="17" />
          Tools
        </div>
        <strong class="mcp-count">{{ status?.exposedToolCount ?? 0 }}</strong>
        <div class="mcp-tools">
          <div v-for="tool in tools" :key="tool.name" class="mcp-tool">
            <span>{{ tool.name }}</span>
            <small>{{ tool.description }}</small>
          </div>
          <p v-if="!tools.length" class="mcp-muted">No exposed tools.</p>
        </div>
      </div>
    </section>

    <section class="mcp-configs">
      <div class="mcp-code-panel">
        <div class="mcp-panel-title">
          <Terminal :size="17" />
          Claude
          <button class="mcp-icon-btn" type="button" @click="copyText(claudeConfig)">
            <Copy :size="15" />
          </button>
        </div>
        <pre>{{ claudeConfig }}</pre>
      </div>

      <div class="mcp-code-panel">
        <div class="mcp-panel-title">
          <Terminal :size="17" />
          Codex
          <button class="mcp-icon-btn" type="button" @click="copyText(codexConfig)">
            <Copy :size="15" />
          </button>
        </div>
        <pre>{{ codexConfig }}</pre>
      </div>
    </section>

    <section class="mcp-panel">
      <div class="mcp-panel-title">
        <CheckCircle2 :size="17" />
        Evidence
      </div>
      <div class="mcp-evidence">
        <span>{{ executions.length }} executions</span>
        <span>{{ evidence.length }} evidence items</span>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  AlertCircle,
  Cable,
  CheckCircle2,
  Copy,
  RefreshCw,
  Terminal,
  Wrench,
} from 'lucide-vue-next'
import { getMcpStatus } from '@/api/mcp'

const loading = ref(false)
const error = ref('')
const status = ref(null)

const tools = computed(() => status.value?.tools || [])
const executions = computed(() => status.value?.recentExecutions || [])
const evidence = computed(() => status.value?.evidence || [])
const claudeConfig = computed(() => JSON.stringify(status.value?.setup?.claudeCode || {}, null, 2))
const codexConfig = computed(() => status.value?.setup?.codexToml || '')

async function loadStatus() {
  error.value = ''
  loading.value = true
  try {
    const result = await getMcpStatus()
    status.value = result
    if (!result.ok) error.value = result.error || 'MCP status unavailable'
  } finally {
    loading.value = false
  }
}

async function copyText(text) {
  if (!text || typeof navigator === 'undefined' || !navigator.clipboard) return
  await navigator.clipboard.writeText(text)
}

onMounted(loadStatus)
</script>

<style scoped>
.mcp-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 20px 56px;
  color: #e2e8f0;
}

.mcp-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.mcp-kicker {
  margin: 0 0 4px;
  color: #2563eb;
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0;
  text-transform: uppercase;
}

.mcp-header h1 {
  margin: 0;
  color: #f8fafc;
  font-size: 40px;
  line-height: 1.08;
  letter-spacing: 0;
}

.mcp-action,
.mcp-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 36px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #ffffff;
  color: #0f172a;
  font-weight: 700;
}

.mcp-action {
  padding: 0 14px;
}

.mcp-icon-btn {
  margin-left: auto;
  width: 34px;
}

.mcp-action:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.spin {
  animation: mcp-spin 0.9s linear infinite;
}

@keyframes mcp-spin {
  to {
    transform: rotate(360deg);
  }
}

.mcp-error {
  display: flex;
  gap: 8px;
  align-items: center;
  margin: 0 0 16px;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 10px 12px;
  background: #fef2f2;
  color: #991b1b;
}

.mcp-grid,
.mcp-configs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.mcp-panel,
.mcp-code-panel {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
  background: #ffffff;
  color: #0f172a;
}

.mcp-panel-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 14px;
  color: #334155;
  font-size: 14px;
  font-weight: 800;
}

.mcp-facts {
  display: grid;
  gap: 12px;
  margin: 0;
}

.mcp-facts div {
  display: grid;
  gap: 3px;
}

.mcp-facts dt,
.mcp-muted,
.mcp-tool small {
  color: #64748b;
  font-size: 12px;
}

.mcp-facts dd {
  margin: 0;
  overflow-wrap: anywhere;
  font-weight: 700;
}

.mcp-count {
  display: block;
  margin-bottom: 12px;
  font-size: 32px;
  line-height: 1;
}

.mcp-tools {
  display: grid;
  gap: 8px;
}

.mcp-tool {
  display: grid;
  gap: 3px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px;
}

.mcp-tool span {
  overflow-wrap: anywhere;
  font-size: 13px;
  font-weight: 800;
}

.mcp-code-panel pre {
  min-height: 220px;
  max-height: 340px;
  overflow: auto;
  margin: 0;
  border-radius: 8px;
  padding: 14px;
  background: #0f172a;
  color: #e2e8f0;
  font-size: 12px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}

.mcp-evidence {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.mcp-evidence span {
  border-radius: 999px;
  padding: 7px 10px;
  background: #f1f5f9;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
}

@media (max-width: 760px) {
  .mcp-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .mcp-grid,
  .mcp-configs {
    grid-template-columns: 1fr;
  }

  .mcp-header h1 {
    font-size: 30px;
  }
}
</style>
