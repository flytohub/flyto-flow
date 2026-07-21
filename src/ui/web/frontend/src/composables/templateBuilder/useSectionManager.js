/**
 * Section Manager Composable
 * Handles UI section CRUD operations for the template builder
 */

import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * Create section manager composable
 * @param {Object} options
 * @param {Ref} options.sections - Reactive sections array
 * @param {Ref} options.selectedSection - Currently selected section index
 * @param {Ref} options.selectedColumn - Currently selected column index
 * @param {Ref} options.selectedComponentLocation - Currently selected component location
 * @param {Ref} options.hasUnsavedChanges - Track unsaved changes
 * @param {Ref} options.showLayoutPicker - Layout picker visibility
 * @param {Ref} options.showGridEditDialog - Grid edit dialog visibility
 * @param {Function} options.showConfirm - Confirmation dialog function
 * @param {Function} options.showToast - Toast notification function
 */
export function useSectionManager(options) {
  const {
    sections,
    selectedSection,
    selectedColumn,
    selectedComponentLocation,
    hasUnsavedChanges,
    showLayoutPicker,
    showGridEditDialog,
    showConfirm,
    showToast
  } = options

  const { t } = useI18n()

  // Local state
  const editingSectionIndex = ref(null)
  const tempGridValues = ref([])
  let sectionCounter = 1

  /**
   * Open column ratio dialog and add new section
   * @param {number} cols - Number of columns
   */
  function openColumnRatioDialog(cols) {
    showLayoutPicker.value = false

    const equalRatio = Math.floor(12 / cols)
    const remainder = 12 % cols
    const grid = Array(cols).fill(equalRatio)
    for (let i = 0; i < remainder; i++) {
      grid[i]++
    }

    const newSection = {
      id: `section_${sectionCounter++}`,
      columns: cols,
      grid: grid,
      gap: '16px',
      columnsData: []
    }

    for (let i = 0; i < cols; i++) {
      newSection.columnsData.push({
        columnIndex: i,
        components: []
      })
    }

    sections.value.push(newSection)
    hasUnsavedChanges.value = true
  }

  /**
   * Open grid edit dialog for a section
   * @param {number} sectionIndex - Section index
   */
  function openEditGridDialog(sectionIndex) {
    editingSectionIndex.value = sectionIndex
    const section = sections.value[sectionIndex]
    tempGridValues.value = [...section.grid]
    showGridEditDialog.value = true
  }

  /**
   * Save grid ratio values
   * @param {Array} gridValues - Grid column values
   */
  function saveGridRatio(gridValues) {
    if (!Array.isArray(gridValues)) return
    const sum = gridValues.reduce((a, b) => a + (parseInt(b) || 0), 0)
    if (sum !== 12) {
      showToast(t('templateBuilder.alerts.gridSumMustBe12'), 'error')
      return
    }

    const section = sections.value[editingSectionIndex.value]
    section.grid = gridValues.map(v => parseInt(v))
    hasUnsavedChanges.value = true
    showGridEditDialog.value = false
    editingSectionIndex.value = null
  }

  /**
   * Select a column
   * @param {number} sectionIndex - Section index
   * @param {number} columnIndex - Column index
   */
  function selectColumn(sectionIndex, columnIndex) {
    selectedSection.value = sectionIndex
    selectedColumn.value = columnIndex
    selectedComponentLocation.value = null
  }

  /**
   * Move section up
   * @param {number} index - Section index
   */
  function moveSectionUp(index) {
    if (index > 0) {
      const secs = sections.value
      ;[secs[index - 1], secs[index]] = [secs[index], secs[index - 1]]
      if (selectedSection.value === index) {
        selectedSection.value = index - 1
      }
      hasUnsavedChanges.value = true
    }
  }

  /**
   * Move section down
   * @param {number} index - Section index
   */
  function moveSectionDown(index) {
    const secs = sections.value
    if (index < secs.length - 1) {
      ;[secs[index], secs[index + 1]] = [secs[index + 1], secs[index]]
      if (selectedSection.value === index) {
        selectedSection.value = index + 1
      }
      hasUnsavedChanges.value = true
    }
  }

  /**
   * Delete a section
   * @param {number} index - Section index
   */
  async function deleteSection(index) {
    const confirmed = await showConfirm({
      type: 'danger',
      title: t('templateBuilder.dialog.deleteSection'),
      message: t('templateBuilder.dialog.confirmDelete'),
      confirmText: t('common.delete')
    })

    if (confirmed) {
      sections.value.splice(index, 1)
      if (selectedSection.value === index) {
        selectedSection.value = null
        selectedColumn.value = null
        selectedComponentLocation.value = null
      }
      hasUnsavedChanges.value = true
      showToast(t('templateBuilder.toast.sectionDeleted'), 'success')
    }
  }

  return {
    // State
    editingSectionIndex,
    tempGridValues,
    // Methods
    openColumnRatioDialog,
    openEditGridDialog,
    saveGridRatio,
    selectColumn,
    moveSectionUp,
    moveSectionDown,
    deleteSection
  }
}
