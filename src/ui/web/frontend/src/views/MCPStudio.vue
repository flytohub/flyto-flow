<template>
  <main class="mcp-studio">
    <header class="studio-header">
      <div class="studio-heading">
        <div class="studio-mark" aria-hidden="true"><Blocks :size="22" /></div>
        <div>
          <div class="studio-title-line">
            <h1>MCP Studio</h1>
            <span class="status-badge" :class="status.ok ? 'status-online' : 'status-offline'">
              <span class="status-dot" />
              {{ status.ok ? 'Online' : 'Offline' }}
            </span>
          </div>
          <p>{{ status.transport }} · {{ status.exposedToolCount }} tools · {{ accessLabel }}</p>
        </div>
      </div>
      <div class="studio-actions">
        <button
          class="icon-button"
          type="button"
          title="Refresh MCP status"
          :disabled="loading"
          @click="loadStatus"
        >
          <RefreshCw :size="17" :class="{ spin: loading }" />
          <span class="sr-only">Refresh MCP status</span>
        </button>
        <button class="primary-button" type="button" :disabled="creating" @click="createTool">
          <Loader2 v-if="creating" :size="17" class="spin" />
          <Plus v-else :size="17" />
          New MCP tool
        </button>
      </div>
    </header>

    <div v-if="error" class="error-banner" role="alert">
      <AlertTriangle :size="17" />
      <span>{{ error }}</span>
      <button type="button" @click="loadStatus">Retry</button>
    </div>

    <section class="server-bar" aria-label="MCP server">
      <div class="server-identity">
        <Server :size="18" />
        <div>
          <strong>{{ status.title }}</strong>
          <span>{{ status.name }}</span>
        </div>
      </div>
      <div class="endpoint-value">
        <span>Endpoint</span>
        <code>{{ status.serverUrl }}</code>
        <button class="inline-icon" type="button" title="Copy endpoint" @click="copyText(status.serverUrl, 'endpoint')">
          <Check v-if="copied === 'endpoint'" :size="15" />
          <Copy v-else :size="15" />
          <span class="sr-only">Copy endpoint</span>
        </button>
      </div>
      <div class="protocol-value">
        <span>Protocol</span>
        <strong>{{ latestProtocol }}</strong>
      </div>
    </section>

    <nav class="studio-tabs" aria-label="MCP Studio views">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        :class="{ active: activeTab === tab.id }"
        @click="activeTab = tab.id"
      >
        <component :is="tab.icon" :size="16" />
        {{ tab.label }}
        <span v-if="tab.id === 'tools'" class="tab-count">{{ status.exposedToolCount }}</span>
      </button>
    </nav>

    <section v-if="activeTab === 'tools'" class="tools-layout">
      <aside class="tool-index" aria-label="MCP tools">
        <label class="search-field">
          <Search :size="16" />
          <input v-model="search" type="search" placeholder="Search tools" />
        </label>
        <div class="tool-list">
          <button
            v-for="tool in visibleTools"
            :key="tool.name"
            class="tool-list-item"
            :class="{ selected: selectedTool?.name === tool.name }"
            type="button"
            @click="selectTool(tool)"
          >
            <span class="tool-icon"><Workflow :size="16" /></span>
            <span class="tool-copy">
              <strong>{{ tool.name }}</strong>
              <small>{{ tool.description || 'Workflow tool' }}</small>
            </span>
            <ChevronRight :size="16" />
          </button>
          <div v-if="!visibleTools.length" class="tool-empty">
            <SearchX v-if="search" :size="22" />
            <Blocks v-else :size="22" />
            <span>{{ search ? 'No matching tools' : 'No MCP tools yet' }}</span>
          </div>
        </div>
      </aside>

      <div v-if="selectedTool" class="tool-workbench">
        <div class="tool-header">
          <div>
            <div class="tool-name-line">
              <h2>{{ selectedTool.name }}</h2>
              <span>{{ selectedFields.length }} inputs</span>
            </div>
            <p>{{ selectedTool.description || 'Workflow-backed MCP tool' }}</p>
          </div>
          <router-link
            v-if="selectedSource.id"
            class="secondary-button"
            :to="`/templates/builder/${selectedSource.id}`"
          >
            <Pencil :size="15" />
            Edit workflow
          </router-link>
        </div>

        <div class="workbench-body">
          <form class="argument-form" @submit.prevent="runSelected">
            <div class="section-heading">
              <div>
                <h3>Arguments</h3>
                <span>JSON Schema</span>
              </div>
              <button class="text-button" type="button" @click="resetArguments">Reset</button>
            </div>

            <div v-if="selectedFields.length" class="field-grid">
              <div v-for="field in selectedFields" :key="field.name" class="argument-field">
                <span class="field-label">
                  <code>{{ field.name }}</code>
                  <em>{{ field.type }}</em>
                  <b v-if="field.required">Required</b>
                </span>
                <select
                  v-if="field.enumValues.length"
                  v-model="argumentValues[field.name]"
                  :aria-label="field.name"
                >
                  <option value="">Select value</option>
                  <option v-for="option in field.enumValues" :key="String(option)" :value="option">
                    {{ option }}
                  </option>
                </select>
                <label v-else-if="field.type === 'boolean'" class="boolean-control">
                  <input v-model="argumentValues[field.name]" :aria-label="field.name" type="checkbox" />
                  <span>{{ argumentValues[field.name] ? 'True' : 'False' }}</span>
                </label>
                <textarea
                  v-else-if="field.type === 'object' || field.type === 'array'"
                  v-model="argumentValues[field.name]"
                  :aria-label="field.name"
                  rows="5"
                  spellcheck="false"
                />
                <input
                  v-else
                  v-model="argumentValues[field.name]"
                  :aria-label="field.name"
                  :type="field.type === 'number' || field.type === 'integer' ? 'number' : 'text'"
                  :step="field.type === 'integer' ? '1' : 'any'"
                />
                <small v-if="field.description">{{ field.description }}</small>
              </div>
            </div>
            <div v-else class="no-arguments">
              <Braces :size="20" />
              <span>This tool accepts no declared arguments.</span>
            </div>

            <div v-if="runError" class="field-error" role="alert">{{ runError }}</div>
            <button class="run-button" type="submit" :disabled="running">
              <Loader2 v-if="running" :size="17" class="spin" />
              <Play v-else :size="17" fill="currentColor" />
              {{ running ? 'Running' : 'Run tool' }}
            </button>
          </form>

          <section class="result-panel" aria-live="polite">
            <div class="section-heading">
              <div>
                <h3>Response</h3>
                <span>{{ responseState }}</span>
              </div>
              <button
                v-if="formattedResponse"
                class="inline-icon"
                type="button"
                title="Copy response"
                @click="copyText(formattedResponse, 'response')"
              >
                <Check v-if="copied === 'response'" :size="15" />
                <Copy v-else :size="15" />
                <span class="sr-only">Copy response</span>
              </button>
            </div>
            <pre v-if="formattedResponse">{{ formattedResponse }}</pre>
            <div v-else class="response-empty">
              <SquareTerminal :size="23" />
              <span>Tool output</span>
            </div>
          </section>
        </div>
      </div>

      <div v-else class="workbench-empty">
        <Blocks :size="28" />
        <strong>{{ search ? 'No tool selected' : 'Create your first MCP tool' }}</strong>
        <button v-if="!search" class="primary-button" type="button" @click="createTool">
          <Plus :size="17" />
          New MCP tool
        </button>
      </div>
    </section>

    <section v-else-if="activeTab === 'connect'" class="connect-layout">
      <div class="client-selector">
        <button
          v-for="client in clients"
          :key="client.id"
          type="button"
          :class="{ active: selectedClientId === client.id }"
          @click="selectedClientId = client.id"
        >
          <TerminalSquare :size="18" />
          <span>{{ client.label }}</span>
          <small>{{ client.format }}</small>
        </button>
      </div>
      <div class="config-panel">
        <div class="section-heading">
          <div>
            <h2>{{ selectedClient.label }}</h2>
            <span>{{ selectedClient.format }}</span>
          </div>
          <button
            class="secondary-button"
            type="button"
            @click="copyText(selectedClient.content, 'config')"
          >
            <Check v-if="copied === 'config'" :size="15" />
            <Copy v-else :size="15" />
            {{ copied === 'config' ? 'Copied' : 'Copy' }}
          </button>
        </div>
        <pre>{{ selectedClient.content }}</pre>
      </div>
    </section>

    <section v-else class="audit-layout">
      <div class="audit-checks">
        <div v-for="checkItem in checks" :key="checkItem.id" class="audit-row">
          <span :class="checkItem.pass ? 'audit-pass' : 'audit-fail'">
            <CheckCircle2 v-if="checkItem.pass" :size="17" />
            <XCircle v-else :size="17" />
          </span>
          <strong>{{ checkItem.label }}</strong>
          <small>{{ checkItem.pass ? 'Pass' : 'Review' }}</small>
        </div>
      </div>
      <div class="protocol-panel">
        <div class="section-heading">
          <div>
            <h2>Protocol surface</h2>
            <span>{{ status.protocolVersions.length }} versions</span>
          </div>
          <ShieldCheck :size="20" />
        </div>
        <dl>
          <div><dt>Transport</dt><dd>{{ status.transport }}</dd></div>
          <div><dt>Access</dt><dd>{{ accessLabel }}</dd></div>
          <div><dt>Tools changed</dt><dd>{{ status.capabilities?.tools?.listChanged ? 'Notified' : 'Static' }}</dd></div>
          <div><dt>Evidence</dt><dd>{{ evidenceCount }}</dd></div>
        </dl>
      </div>
      <div class="history-panel">
        <div class="section-heading">
          <div>
            <h2>Session history</h2>
            <span>{{ history.length }} calls</span>
          </div>
          <button v-if="history.length" class="text-button" type="button" @click="history = []">Clear</button>
        </div>
        <div v-if="history.length" class="history-list">
          <button
            v-for="entry in history"
            :key="entry.id"
            type="button"
            @click="restoreHistory(entry)"
          >
            <span :class="entry.ok ? 'history-pass' : 'history-fail'" />
            <strong>{{ entry.tool }}</strong>
            <small>{{ entry.duration }} ms</small>
          </button>
        </div>
        <div v-else class="history-empty">No calls in this session.</div>
      </div>
    </section>
  </main>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  AlertTriangle,
  Blocks,
  Braces,
  Check,
  CheckCircle2,
  ChevronRight,
  Copy,
  FileCheck2,
  Loader2,
  Pencil,
  Play,
  PlugZap,
  Plus,
  RefreshCw,
  Search,
  SearchX,
  Server,
  ShieldCheck,
  SquareTerminal,
  TerminalSquare,
  Workflow,
  Wrench,
  XCircle,
} from 'lucide-vue-next'
import { callMcpTool, getMcpStatus } from '@/api/mcp'
import { templatesAPI } from '@/api/templates'
import {
  auditChecks,
  clientConfigurations,
  createMcpStarter,
  initialArguments,
  normalizeMcpStatus,
  parseArguments,
  schemaFields,
  toolSource,
} from '@/features/mcp/studioModel'

const router = useRouter()
const loading = ref(false)
const creating = ref(false)
const running = ref(false)
const error = ref('')
const runError = ref('')
const status = ref(normalizeMcpStatus({}))
const activeTab = ref('tools')
const search = ref('')
const selectedToolName = ref('')
const selectedClientId = ref('codex')
const argumentValues = ref({})
const response = ref(null)
const responseState = ref('Ready')
const copied = ref('')
const history = ref([])

const tabs = [
  { id: 'tools', label: 'Tools', icon: Wrench },
  { id: 'connect', label: 'Connect', icon: PlugZap },
  { id: 'audit', label: 'Audit', icon: FileCheck2 },
]

const visibleTools = computed(() => {
  const needle = search.value.trim().toLowerCase()
  if (!needle) return status.value.tools
  return status.value.tools.filter(tool => (
    `${tool.name} ${tool.description || ''}`.toLowerCase().includes(needle)
  ))
})
const selectedTool = computed(() => (
  status.value.tools.find(tool => tool.name === selectedToolName.value) || null
))
const selectedFields = computed(() => schemaFields(selectedTool.value))
const selectedSource = computed(() => toolSource(selectedTool.value))
const clients = computed(() => clientConfigurations(status.value))
const selectedClient = computed(() => (
  clients.value.find(client => client.id === selectedClientId.value) || clients.value[0]
))
const checks = computed(() => auditChecks(status.value))
const latestProtocol = computed(() => status.value.protocolVersions[0] || 'MCP')
const accessLabel = computed(() => {
  if (status.value.auth.localLoopbackAccountless) return 'Local accountless'
  if (status.value.auth.configured) return 'Bearer connected'
  return status.value.auth.required ? 'Bearer required' : 'Operator access'
})
const formattedResponse = computed(() => {
  if (!response.value) return ''
  return JSON.stringify(response.value, null, 2)
})
const evidenceCount = computed(() => (
  (Array.isArray(status.value.evidence) ? status.value.evidence.length : 0) +
  (Array.isArray(status.value.recentExecutions) ? status.value.recentExecutions.length : 0)
))

function selectTool(tool) {
  selectedToolName.value = tool.name
  resetArguments()
  response.value = null
  responseState.value = 'Ready'
  runError.value = ''
}

function resetArguments() {
  argumentValues.value = initialArguments(selectedTool.value)
  runError.value = ''
}

async function loadStatus() {
  loading.value = true
  error.value = ''
  const result = await getMcpStatus()
  status.value = normalizeMcpStatus(result)
  loading.value = false
  if (!status.value.ok) error.value = result.error || 'MCP status unavailable'
  if (!selectedTool.value && status.value.tools.length) selectTool(status.value.tools[0])
}

async function createTool() {
  if (creating.value) return
  creating.value = true
  error.value = ''
  const result = await templatesAPI.createTemplate(createMcpStarter(status.value.exposedToolCount + 1))
  creating.value = false
  if (!result.ok) {
    error.value = result.error || 'Unable to create MCP tool'
    return
  }
  router.push(`/templates/builder/${result.template.id}`)
}

async function runSelected() {
  if (!selectedTool.value || running.value) return
  runError.value = ''
  let args
  try {
    args = parseArguments(selectedTool.value, argumentValues.value)
  } catch (validationError) {
    runError.value = validationError.message
    return
  }

  running.value = true
  responseState.value = 'Running'
  const startedAt = performance.now()
  const result = await callMcpTool(selectedTool.value.name, args)
  const duration = Math.round(performance.now() - startedAt)
  running.value = false
  response.value = result.response || { error: result.error }
  responseState.value = result.ok ? 'Completed' : 'Failed'
  if (!result.ok) runError.value = result.error || 'Tool call failed'
  history.value = [{
    id: `${Date.now()}-${selectedTool.value.name}`,
    tool: selectedTool.value.name,
    args,
    response: response.value,
    ok: result.ok,
    duration,
  }, ...history.value].slice(0, 20)
}

function restoreHistory(entry) {
  const tool = status.value.tools.find(item => item.name === entry.tool)
  if (tool) {
    activeTab.value = 'tools'
    selectedToolName.value = tool.name
    argumentValues.value = { ...initialArguments(tool), ...entry.args }
    response.value = entry.response
    responseState.value = entry.ok ? 'Completed' : 'Failed'
  }
}

async function copyText(value, key) {
  if (!value || typeof navigator === 'undefined' || !navigator.clipboard) return
  await navigator.clipboard.writeText(String(value))
  copied.value = key
  window.setTimeout(() => { if (copied.value === key) copied.value = '' }, 1600)
}

onMounted(loadStatus)
</script>

<style scoped src="../features/mcp/studio.css"></style>
