<template>
  <div class="bg-gray-800/50 backdrop-blur-xl rounded-2xl border border-white/10 p-6 animate-fade-in">
    <h3 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
      <GitPullRequest :size="18" class="text-purple-400" />
      {{ $t('templateCollaboration.pullRequests.create') }}
    </h3>

    <form @submit.prevent="submit" class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-400 mb-1">
          {{ $t('templateCollaboration.pullRequests.titleLabel') }}
        </label>
        <input
          v-model="title"
          type="text"
          required
          maxlength="200"
          class="w-full bg-gray-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none transition-colors"
          :placeholder="$t('templateCollaboration.pullRequests.titlePlaceholder')"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-400 mb-1">
          {{ $t('templateCollaboration.pullRequests.descriptionLabel') }}
        </label>
        <textarea
          v-model="description"
          rows="4"
          class="w-full bg-gray-900/50 border border-white/10 rounded-xl px-4 py-2.5 text-white placeholder-gray-500 focus:border-purple-500/50 focus:outline-none transition-colors resize-none"
          :placeholder="$t('templateCollaboration.pullRequests.descriptionPlaceholder')"
        ></textarea>
        <p class="text-xs text-gray-600 mt-1">Markdown supported</p>
      </div>

      <!-- Draft checkbox -->
      <label class="flex items-center gap-2 cursor-pointer group">
        <input
          v-model="isDraft"
          type="checkbox"
          class="w-4 h-4 rounded border-white/20 bg-gray-900/50 text-purple-500 focus:ring-purple-500/50"
        />
        <span class="text-sm text-gray-400 group-hover:text-gray-300 transition-colors">
          {{ $t('templateCollaboration.pullRequests.createAsDraft') }}
        </span>
      </label>

      <!-- YAML diff upload -->
      <div>
        <label class="block text-sm font-medium text-gray-400 mb-1">
          YAML Diff (optional)
        </label>
        <div class="flex items-center gap-3">
          <button
            type="button"
            @click="$refs.yamlInput?.click()"
            aria-label="Upload YAML"
            class="px-3 py-2 bg-gray-900/50 border border-white/10 rounded-xl text-sm text-gray-400 hover:text-white hover:border-purple-500/30 transition-all flex items-center gap-2"
          >
            <FileUp :size="14" />
            {{ yamlFile ? yamlFile.name : 'Upload .yaml' }}
          </button>
          <button
            v-if="yamlFile"
            type="button"
            @click="clearYaml"
            aria-label="Clear YAML"
            class="text-gray-500 hover:text-red-400 transition-colors"
          >
            <X :size="14" />
          </button>
        </div>
        <input
          ref="yamlInput"
          type="file"
          accept=".yaml,.yml"
          class="hidden"
          @change="handleYamlFile"
        />
        <p v-if="yamlContent" class="text-xs text-emerald-500 mt-1">
          {{ yamlContent.split('\n').length }} lines loaded
        </p>
      </div>

      <!-- Issue linker -->
      <div v-if="openIssues.length">
        <label class="block text-sm font-medium text-gray-400 mb-1">
          {{ $t('templateCollaboration.pullRequests.linkedIssues') }}
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="issue in openIssues"
            :key="issue.id"
            type="button"
            @click="toggleIssueLink(issue.id)"
            :class="[
              'px-3 py-1.5 rounded-lg text-xs font-medium transition-all border',
              linkedIssueIds.includes(issue.id)
                ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                : 'text-gray-500 hover:text-gray-300 bg-gray-900/30 border-white/5'
            ]"
          >
            #{{ issue.id.slice(0, 8) }} {{ issue.title.slice(0, 30) }}{{ issue.title.length > 30 ? '...' : '' }}
          </button>
        </div>
      </div>

      <div class="flex items-center gap-3 pt-2">
        <button
          type="submit"
          :disabled="!title.trim() || submitting"
          class="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:shadow-lg hover:shadow-purple-500/30 text-white font-medium rounded-xl transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ submitting ? $t('common.submitting') : (isDraft ? $t('templateCollaboration.pullRequests.submitDraft') : $t('templateCollaboration.pullRequests.submitPR')) }}
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
</template>

<script setup>
import { ref } from 'vue'
import { GitPullRequest, FileUp, X } from 'lucide-vue-next'

const props = defineProps({
  forkId: { type: String, required: true },
  submitting: { type: Boolean, default: false },
  openIssues: { type: Array, default: () => [] },
})

const emit = defineEmits(['submit', 'cancel'])

const title = ref('')
const description = ref('')
const isDraft = ref(false)
const linkedIssueIds = ref([])
const yamlFile = ref(null)
const yamlContent = ref('')

function toggleIssueLink(issueId) {
  const idx = linkedIssueIds.value.indexOf(issueId)
  if (idx >= 0) {
    linkedIssueIds.value.splice(idx, 1)
  } else {
    linkedIssueIds.value.push(issueId)
  }
}

function handleYamlFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  yamlFile.value = file
  file.text().then(text => { yamlContent.value = text })
}

function clearYaml() {
  yamlFile.value = null
  yamlContent.value = ''
}

function submit() {
  emit('submit', {
    forkId: props.forkId,
    title: title.value.trim(),
    description: description.value.trim(),
    isDraft: isDraft.value,
    linkedIssueIds: linkedIssueIds.value,
    yamlContent: yamlContent.value || undefined,
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
