<template>
  <div class="flex flex-col gap-2">
    <label v-if="label" :for="inputId" class="text-[0.85rem] font-medium text-white/70">{{ label }}</label>
    <div class="relative flex items-center">
      <component :is="icon" v-if="icon" :size="18" class="absolute left-4 text-white/40 pointer-events-none" aria-hidden="true" />
      <input
        :id="inputId"
        :type="computedType"
        :value="modelValue"
        :required="required"
        :minlength="minlength"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-label="!label ? ariaLabel || placeholder : undefined"
        :aria-invalid="error || undefined"
        :aria-describedby="errorId"
        :autofocus="autofocus"
        :autocomplete="autocomplete"
        class="w-full py-3.5 pr-4 pl-11 bg-white/5 border rounded-xl text-white text-[0.95rem] transition-all duration-300 placeholder:text-white/30 focus:outline-none focus:ring-3 focus-visible:outline-2 focus-visible:outline-primary-500 focus-visible:outline-offset-2"
        :class="error
          ? 'border-red-500 focus:ring-red-500/20'
          : 'border-white/10 focus:border-primary-500 focus:bg-primary-500/10 focus:ring-primary-500/20'"
        @input="$emit('update:modelValue', $event.target.value)"
        @blur="$emit('blur', $event)"
      />
      <button
        v-if="type === 'password'"
        type="button"
        class="absolute right-2 bg-none border-none text-white/40 cursor-pointer p-2.5 min-w-11 min-h-11 flex items-center justify-center transition-colors rounded-lg hover:text-white/70 hover:bg-white/5 focus-visible:outline-2 focus-visible:outline-primary-500 focus-visible:outline-offset-2"
        :aria-label="passwordVisible ? t('common.hidePassword') : t('common.showPassword')"
        :aria-pressed="passwordVisible"
        @click="toggleVisible"
      >
        <Eye v-if="!passwordVisible" :size="18" aria-hidden="true" />
        <EyeOff v-else :size="18" aria-hidden="true" />
      </button>
    </div>
    <p v-if="error && errorMessage" :id="errorId" class="text-red-500 text-[0.8rem] m-0" role="alert">
      {{ errorMessage }}
    </p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Eye, EyeOff } from 'lucide-vue-next'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  label: {
    type: String,
    default: ''
  },
  ariaLabel: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'text'
  },
  placeholder: {
    type: String,
    default: ''
  },
  icon: {
    type: [Object, Function],
    default: null
  },
  required: {
    type: Boolean,
    default: false
  },
  minlength: {
    type: [Number, String],
    default: undefined
  },
  disabled: {
    type: Boolean,
    default: false
  },
  error: {
    type: Boolean,
    default: false
  },
  errorMessage: {
    type: String,
    default: ''
  },
  autofocus: {
    type: Boolean,
    default: false
  },
  autocomplete: {
    type: String,
    default: undefined
  },
  id: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue', 'blur'])

const inputId = computed(() => props.id || `input-${Math.random().toString(36).substr(2, 9)}`)
const errorId = computed(() => props.error && props.errorMessage ? `${inputId.value}-error` : undefined)

const passwordVisible = ref(false)

const computedType = computed(() => {
  if (props.type === 'password') {
    return passwordVisible.value ? 'text' : 'password'
  }
  return props.type
})

function toggleVisible() {
  passwordVisible.value = !passwordVisible.value
}
</script>
