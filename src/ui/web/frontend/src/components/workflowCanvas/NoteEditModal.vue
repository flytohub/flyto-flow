<template>
  <BaseModal
    :show="show"
    :title="hasDescription ? $t('workflow.editDescription', 'Edit Description') : $t('workflow.addDescription', 'Add Description')"
    size="md"
    @close="handleCancel"
  >
    <div class="note-edit-content">
      <p class="note-hint">{{ $t('workflow.descriptionHint', 'Add a description to document this node\'s purpose.') }}</p>
      <AppTextarea
        ref="appTextareaRef"
        v-model="noteText"
        :rows="4"
        :placeholder="$t('workflow.descriptionPlaceholder', 'Describe what this node does...')"
        @keydown.enter.ctrl="handleSave"
        @keydown.enter.meta="handleSave"
      />
      <p class="note-shortcut">{{ $t('workflow.descriptionSaveShortcut', 'Press Ctrl+Enter to save') }}</p>
    </div>

    <template #footer>
      <button class="btn btn-secondary" @click="handleCancel">
        {{ $t('common.cancel', 'Cancel') }}
      </button>
      <button class="btn btn-danger" v-if="hasNote" @click="handleDelete">
        {{ $t('common.delete', 'Delete') }}
      </button>
      <button class="btn btn-primary" @click="handleSave">
        {{ $t('common.save', 'Save') }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, watch, nextTick, computed } from 'vue'
import BaseModal from '@/components/common/BaseModal.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  initialNote: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['save', 'delete', 'close'])

const appTextareaRef = ref(null)
const noteText = ref('')

const hasDescription = computed(() => props.initialNote && props.initialNote.trim().length > 0)

// Sync with initial note when modal opens
watch(() => props.show, async (newVal) => {
  if (newVal) {
    noteText.value = props.initialNote || ''
    await nextTick()
    const el = appTextareaRef.value?.textareaRef
    el?.focus()
    // Select all text if editing existing description
    if (hasDescription.value) {
      el?.select()
    }
  }
})

function handleSave() {
  emit('save', noteText.value.trim())
}

function handleDelete() {
  emit('delete')
}

function handleCancel() {
  emit('close')
}
</script>

<style scoped>
.note-edit-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.note-hint {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
}


.note-shortcut {
  margin: 0;
  font-size: 11px;
  color: #64748b;
  text-align: right;
}

/* Button styles */
.btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-secondary {
  background: rgba(71, 85, 105, 0.3);
  color: #cbd5e1;
}

.btn-secondary:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #f1f5f9;
}

.btn-primary {
  background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
  color: white;
}

.btn-primary:hover {
  background: linear-gradient(135deg, #A78BFA 0%, #8B5CF6 100%);
}

.btn-danger {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.btn-danger:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #fca5a5;
}
</style>
