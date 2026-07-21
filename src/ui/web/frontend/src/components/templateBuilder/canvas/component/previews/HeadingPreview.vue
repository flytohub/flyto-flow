<template>
  <div class="heading-preview">
    <component
      :is="headingTag"
      :class="['preview-heading', `level-${component.level || 2}`]"
      :style="headingStyle"
    >
      {{ component.text || 'Heading' }}
    </component>
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

const headingTag = computed(() => {
  const level = props.component.level || 2
  return `h${Math.min(Math.max(level, 1), 6)}`
})

const headingStyle = computed(() => {
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
.heading-preview {
  width: 100%;
}

.preview-heading {
  margin: 0;
  color: #f1f5f9;
  font-weight: 600;
  line-height: 1.3;
}

.preview-heading.level-1 {
  font-size: 28px;
}

.preview-heading.level-2 {
  font-size: 24px;
}

.preview-heading.level-3 {
  font-size: 20px;
}

.preview-heading.level-4 {
  font-size: 18px;
}

.preview-heading.level-5 {
  font-size: 16px;
}

.preview-heading.level-6 {
  font-size: 14px;
}
</style>
