<template>
  <ConfirmDialog
    :show="state.show"
    :title="state.title"
    :message="state.message"
    :confirm-text="state.confirmText"
    :cancel-text="state.cancelText"
    :variant="state.type === 'danger' ? 'danger' : state.type === 'warning' ? 'warning' : 'primary'"
    @confirm="confirm"
    @cancel="cancel"
  />
</template>

<script setup>
import ConfirmDialog from './ConfirmDialog.vue'
import { useConfirm } from '../../composables/useConfirm'

const { state, confirm, cancel } = useConfirm()
</script>
