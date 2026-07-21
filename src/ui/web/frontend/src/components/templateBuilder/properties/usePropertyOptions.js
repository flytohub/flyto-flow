/**
 * Property Options Composable
 * Centralized configuration for property panel dropdowns
 */
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

export function usePropertyOptions() {
  const { t } = useI18n()

  const inputTypeOptions = computed(() => [
    { value: 'text', label: t('templateBuilder.properties.inputTypeText') },
    { value: 'email', label: t('templateBuilder.properties.inputTypeEmail') },
    { value: 'url', label: t('templateBuilder.properties.inputTypeUrl') },
    { value: 'number', label: t('templateBuilder.properties.inputTypeNumber') },
    { value: 'tel', label: t('templateBuilder.properties.inputTypeTel') },
    { value: 'password', label: t('templateBuilder.properties.inputTypePassword') }
  ])

  const layoutOptions = computed(() => [
    { value: 'vertical', label: t('templateBuilder.properties.layoutVertical') },
    { value: 'horizontal', label: t('templateBuilder.properties.layoutHorizontal') }
  ])

  const buttonTypeOptions = computed(() => [
    { value: 'button', label: t('templateBuilder.properties.buttonTypeButton') },
    { value: 'submit', label: t('templateBuilder.properties.buttonTypeSubmit') },
    { value: 'reset', label: t('templateBuilder.properties.buttonTypeReset') }
  ])

  const buttonStyleOptions = computed(() => [
    { value: 'primary', label: t('templateBuilder.properties.buttonStylePrimary') },
    { value: 'secondary', label: t('templateBuilder.properties.buttonStyleSecondary') },
    { value: 'danger', label: t('templateBuilder.properties.buttonStyleDanger') }
  ])

  return {
    inputTypeOptions,
    layoutOptions,
    buttonTypeOptions,
    buttonStyleOptions
  }
}
