<template>
  <div>
    <!-- Category Header -->
    <div class="flex items-center gap-3 mb-4">
      <div
        class="w-8 h-8 rounded-lg flex items-center justify-center"
        :style="{
          backgroundColor: color + '20',
          boxShadow: `0 0 20px ${color}30`
        }"
      >
        <component :is="icon" :size="16" :style="{ color: color }" />
      </div>
      <span class="text-sm font-semibold text-white">{{ label }}</span>
      <span class="px-2 py-0.5 bg-white/10 text-gray-400 text-xs rounded-md font-medium">
        {{ modules.length }}
      </span>
    </div>

    <!-- Module Cards Grid — same ModuleCard as ModuleSelector -->
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
      <!-- Create Template Card (first slot, only for my-templates) -->
      <button
        v-if="showCreateCard"
        class="create-template-card"
        @click="$emit('create-template')"
      >
        <Plus :size="24" class="text-purple-400" />
        <span class="text-xs font-medium text-gray-400 mt-1">New Template</span>
      </button>

      <ModuleCard
        v-for="module in modules"
        :key="module.moduleId || module.module"
        :module="module"
        @select="$emit('select-module', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Plus } from 'lucide-vue-next'
import ModuleCard from '../ModuleCard.vue'
import { useModuleCategories } from '../../composables/useModuleCategories'

const props = defineProps({
  category: {
    type: String,
    required: true
  },
  modules: {
    type: Array,
    required: true
  },
  showCreateCard: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select-module', 'create-template'])

const { getCategoryLabel, getCategoryColor, getCategoryIcon } = useModuleCategories()

const label = computed(() => getCategoryLabel(props.category))
const color = computed(() => getCategoryColor(props.category))
const icon = computed(() => getCategoryIcon(props.category))
</script>

<style scoped>
.create-template-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-height: 72px;
  border: 2px dashed rgba(139, 92, 246, 0.3);
  border-radius: 12px;
  background: rgba(139, 92, 246, 0.05);
  cursor: pointer;
  transition: all 0.2s ease;
}

.create-template-card:hover {
  border-color: rgba(139, 92, 246, 0.6);
  background: rgba(139, 92, 246, 0.1);
  transform: translateY(-1px);
}
</style>
