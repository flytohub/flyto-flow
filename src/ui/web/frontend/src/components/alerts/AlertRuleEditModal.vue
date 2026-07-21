<template>
  <BaseModal
    :is-open="isOpen"
    :title="isEditing ? $t('alerts.modal.editTitle', 'Edit Alert Rule') : $t('alerts.modal.createTitle', 'Create Alert Rule')"
    @close="$emit('close')"
  >
    <form @submit.prevent="handleSubmit" class="space-y-6">
      <!-- Name -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          {{ $t('alerts.modal.name', 'Rule Name') }} *
        </label>
        <AppInput
          v-model="form.name"
          required
          :placeholder="$t('alerts.modal.namePlaceholder', 'e.g., High failure rate alert')"
        />
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          {{ $t('alerts.modal.description', 'Description') }}
        </label>
        <AppTextarea
          v-model="form.description"
          :rows="2"
          :placeholder="$t('alerts.modal.descriptionPlaceholder', 'Optional description...')"
        />
      </div>

      <!-- Condition -->
      <div class="grid grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('alerts.modal.conditionType', 'Metric') }} *
          </label>
          <AppSelect
            v-model="form.condition.type"
            :options="[
              { value: 'failure_rate', label: $t('alerts.condition.failureRate', 'Failure Rate') },
              { value: 'execution_count', label: $t('alerts.condition.executionCount', 'Execution Count') },
              { value: 'duration', label: $t('alerts.condition.duration', 'Duration (ms)') },
              { value: 'consecutive_failures', label: $t('alerts.condition.consecutiveFailures', 'Consecutive Failures') }
            ]"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('alerts.modal.operator', 'Operator') }} *
          </label>
          <AppSelect
            v-model="form.condition.operator"
            :options="[
              { value: 'gt', label: $t('alerts.operator.gt', '> Greater than') },
              { value: 'gte', label: $t('alerts.operator.gte', '>= Greater or equal') },
              { value: 'lt', label: $t('alerts.operator.lt', '< Less than') },
              { value: 'lte', label: $t('alerts.operator.lte', '<= Less or equal') },
              { value: 'eq', label: $t('alerts.operator.eq', '= Equal to') }
            ]"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-300 mb-2">
            {{ $t('alerts.modal.threshold', 'Threshold') }} *
          </label>
          <input
            v-model.number="form.condition.threshold"
            type="number"
            required
            min="0"
            class="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
      </div>

      <!-- Severity -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          {{ $t('alerts.modal.severity', 'Severity') }} *
        </label>
        <div class="flex gap-3">
          <label
            v-for="sev in severityOptions"
            :key="sev.value"
            class="flex-1 relative"
          >
            <input
              v-model="form.severity"
              type="radio"
              :value="sev.value"
              class="peer sr-only"
            />
            <div
              class="p-3 rounded-lg border-2 cursor-pointer text-center transition-all peer-checked:border-purple-500"
              :class="sev.borderClass"
            >
              <component :is="sev.icon" :size="20" class="mx-auto mb-1" :class="sev.iconClass" />
              <span class="text-sm text-white">{{ sev.label }}</span>
            </div>
          </label>
        </div>
      </div>

      <!-- Cooldown -->
      <div>
        <label class="block text-sm font-medium text-gray-300 mb-2">
          {{ $t('alerts.modal.cooldown', 'Cooldown (minutes)') }}
        </label>
        <input
          v-model.number="form.cooldown_minutes"
          type="number"
          min="1"
          class="w-full px-4 py-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
        />
        <p class="mt-1 text-xs text-gray-400">
          {{ $t('alerts.modal.cooldownHelp', 'Minimum time between repeated alerts for the same rule') }}
        </p>
      </div>

      <!-- Enabled -->
      <div class="flex items-center gap-3">
        <button
          type="button"
          @click="form.enabled = !form.enabled"
          class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors"
          :class="form.enabled ? 'bg-purple-600' : 'bg-gray-600'"
        >
          <span
            class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform"
            :class="form.enabled ? 'translate-x-6' : 'translate-x-1'"
          />
        </button>
        <span class="text-sm text-gray-300">
          {{ $t('alerts.modal.enabled', 'Enable this rule') }}
        </span>
      </div>

      <!-- Actions -->
      <div class="flex justify-end gap-3 pt-4 border-t border-gray-700">
        <button
          type="button"
          @click="$emit('close')"
          class="px-4 py-2 text-gray-300 hover:text-white transition-colors"
        >
          {{ $t('common.cancel', 'Cancel') }}
        </button>
        <button
          type="submit"
          :disabled="loading"
          class="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors disabled:opacity-50"
        >
          {{ isEditing ? $t('common.save', 'Save') : $t('common.create', 'Create') }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { AlertTriangle, AlertCircle, Info } from 'lucide-vue-next'
import BaseModal from '@/components/common/BaseModal.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  rule: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'save'])

const { t } = useI18n()

const isEditing = computed(() => !!props.rule)

const defaultForm = {
  name: '',
  description: '',
  condition: {
    type: 'failure_rate',
    operator: 'gt',
    threshold: 10
  },
  severity: 'warning',
  cooldownMinutes: 15,
  enabled: true
}

const form = ref({ ...defaultForm })

const severityOptions = computed(() => [
  {
    value: 'critical',
    label: t('alerts.severity.critical', 'Critical'),
    icon: AlertTriangle,
    iconClass: 'text-red-400',
    borderClass: 'border-gray-700 hover:border-red-500/50'
  },
  {
    value: 'warning',
    label: t('alerts.severity.warning', 'Warning'),
    icon: AlertCircle,
    iconClass: 'text-yellow-400',
    borderClass: 'border-gray-700 hover:border-yellow-500/50'
  },
  {
    value: 'info',
    label: t('alerts.severity.info', 'Info'),
    icon: Info,
    iconClass: 'text-blue-400',
    borderClass: 'border-gray-700 hover:border-blue-500/50'
  }
])

watch(() => props.isOpen, (open) => {
  if (open) {
    if (props.rule) {
      form.value = {
        name: props.rule.name || '',
        description: props.rule.description || '',
        condition: { ...props.rule.condition },
        severity: props.rule.severity || 'warning',
        cooldownMinutes: props.rule.cooldownMinutes || 15,
        enabled: props.rule.enabled !== false
      }
    } else {
      form.value = { ...defaultForm }
    }
  }
})

function handleSubmit() {
  emit('save', {
    ...form.value,
    id: props.rule?.id
  })
}
</script>
