<template>
  <div class="prop-group">
    <label class="prop-label">
      <ShieldCheck :size="14" />
      {{ $t('templateBuilder.properties.validation') }}
    </label>
    <div class="prop-row">
      <div class="validation-summary">
        <span v-if="!enabled" class="validation-status off">
          {{ $t('templateBuilder.properties.validationOff') }}
        </span>
        <span v-else class="validation-status on">
          {{ summary }}
        </span>
      </div>
      <button
        class="settings-btn"
        :class="{ active: expanded }"
        :title="$t('templateBuilder.properties.moreOptions')"
        @click="$emit('toggle')"
      >
        <Settings :size="14" />
      </button>
    </div>
    <Transition name="expand">
      <div v-if="expanded" class="expanded-options">
        <OptionCheckbox
          :label="$t('templateBuilder.properties.enableValidation')"
          :model-value="enabled"
          @update:model-value="$emit('update:enabled', $event)"
        />

        <template v-if="enabled && validation">
          <OptionCheckbox
            :label="$t('templateBuilder.properties.required')"
            :model-value="validation.required"
            @update:model-value="$emit('update:field', 'required', $event)"
          />

          <template v-if="showLengthFields">
            <div class="option-row">
              <OptionInput
                :label="$t('templateBuilder.properties.minLength')"
                input-type="number"
                :model-value="validation.minLength"
                @update:model-value="$emit('update:field', 'minLength', $event ? Number($event) : null)"
                half
              />
              <OptionInput
                :label="$t('templateBuilder.properties.maxLength')"
                input-type="number"
                :model-value="validation.maxLength"
                @update:model-value="$emit('update:field', 'maxLength', $event ? Number($event) : null)"
                half
              />
            </div>
            <OptionInput
              :label="$t('templateBuilder.properties.pattern')"
              :model-value="validation.pattern"
              @update:model-value="$emit('update:field', 'pattern', $event)"
              monospace
              :placeholder="$t('templateBuilder.properties.patternPlaceholder')"
            />
          </template>

          <OptionInput
            :label="$t('templateBuilder.properties.errorMessage')"
            :model-value="validation.message"
            @update:model-value="$emit('update:field', 'message', $event)"
            :placeholder="$t('templateBuilder.properties.errorMessagePlaceholder')"
          />
        </template>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ShieldCheck, Settings } from 'lucide-vue-next'
import OptionCheckbox from '../OptionCheckbox.vue'
import OptionInput from '../OptionInput.vue'

const { t } = useI18n()

const props = defineProps({
  enabled: { type: Boolean, default: false },
  expanded: { type: Boolean, default: false },
  validation: { type: Object, default: null },
  showLengthFields: { type: Boolean, default: false }
})

defineEmits(['toggle', 'update:enabled', 'update:field'])

const summary = computed(() => {
  if (!props.validation) return t('templateBuilder.properties.noRules')
  const rules = []
  if (props.validation.required) rules.push(t('templateBuilder.properties.required'))
  if (props.validation.minLength) rules.push(`Min: ${props.validation.minLength}`)
  if (props.validation.maxLength) rules.push(`Max: ${props.validation.maxLength}`)
  if (props.validation.pattern) rules.push(t('templateBuilder.properties.patternSet'))
  return rules.length > 0 ? rules.join(', ') : t('templateBuilder.properties.noRules')
})
</script>

<style scoped>
.prop-group { margin-bottom: 20px; }

.prop-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 8px;
}

.prop-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.validation-summary {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #475569;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.6);
}

.validation-status { font-size: 12px; }
.validation-status.off { color: #64748b; }
.validation-status.on { color: #a78bfa; }

.settings-btn {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  border: 1px solid #475569;
  background: rgba(71, 85, 105, 0.2);
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.settings-btn:hover {
  background: rgba(139, 92, 246, 0.15);
  border-color: rgba(139, 92, 246, 0.3);
  color: #a78bfa;
}

.settings-btn.active {
  background: rgba(139, 92, 246, 0.2);
  border-color: #8B5CF6;
  color: #8B5CF6;
}

.expanded-options {
  margin-top: 12px;
  padding: 14px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid #334155;
  border-radius: 8px;
}

.option-row {
  display: flex;
  gap: 12px;
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease-out;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  max-height: 0;
  margin-top: 0;
  padding: 0 14px;
}

.expand-enter-to,
.expand-leave-from {
  opacity: 1;
  max-height: 500px;
}
</style>
