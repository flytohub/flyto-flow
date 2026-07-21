<template>
  <div class="skeleton-card" :class="[`variant-${variant}`]">
    <div v-if="showImage" class="skeleton-image skeleton-pulse"></div>
    <div class="skeleton-content">
      <div class="skeleton-title skeleton-pulse"></div>
      <div v-if="showDescription" class="skeleton-description">
        <div class="skeleton-line skeleton-pulse"></div>
        <div class="skeleton-line skeleton-line-short skeleton-pulse"></div>
      </div>
      <div v-if="showMeta" class="skeleton-meta">
        <div class="skeleton-avatar skeleton-pulse"></div>
        <div class="skeleton-meta-text skeleton-pulse"></div>
      </div>
      <div v-if="showActions" class="skeleton-actions">
        <div class="skeleton-button skeleton-pulse"></div>
        <div class="skeleton-button skeleton-button-small skeleton-pulse"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'card',
    validator: (v) => ['card', 'list', 'compact'].includes(v)
  },
  showImage: {
    type: Boolean,
    default: true
  },
  showDescription: {
    type: Boolean,
    default: true
  },
  showMeta: {
    type: Boolean,
    default: true
  },
  showActions: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.skeleton-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  overflow: hidden;
}

.skeleton-pulse {
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.03) 25%,
    rgba(255, 255, 255, 0.08) 50%,
    rgba(255, 255, 255, 0.03) 75%
  );
  background-size: 200% 100%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Card variant */
.variant-card .skeleton-image {
  height: 160px;
  width: 100%;
}

.variant-card .skeleton-content {
  padding: 16px;
}

.variant-card .skeleton-title {
  height: 20px;
  width: 70%;
  border-radius: 4px;
  margin-bottom: 12px;
}

.variant-card .skeleton-line {
  height: 14px;
  width: 100%;
  border-radius: 4px;
  margin-bottom: 8px;
}

.variant-card .skeleton-line-short {
  width: 60%;
}

.variant-card .skeleton-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.variant-card .skeleton-avatar {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  flex-shrink: 0;
}

.variant-card .skeleton-meta-text {
  height: 14px;
  width: 100px;
  border-radius: 4px;
}

/* List variant */
.variant-list {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
}

.variant-list .skeleton-image {
  width: 80px;
  height: 80px;
  border-radius: 12px;
  flex-shrink: 0;
}

.variant-list .skeleton-content {
  flex: 1;
}

.variant-list .skeleton-title {
  height: 18px;
  width: 50%;
  border-radius: 4px;
  margin-bottom: 8px;
}

.variant-list .skeleton-line {
  height: 14px;
  width: 80%;
  border-radius: 4px;
  margin-bottom: 6px;
}

.variant-list .skeleton-line-short {
  width: 40%;
}

.variant-list .skeleton-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
}

.variant-list .skeleton-avatar {
  width: 24px;
  height: 24px;
  border-radius: 6px;
}

.variant-list .skeleton-meta-text {
  height: 12px;
  width: 80px;
  border-radius: 4px;
}

/* Compact variant */
.variant-compact {
  padding: 12px;
}

.variant-compact .skeleton-image {
  display: none;
}

.variant-compact .skeleton-title {
  height: 16px;
  width: 60%;
  border-radius: 4px;
  margin-bottom: 8px;
}

.variant-compact .skeleton-line {
  height: 12px;
  width: 100%;
  border-radius: 4px;
}

.variant-compact .skeleton-line-short {
  width: 50%;
}

/* Actions */
.skeleton-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.skeleton-button {
  height: 36px;
  width: 100px;
  border-radius: 8px;
}

.skeleton-button-small {
  width: 36px;
}
</style>
