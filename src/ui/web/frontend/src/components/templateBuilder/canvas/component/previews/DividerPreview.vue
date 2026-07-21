<template>
  <div class="divider-preview">
    <hr
      :class="['preview-divider', component.variant || 'solid']"
      :style="dividerStyle"
    />
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

const dividerStyle = computed(() => {
  const styles = {}
  if (props.component.color) {
    styles.borderColor = props.component.color
  }
  if (props.component.spacing) {
    styles.marginTop = `${props.component.spacing}px`
    styles.marginBottom = `${props.component.spacing}px`
  }
  return styles
})
</script>

<style scoped>
.divider-preview {
  width: 100%;
  padding: 8px 0;
}

.preview-divider {
  border: none;
  border-top: 1px solid #475569;
  margin: 0;
}

.preview-divider.solid {
  border-style: solid;
}

.preview-divider.dashed {
  border-style: dashed;
}

.preview-divider.dotted {
  border-style: dotted;
}

.preview-divider.thick {
  border-width: 2px;
}
</style>
