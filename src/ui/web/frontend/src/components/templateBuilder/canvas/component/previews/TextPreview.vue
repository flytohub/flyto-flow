<template>
  <div class="text-preview">
    <p
      :class="['preview-text', component.variant || 'body']"
      :style="textStyle"
    >
      {{ component.text || 'Text content' }}
    </p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  component: {
    type: Object,
    required: true
  },
  editable: {
    type: Boolean,
    default: true
  }
})

const textStyle = computed(() => {
  const styles = {}
  if (props.component.align) {
    styles.textAlign = props.component.align
  }
  if (props.component.color) {
    styles.color = props.component.color
  }
  return styles
})
</script>

<style scoped>
.text-preview {
  width: 100%;
}

.preview-text {
  margin: 0;
  line-height: 1.6;
}

.preview-text.body {
  font-size: 14px;
  color: #cbd5e1;
}

.preview-text.caption {
  font-size: 12px;
  color: #94a3b8;
}

.preview-text.small {
  font-size: 11px;
  color: #64748b;
}

.preview-text.lead {
  font-size: 16px;
  color: #e2e8f0;
}
</style>
