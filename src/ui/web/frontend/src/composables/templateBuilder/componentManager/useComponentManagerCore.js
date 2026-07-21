/**
 * Component Manager Core
 *
 * S-Grade: Main component manager composable.
 * Single responsibility: Compose component manager functionality.
 */

import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createCrudActions } from './crudActions'

/**
 * Create component manager composable
 * @param {Object} options
 * @param {Ref} options.sections - Reactive sections array
 * @param {Ref} options.selectedSection - Currently selected section index
 * @param {Ref} options.selectedColumn - Currently selected column index
 * @param {Ref} options.selectedComponentLocation - Currently selected component location
 * @param {Ref} options.showPropertiesPanel - Properties panel visibility
 * @param {Ref} options.hasUnsavedChanges - Track unsaved changes
 * @param {Function} options.showConfirm - Confirmation dialog function
 * @param {Function} options.showToast - Toast notification function
 */
export function useComponentManager(options) {
  const { t } = useI18n()

  // Component counter
  const componentCounter = ref(1)

  // Create CRUD actions
  const crudActions = createCrudActions(options, componentCounter, t)

  return {
    ...crudActions
  }
}
