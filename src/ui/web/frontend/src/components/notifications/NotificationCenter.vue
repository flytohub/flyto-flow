<template>
  <div class="notification-center" ref="containerRef">
    <!-- Trigger Button -->
    <button
      @click="toggleDropdown"
      aria-label="Notifications"
      class="notification-trigger"
      :class="{ 'has-unread': unreadCount > 0 }"
    >
      <Bell :size="20" />
      <span v-if="unreadCount > 0" class="unread-badge">
        {{ unreadCount > 99 ? '99+' : unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <Transition name="dropdown">
      <div v-if="isOpen" class="notification-dropdown">
        <!-- Header -->
        <div class="dropdown-header">
          <h3 class="dropdown-title">{{ $t('notifications.title') }}</h3>
          <button
            v-if="unreadCount > 0"
            @click="handleMarkAllRead"
            class="mark-all-btn"
            :disabled="markingAll"
          >
            <CheckCheck :size="16" />
            {{ $t('notifications.markAllRead') }}
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading-state">
          <Loader2 class="spinner" :size="24" />
        </div>

        <!-- Empty State -->
        <div v-else-if="notifications.length === 0" class="empty-state">
          <BellOff :size="40" class="empty-icon" />
          <p class="empty-text">{{ $t('notifications.empty') }}</p>
        </div>

        <!-- Notification List -->
        <div v-else class="notification-list">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            class="notification-item"
            :class="{ unread: !notification.isRead }"
            @click="handleNotificationClick(notification)"
          >
            <!-- Icon -->
            <div class="notification-icon" :class="getIconClass(notification.type)">
              <component :is="getIcon(notification.type)" :size="16" />
            </div>

            <!-- Content -->
            <div class="notification-content">
              <p class="notification-title">{{ notification.title }}</p>
              <p class="notification-message">{{ notification.message }}</p>
              <span class="notification-time">{{ formatTime(notification.createdAt) }}</span>
            </div>

            <!-- Actions -->
            <button
              @click.stop="handleDelete(notification.id)"
              aria-label="Delete notification"
              class="delete-btn"
            >
              <X :size="14" />
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div v-if="hasMore" class="dropdown-footer">
          <button @click="loadMore" class="load-more-btn" :disabled="loadingMore">
            <Loader2 v-if="loadingMore" class="spinner" :size="16" />
            <span v-else>{{ $t('notifications.loadMore') }}</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  Bell, BellOff, CheckCheck, X, Loader2,
  UserPlus, ShoppingCart, Star, MessageSquare,
  AlertCircle, AlertTriangle, CheckCircle, FileText
} from 'lucide-vue-next'
import notificationsAPI from '@/api/notifications'
import { DEFAULTS } from '@/config/defaults'

const router = useRouter()
const { t } = useI18n()

const containerRef = ref(null)
const isOpen = ref(false)
const loading = ref(false)
const loadingMore = ref(false)
const markingAll = ref(false)
const notifications = ref([])
const unreadCount = ref(0)
const page = ref(1)
const total = ref(0)
const PAGE_SIZE = DEFAULTS.PAGINATION.SMALL

const hasMore = computed(() => notifications.value.length < total.value)

const ICON_MAP = {
  follow: UserPlus,
  purchase: ShoppingCart,
  sale: ShoppingCart,
  review: Star,
  message: MessageSquare,
  template_approved: CheckCircle,
  template_rejected: AlertCircle,
  execution_failed: AlertTriangle,
  system: Bell,
  default: FileText
}

const ICON_CLASS_MAP = {
  follow: 'icon-follow',
  purchase: 'icon-purchase',
  sale: 'icon-sale',
  review: 'icon-review',
  message: 'icon-message',
  template_approved: 'icon-success',
  template_rejected: 'icon-error',
  execution_failed: 'icon-execution-failed',
  system: 'icon-system'
}

function getIcon(type) {
  return ICON_MAP[type] || ICON_MAP.default
}

function getIconClass(type) {
  return ICON_CLASS_MAP[type] || ''
}

function formatTime(dateStr) {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now - date
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return t('notifications.justNow')
  if (minutes < 60) return t('notifications.minutesAgo', { count: minutes })
  if (hours < 24) return t('notifications.hoursAgo', { count: hours })
  if (days < 7) return t('notifications.daysAgo', { count: days })
  return date.toLocaleDateString()
}

function toggleDropdown() {
  isOpen.value = !isOpen.value
  if (isOpen.value && notifications.value.length === 0) {
    fetchNotifications()
  }
}

async function fetchNotifications(append = false) {
  if (!append) {
    loading.value = true
    page.value = 1
  } else {
    loadingMore.value = true
  }

  try {
    const response = await notificationsAPI.getNotifications({
      page: page.value,
      pageSize: PAGE_SIZE
    })

    if (append) {
      notifications.value.push(...response.items)
    } else {
      notifications.value = response.items
    }
    total.value = response.total
  } catch (err) {
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

async function fetchUnreadCount() {
  try {
    unreadCount.value = await notificationsAPI.getUnreadCount()
  } catch (err) {
  }
}

function loadMore() {
  page.value++
  fetchNotifications(true)
}

async function handleNotificationClick(notification) {
  if (!notification.isRead) {
    try {
      await notificationsAPI.markAsRead(notification.id)
      notification.isRead = true
      unreadCount.value = Math.max(0, unreadCount.value - 1)
    } catch (err) {
    }
  }

  // Determine navigation target
  const targetUrl = notification.actionUrl || getNotificationUrl(notification)
  if (targetUrl) {
    router.push(targetUrl)
    isOpen.value = false
  }
}

function getNotificationUrl(notification) {
  if (notification.referenceType === 'execution' && notification.referenceId) {
    return `/executions/${notification.referenceId}`
  }
  return null
}

async function handleMarkAllRead() {
  markingAll.value = true
  try {
    await notificationsAPI.markAllAsRead()
    notifications.value.forEach(n => n.isRead = true)
    unreadCount.value = 0
  } catch (err) {
  } finally {
    markingAll.value = false
  }
}

async function handleDelete(notificationId) {
  try {
    await notificationsAPI.deleteNotification(notificationId)
    const idx = notifications.value.findIndex(n => n.id === notificationId)
    if (idx !== -1) {
      if (!notifications.value[idx].isRead) {
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      notifications.value.splice(idx, 1)
      total.value--
    }
  } catch (err) {
  }
}

function handleClickOutside(event) {
  if (containerRef.value && !containerRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

// Store interval reference for cleanup
let pollInterval = null

onMounted(() => {
  fetchUnreadCount()
  document.addEventListener('click', handleClickOutside)

  // Clear any existing interval before creating new one (safeguard for HMR/edge cases)
  if (pollInterval) {
    clearInterval(pollInterval)
  }
  // Poll for new notifications
  pollInterval = setInterval(fetchUnreadCount, DEFAULTS.TIMING.POLL_NOTIFICATIONS)
})

onUnmounted(() => {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-trigger {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.2s;
}

.notification-trigger:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.notification-trigger.has-unread {
  color: #fff;
}

.unread-badge {
  position: absolute;
  top: 4px;
  right: 4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: linear-gradient(135deg, #ef4444, #dc2626);
  color: #fff;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.notification-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  max-height: 480px;
  background: rgba(30, 30, 40, 0.98);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

.dropdown-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dropdown-title {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.mark-all-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: rgba(139, 92, 246, 0.2);
  border: none;
  border-radius: 8px;
  color: #a78bfa;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.mark-all-btn:hover:not(:disabled) {
  background: rgba(139, 92, 246, 0.3);
}

.mark-all-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state,
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  color: rgba(255, 255, 255, 0.4);
}

.spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  margin-bottom: 12px;
  opacity: 0.3;
}

.empty-text {
  margin: 0;
  font-size: 14px;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  max-height: 360px;
}

.notification-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.2s;
  position: relative;
}

.notification-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.notification-item.unread {
  background: rgba(139, 92, 246, 0.08);
}

.notification-item.unread::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, #8b5cf6, #ec4899);
}

.notification-icon {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

.notification-icon.icon-follow { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.notification-icon.icon-purchase { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.notification-icon.icon-sale { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.notification-icon.icon-review { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.notification-icon.icon-message { background: rgba(139, 92, 246, 0.2); color: #a78bfa; }
.notification-icon.icon-success { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.notification-icon.icon-error { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.notification-icon.icon-execution-failed { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.notification-icon.icon-system { background: rgba(107, 114, 128, 0.2); color: #9ca3af; }

.notification-content {
  flex: 1;
  min-width: 0;
}

.notification-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notification-message {
  margin: 0 0 6px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notification-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.delete-btn {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all 0.2s;
}

.notification-item:hover .delete-btn {
  opacity: 1;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.dropdown-footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.load-more-btn {
  width: 100%;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: none;
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.load-more-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.load-more-btn:disabled {
  cursor: not-allowed;
}

/* Dropdown Animation */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: all 0.2s ease;
}

.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (max-width: 480px) {
  .notification-dropdown {
    position: fixed;
    top: 60px;
    left: 10px;
    right: 10px;
    width: auto;
  }
}
</style>
