<template>
  <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 animate-fade-in">
    <!-- Template Selector (step 1) -->
    <div v-if="!selectedTemplate" class="space-y-4">
      <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <CircleDot :size="18" class="text-emerald-400" />
        {{ $t('templateCollaboration.templateIssues.chooseTemplate') }}
      </h3>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          v-for="tmpl in issueTemplates"
          :key="tmpl.type"
          @click="selectTemplate(tmpl)"
          class="p-4 bg-gray-900/50 border border-white/10 rounded-xl hover:border-purple-500/30 transition-all text-left group"
        >
          <div :class="tmpl.iconClass" class="w-10 h-10 rounded-lg flex items-center justify-center mb-3">
            <component :is="tmpl.icon" :size="20" class="text-white" />
          </div>
          <h4 class="text-sm font-medium text-white group-hover:text-purple-300 transition-colors">{{ tmpl.label }}</h4>
          <p class="text-xs text-gray-500 mt-1">{{ tmpl.description }}</p>
        </button>
      </div>
      <button
        @click="$emit('cancel')"
        class="px-4 py-2 text-gray-400 hover:text-white transition-colors text-sm"
      >
        {{ $t('common.cancel') }}
      </button>
    </div>

    <!-- Issue Form (step 2) -->
    <div v-else>
      <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <CircleDot :size="18" class="text-emerald-400" />
        {{ $t('templateCollaboration.templateIssues.create') }}
      </h3>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-400 mb-1">
            {{ $t('templateCollaboration.templateIssues.titleLabel') }}
          </label>
          <input
            v-model="title"
            type="text"
            required
            maxlength="200"
            class="w-full bg-gray-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-emerald-500/50 focus:outline-none transition-colors"
            :placeholder="$t('templateCollaboration.templateIssues.titlePlaceholder')"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-400 mb-1">
            {{ $t('templateCollaboration.templateIssues.typeLabel') }}
          </label>
          <div class="flex items-center gap-2">
            <button
              v-for="t in typeOptions"
              :key="t.value"
              type="button"
              @click="type = t.value"
              :class="[
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                type === t.value ? t.activeClass : 'text-gray-500 hover:text-gray-300 bg-gray-900/30'
              ]"
            >
              {{ t.label }}
            </button>
          </div>
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-400 mb-1">
            {{ $t('templateCollaboration.templateIssues.descriptionLabel') }}
          </label>
          <textarea
            v-model="description"
            rows="6"
            class="w-full bg-gray-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-emerald-500/50 focus:outline-none transition-colors resize-none"
            :placeholder="$t('templateCollaboration.templateIssues.descriptionPlaceholder')"
          ></textarea>
          <p class="text-xs text-gray-600 mt-1">Markdown supported</p>
        </div>

        <div class="flex items-center gap-3 pt-2">
          <button
            type="submit"
            :disabled="!title.trim() || submitting"
            class="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:shadow-lg hover:shadow-emerald-500/30 text-white font-medium rounded-xl transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ submitting ? $t('common.submitting') : $t('templateCollaboration.templateIssues.submitIssue') }}
          </button>
          <button
            type="button"
            @click="selectedTemplate = null"
            class="px-4 py-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            {{ $t('common.back') }}
          </button>
          <button
            type="button"
            @click="$emit('cancel')"
            class="px-4 py-2 text-gray-400 hover:text-white transition-colors text-sm"
          >
            {{ $t('common.cancel') }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { CircleDot, Bug, Lightbulb, HelpCircle } from 'lucide-vue-next'

const { t } = useI18n()

defineProps({
  submitting: { type: Boolean, default: false },
})

const emit = defineEmits(['submit', 'cancel'])

const selectedTemplate = ref(null)
const title = ref('')
const description = ref('')
const type = ref('bug')

const issueTemplates = computed(() => [
  {
    type: 'bug',
    label: t('templateCollaboration.templateIssues.templates.bugReport'),
    description: t('templateCollaboration.templateIssues.templates.bugReportDesc'),
    icon: Bug,
    iconClass: 'bg-gradient-to-br from-red-500 to-pink-500',
    prefill: '## Description\n\nA clear description of the bug.\n\n## Steps to Reproduce\n\n1. \n2. \n3. \n\n## Expected Behavior\n\n\n## Actual Behavior\n\n',
  },
  {
    type: 'feature',
    label: t('templateCollaboration.templateIssues.templates.featureRequest'),
    description: t('templateCollaboration.templateIssues.templates.featureRequestDesc'),
    icon: Lightbulb,
    iconClass: 'bg-gradient-to-br from-blue-500 to-cyan-500',
    prefill: '## Feature Description\n\nA clear description of the feature.\n\n## Use Case\n\nWhy is this feature needed?\n\n## Proposed Solution\n\n',
  },
  {
    type: 'question',
    label: t('templateCollaboration.templateIssues.templates.question'),
    description: t('templateCollaboration.templateIssues.templates.questionDesc'),
    icon: HelpCircle,
    iconClass: 'bg-gradient-to-br from-amber-500 to-orange-500',
    prefill: '## Question\n\n\n## Context\n\nWhat are you trying to achieve?\n',
  },
])

const typeOptions = computed(() => [
  { value: 'bug', label: t('templateCollaboration.templateIssues.typeBug'), activeClass: 'bg-red-500/20 text-red-400 border border-red-500/30' },
  { value: 'feature', label: t('templateCollaboration.templateIssues.typeFeature'), activeClass: 'bg-blue-500/20 text-blue-400 border border-blue-500/30' },
  { value: 'question', label: t('templateCollaboration.templateIssues.typeQuestion'), activeClass: 'bg-amber-500/20 text-amber-400 border border-amber-500/30' },
])

function selectTemplate(tmpl) {
  selectedTemplate.value = tmpl
  type.value = tmpl.type
  description.value = tmpl.prefill
}

function submit() {
  emit('submit', {
    title: title.value.trim(),
    description: description.value.trim(),
    type: type.value,
  })
}
</script>

<style scoped>
.animate-fade-in {
  animation: fade-in 0.3s ease-out;
}
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
