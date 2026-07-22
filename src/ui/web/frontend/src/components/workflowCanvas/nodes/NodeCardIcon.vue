<template>
  <div class="node-icon-wrapper" :class="{ 'node-icon-wrapper--compact': compact }" :style="{ background: gradient }">
    <!-- Embedded image icon -->
    <img
      v-if="isUrlIcon"
      :src="icon.value || icon.url"
      class="node-icon-img"
      :class="{ 'node-icon-img--compact': compact }"
      :alt="label"
      @error="handleIconError"
    />
    <!-- Lucide component icon -->
    <component v-else :is="icon" :size="compact ? 28 : 24" class="node-icon" aria-hidden="true" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  icon: { type: [Object, Function], required: true },
  gradient: { type: String, required: true },
  label: { type: String, default: '' },
  compact: { type: Boolean, default: false }
})

const isUrlIcon = computed(() => {
  const value = props.icon?.value || props.icon?.url || ''
  return props.icon && typeof props.icon === 'object' && props.icon.type === 'url' && value.startsWith('data:image/')
})

const iconError = ref(false)
function handleIconError() {
  iconError.value = true
}
</script>

<style scoped>
.node-icon-wrapper {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow:
    0 4px 12px rgba(0, 0, 0, 0.25),
    0 0 10px rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.node-icon-wrapper--compact {
  width: 44px;
  height: 44px;
  border-radius: 10px;
}

.node-icon {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.2));
}

.node-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: inherit;
}

.node-icon-img--compact {
  width: 100%;
  height: 100%;
}
</style>
