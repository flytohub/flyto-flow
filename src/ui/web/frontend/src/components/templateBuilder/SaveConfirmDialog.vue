<!--
  SaveConfirmDialog.vue

  Wrapper around ConfirmDialog for unsaved changes confirmation.
  Provides a three-button dialog: Don't Save, Cancel, Save and Leave.

  This component delegates to ConfirmDialog for proper accessibility,
  focus management, and consistent styling.
-->
<template>
  <ConfirmDialog
    :show="show"
    :title="$t('templateBuilder.dialog.unsavedChanges')"
    :message="$t('templateBuilder.dialog.unsavedChangesMessage')"
    :confirm-text="$t('templateBuilder.dialog.saveAndLeave')"
    :cancel-text="$t('common.cancel')"
    :secondary-text="$t('templateBuilder.dialog.dontSave')"
    :show-secondary="true"
    variant="warning"
    @confirm="$emit('saveAndLeave')"
    @cancel="$emit('close')"
    @secondary="$emit('leaveWithoutSaving')"
  />
</template>

<script setup>
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

defineProps({
  show: {
    type: Boolean,
    default: false
  }
})

defineEmits(['close', 'leaveWithoutSaving', 'saveAndLeave'])
</script>
