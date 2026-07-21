<template>
  <div class="messaging-integrations">
    <!-- Header -->
    <div class="page-header">
      <div class="header-content">
        <h1>訊息整合</h1>
        <p class="subtitle">管理 LINE、Telegram、Slack、Discord 等通訊平台整合</p>
      </div>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <Plus class="icon" />
        新增整合
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
      <Loader2 class="icon spinning" />
      <span>載入中...</span>
    </div>

    <!-- Empty State -->
    <div v-else-if="integrations.length === 0" class="empty-state">
      <MessageSquare class="empty-icon" />
      <h3>尚無訊息整合</h3>
      <p>新增一個整合來開始接收和處理訊息</p>
      <button class="btn btn-primary" @click="showCreateModal = true">
        <Plus class="icon" />
        新增整合
      </button>
    </div>

    <!-- Integrations Grid -->
    <div v-else class="integrations-grid">
      <div
        v-for="integration in integrations"
        :key="integration.id"
        class="integration-card"
        :class="{ disabled: integration.status !== 'active' }"
      >
        <div class="card-header">
          <div class="provider-info">
            <div
              class="provider-icon"
              :style="{ backgroundColor: getProviderColor(integration.provider) }"
            >
              <component :is="getProviderIcon(integration.provider)" class="icon" />
            </div>
            <div class="provider-details">
              <h3>{{ integration.name }}</h3>
              <span class="provider-name">{{ getProviderDisplayName(integration.provider) }}</span>
            </div>
          </div>
          <div class="card-actions">
            <button
              class="btn btn-icon"
              :class="integration.status === 'active' ? 'btn-success' : 'btn-secondary'"
              @click="toggleStatus(integration)"
              :title="integration.status === 'active' ? '停用' : '啟用'"
            >
              <Power class="icon" />
            </button>
            <button class="btn btn-icon" @click="editIntegration(integration)" title="設定">
              <Settings class="icon" />
            </button>
            <button class="btn btn-icon btn-danger" @click="confirmDelete(integration)" title="刪除">
              <Trash2 class="icon" />
            </button>
          </div>
        </div>

        <div class="card-body">
          <div class="stat-row">
            <span class="label">訊息數量</span>
            <span class="value">{{ integration.messageCount || 0 }}</span>
          </div>
          <div class="stat-row">
            <span class="label">最後活動</span>
            <span class="value">{{ formatTime(integration.lastWebhookAt) }}</span>
          </div>
          <div class="stat-row">
            <span class="label">狀態</span>
            <span class="status-badge" :class="integration.status">
              {{ integration.status === 'active' ? '運作中' : '已停用' }}
            </span>
          </div>
        </div>

        <div class="card-footer">
          <button class="btn btn-sm btn-secondary" @click="showWebhookUrl(integration)">
            <Link class="icon" />
            Webhook URL
          </button>
          <button class="btn btn-sm btn-secondary" @click="testConnection(integration)">
            <Zap class="icon" />
            測試連線
          </button>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <Modal v-model="showCreateModal" title="新增訊息整合" size="lg">
      <IntegrationForm
        v-if="showCreateModal"
        :providers="providers"
        @submit="handleCreate"
        @cancel="showCreateModal = false"
      />
    </Modal>

    <!-- Edit Modal -->
    <Modal v-model="showEditModal" title="編輯整合" size="lg">
      <IntegrationForm
        v-if="showEditModal && editingIntegration"
        :providers="providers"
        :integration="editingIntegration"
        @submit="handleUpdate"
        @cancel="showEditModal = false"
      />
    </Modal>

    <!-- Webhook URL Modal -->
    <Modal v-model="showWebhookModal" title="Webhook URL" size="md">
      <div class="webhook-modal" v-if="selectedIntegration">
        <p class="instructions">
          將此 URL 設定到 {{ getProviderDisplayName(selectedIntegration.provider) }} 的 Webhook 設定中：
        </p>
        <div class="url-box">
          <code>{{ getWebhookUrl(selectedIntegration) }}</code>
          <button class="btn btn-icon" @click="copyWebhookUrl(selectedIntegration)" aria-label="Copy URL">
            <Copy class="icon" />
          </button>
        </div>
        <div class="setup-instructions" v-html="getSetupInstructions(selectedIntegration.provider)"></div>
      </div>
    </Modal>

    <!-- Delete Confirmation -->
    <Modal v-model="showDeleteModal" title="確認刪除" size="sm">
      <div class="delete-confirm" v-if="deletingIntegration">
        <p>確定要刪除「{{ deletingIntegration.name }}」嗎？</p>
        <p class="warning">此操作無法復原，所有相關訊息也會被刪除。</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="showDeleteModal = false">取消</button>
          <button class="btn btn-danger" @click="handleDelete">刪除</button>
        </div>
      </div>
    </Modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useMessagingStore } from '@/stores/messaging'
import { useToast } from '@/composables/useToast'
import Modal from '@/components/common/Modal.vue'
import IntegrationForm from '@/components/messaging/IntegrationForm.vue'
import { formatRelativeTime } from '@/utils/formatTime'
import DOMPurify from 'dompurify'
import {
  Plus,
  MessageSquare,
  Loader2,
  Power,
  Settings,
  Trash2,
  Link,
  Zap,
  Copy,
  Hash,
  Send,
  MessageCircle,
} from 'lucide-vue-next'

const store = useMessagingStore()
const toast = useToast()

// State
const showCreateModal = ref(false)
const showEditModal = ref(false)
const showWebhookModal = ref(false)
const showDeleteModal = ref(false)
const editingIntegration = ref(null)
const selectedIntegration = ref(null)
const deletingIntegration = ref(null)

// Computed
const loading = computed(() => store.loading)
const integrations = computed(() => store.integrations)
const providers = computed(() => store.providers)

// Provider helpers
const providerIcons = {
  line: MessageCircle,
  telegram: Send,
  slack: Hash,
  discord: MessageSquare,
}

const providerColors = {
  line: '#06C755',
  telegram: '#0088CC',
  slack: '#4A154B',
  discord: '#5865F2',
}

function getProviderIcon(provider) {
  return providerIcons[provider] || MessageSquare
}

function getProviderColor(provider) {
  return providerColors[provider] || '#6366F1'
}

function getProviderDisplayName(provider) {
  const names = {
    line: 'LINE',
    telegram: 'Telegram',
    slack: 'Slack',
    discord: 'Discord',
  }
  return names[provider] || provider
}

function getWebhookUrl(integration) {
  const baseUrl = window.location.origin
  return `${baseUrl}/api/webhooks/messaging/${integration.webhookId}`
}

function getSetupInstructions(provider) {
  const p = providers.value.find(p => p.name === provider)
  if (p?.setupInstructions) {
    return DOMPurify.sanitize(p.setupInstructions.replace(/\n/g, '<br>'))
  }
  return ''
}

// Time formatting — delegated to shared utility
function formatTime(timestamp) {
  return formatRelativeTime(timestamp)
}

// Actions
async function toggleStatus(integration) {
  const enable = integration.status !== 'active'
  const result = await store.toggleIntegration(integration.id, enable)
  if (result.ok) {
    toast.success(enable ? '整合已啟用' : '整合已停用')
  } else {
    toast.error(result.error || '操作失敗')
  }
}

function editIntegration(integration) {
  editingIntegration.value = integration
  showEditModal.value = true
}

function showWebhookUrl(integration) {
  selectedIntegration.value = integration
  showWebhookModal.value = true
}

async function copyWebhookUrl(integration) {
  const url = getWebhookUrl(integration)
  await navigator.clipboard.writeText(url)
  toast.success('已複製到剪貼簿')
}

async function testConnection(integration) {
  toast.info('測試連線中...')
  const result = await store.testIntegration(integration.id)
  if (result.ok) {
    toast.success(`連線成功！Bot: ${result.botName || result.botId}`)
  } else {
    toast.error(`連線失敗: ${result.error}`)
  }
}

function confirmDelete(integration) {
  deletingIntegration.value = integration
  showDeleteModal.value = true
}

async function handleCreate(data) {
  const result = await store.createIntegration(data)
  if (result.ok) {
    showCreateModal.value = false
    toast.success('整合已建立')
    // Show webhook URL
    selectedIntegration.value = result.integration
    selectedIntegration.value.webhookId = result.webhookUrl?.split('/').pop()
    showWebhookModal.value = true
  } else {
    toast.error(result.error || '建立失敗')
  }
}

async function handleUpdate(data) {
  const result = await store.updateIntegration(editingIntegration.value.id, data)
  if (result.ok) {
    showEditModal.value = false
    editingIntegration.value = null
    toast.success('整合已更新')
  } else {
    toast.error(result.error || '更新失敗')
  }
}

async function handleDelete() {
  const result = await store.deleteIntegration(deletingIntegration.value.id)
  if (result.ok) {
    showDeleteModal.value = false
    deletingIntegration.value = null
    toast.success('整合已刪除')
  } else {
    toast.error(result.error || '刪除失敗')
  }
}

// Lifecycle
onMounted(async () => {
  await Promise.all([
    store.loadProviders(),
    store.loadIntegrations(),
  ])
})
</script>

<style scoped>
.messaging-integrations {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-content h1 {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
}

.subtitle {
  color: var(--text-secondary);
  margin: 4px 0 0;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.integrations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.integration-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.2s;
}

.integration-card:hover {
  border-color: var(--primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.integration-card.disabled {
  opacity: 0.6;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.provider-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.provider-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.provider-icon .icon {
  width: 20px;
  height: 20px;
}

.provider-details h3 {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
}

.provider-name {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-actions {
  display: flex;
  gap: 4px;
}

.card-body {
  padding: 16px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid var(--border-color);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-row .label {
  color: var(--text-secondary);
  font-size: 14px;
}

.stat-row .value {
  font-weight: 500;
}

.status-badge {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
}

.status-badge.active {
  background: var(--success-bg);
  color: var(--success);
}

.status-badge.disabled {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
}

.card-footer {
  display: flex;
  gap: 8px;
  padding: 12px 16px;
  background: var(--bg-tertiary);
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn .icon {
  width: 16px;
  height: 16px;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-danger {
  background: transparent;
  color: var(--danger);
}

.btn-danger:hover {
  background: var(--danger-bg);
}

.btn-success {
  background: var(--success-bg);
  color: var(--success);
}

.btn-icon {
  padding: 6px;
  background: transparent;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 13px;
}

.webhook-modal .instructions {
  margin-bottom: 12px;
  color: var(--text-secondary);
}

.url-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: var(--bg-tertiary);
  border-radius: 8px;
  margin-bottom: 16px;
}

.url-box code {
  flex: 1;
  font-family: monospace;
  font-size: 13px;
  word-break: break-all;
}

.setup-instructions {
  font-size: 13px;
  color: var(--text-secondary);
  white-space: pre-wrap;
}

.delete-confirm .warning {
  color: var(--danger);
  font-size: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 16px;
}
</style>
