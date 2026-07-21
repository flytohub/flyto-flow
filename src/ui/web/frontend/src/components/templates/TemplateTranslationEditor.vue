<template>
  <div class="group relative bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 hover:border-blue-500/30 transition-all duration-500">
    <div class="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
    <div class="relative">
      <!-- Header -->
      <div class="flex items-center justify-between mb-6">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center">
            <Languages :size="20" class="text-white" />
          </div>
          <div>
            <h2 class="text-lg font-semibold text-white">{{ $t('publish.translations.title') }}</h2>
            <p class="text-sm text-gray-400">{{ $t('publish.translations.subtitle') }}</p>
          </div>
        </div>
        <button
          @click="showAddLanguage = true"
          aria-label="Add language"
          class="flex items-center gap-2 px-3 py-2 bg-blue-500/20 hover:bg-blue-500/30 text-blue-400 rounded-lg transition-colors text-sm"
        >
          <Plus :size="16" />
          {{ $t('publish.translations.addLanguage') }}
        </button>
      </div>

      <!-- Default Language -->
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-300 mb-2">
          {{ $t('publish.translations.defaultLanguage') }}
        </label>
        <AppSelect
          :modelValue="defaultLanguage"
          @update:modelValue="$emit('update:defaultLanguage', $event)"
          :options="availableLanguages.map(lang => ({ value: lang.code, label: lang.name + ' (' + lang.code + ')' }))"
        />
      </div>

      <!-- Translations List -->
      <div class="space-y-4">
        <div
          v-for="(translation, langCode) in translations"
          :key="langCode"
          class="p-4 bg-gray-900/50 border border-white/10 rounded-xl"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs font-medium">
                {{ langCode }}
              </span>
              <span class="text-gray-400 text-sm">{{ getLanguageName(langCode) }}</span>
            </div>
            <button
              @click="removeTranslation(langCode)"
              aria-label="Remove translation"
              class="p-1.5 text-gray-500 hover:text-red-400 transition-colors"
              :title="$t('common.remove')"
            >
              <X :size="16" />
            </button>
          </div>

          <!-- Name Translation -->
          <div class="mb-3">
            <label class="block text-xs text-gray-500 mb-1">{{ $t('publish.translations.name') }}</label>
            <AppInput
              :modelValue="translation.name"
              @update:modelValue="updateTranslation(langCode, 'name', $event)"
              :placeholder="name || $t('publish.translations.namePlaceholder')"
            />
          </div>

          <!-- Description Translation -->
          <div>
            <label class="block text-xs text-gray-500 mb-1">{{ $t('publish.translations.description') }}</label>
            <AppTextarea
              :modelValue="translation.description"
              @update:modelValue="updateTranslation(langCode, 'description', $event)"
              :rows="3"
              :placeholder="description || $t('publish.translations.descriptionPlaceholder')"
            />
          </div>
        </div>

        <!-- Empty State -->
        <div v-if="Object.keys(translations).length === 0" class="text-center py-8 text-gray-500">
          <Globe :size="32" class="mx-auto mb-2 opacity-50" />
          <p>{{ $t('publish.translations.noTranslations') }}</p>
          <p class="text-sm mt-1">{{ $t('publish.translations.addLanguageHint') }}</p>
        </div>
      </div>

      <!-- Add Language Modal -->
      <Teleport to="body">
        <div
          v-if="showAddLanguage"
          class="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div class="absolute inset-0 bg-black/50" @click="showAddLanguage = false"></div>
          <div class="relative bg-gray-800 rounded-2xl w-full max-w-md p-6 shadow-xl border border-white/10">
            <h3 class="text-lg font-semibold text-white mb-4">{{ $t('publish.translations.selectLanguage') }}</h3>

            <div class="space-y-2 max-h-64 overflow-y-auto">
              <button
                v-for="lang in unaddedLanguages"
                :key="lang.code"
                @click="addLanguage(lang.code)"
                class="w-full flex items-center justify-between px-4 py-3 bg-gray-700/50 hover:bg-gray-700 rounded-xl transition-colors text-left"
              >
                <span class="text-white">{{ lang.name }}</span>
                <span class="text-gray-400 text-sm">{{ lang.code }}</span>
              </button>
            </div>

            <button
              @click="showAddLanguage = false"
              aria-label="Cancel"
              class="mt-4 w-full px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-xl transition-colors"
            >
              {{ $t('common.cancel') }}
            </button>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Languages, Plus, X, Globe } from 'lucide-vue-next'
import AppInput from '@/components/common/AppInput.vue'
import AppSelect from '@/components/common/AppSelect.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const { t } = useI18n()

const props = defineProps({
  translations: {
    type: Object,
    default: () => ({})
  },
  defaultLanguage: {
    type: String,
    default: 'en'
  },
  name: {
    type: String,
    default: ''
  },
  description: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:translations', 'update:defaultLanguage'])

const showAddLanguage = ref(false)

const availableLanguages = [
  { code: 'en', name: 'English' },
  { code: 'zh-TW', name: 'Traditional Chinese' },
  { code: 'zh-CN', name: 'Simplified Chinese' },
  { code: 'ja', name: 'Japanese' },
  { code: 'ko', name: 'Korean' },
  { code: 'es', name: 'Spanish' },
  { code: 'fr', name: 'French' },
  { code: 'de', name: 'German' },
  { code: 'pt', name: 'Portuguese' },
  { code: 'it', name: 'Italian' },
  { code: 'ru', name: 'Russian' },
  { code: 'ar', name: 'Arabic' },
  { code: 'hi', name: 'Hindi' },
  { code: 'th', name: 'Thai' },
  { code: 'vi', name: 'Vietnamese' },
]

const unaddedLanguages = computed(() => {
  return availableLanguages.filter(lang => !(lang.code in props.translations))
})

function getLanguageName(code) {
  const lang = availableLanguages.find(l => l.code === code)
  return lang?.name || code
}

function addLanguage(langCode) {
  const updated = {
    ...props.translations,
    [langCode]: { name: '', description: '' }
  }
  emit('update:translations', updated)
  showAddLanguage.value = false
}

function removeTranslation(langCode) {
  const updated = { ...props.translations }
  delete updated[langCode]
  emit('update:translations', updated)
}

function updateTranslation(langCode, field, value) {
  const updated = {
    ...props.translations,
    [langCode]: {
      ...props.translations[langCode],
      [field]: value
    }
  }
  emit('update:translations', updated)
}
</script>
