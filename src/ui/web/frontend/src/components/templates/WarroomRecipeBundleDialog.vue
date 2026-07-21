<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="show"
        class="warroom-backdrop"
        @click.self="$emit('close')"
      >
        <section class="warroom-dialog" aria-modal="true" role="dialog" aria-labelledby="warroom-import-title">
          <header class="warroom-header">
            <div>
              <h2 id="warroom-import-title">Import Warroom Recipes</h2>
              <p>Store reusable flyto-core smoke recipes under Warroom project folders.</p>
            </div>
            <button class="warroom-icon-btn" type="button" aria-label="Close" @click="$emit('close')">
              <X :size="18" />
            </button>
          </header>

          <form class="warroom-form" @submit.prevent="$emit('dry-run')">
            <label>
              <span>Project slug</span>
              <input
                :value="projectSlug"
                type="text"
                autocomplete="off"
                placeholder="acme-prod"
                @input="$emit('update:projectSlug', $event.target.value)"
              />
            </label>
            <label>
              <span>Flyto2 base URL</span>
              <input
                :value="baseUrl"
                type="url"
                autocomplete="off"
                placeholder="https://app.flyto2.com"
                @input="$emit('update:baseUrl', $event.target.value)"
              />
            </label>

            <div class="warroom-policy">
              <ShieldCheck :size="16" />
              <span>Credentials are runtime-only. Passwords, tokens, cookies, headers, bodies, and query strings are not stored in the bundle.</span>
            </div>

            <section class="warroom-section">
              <div class="warroom-section-title">
                <Inbox :size="15" />
                Signed inbox
                <button
                  class="warroom-small-btn"
                  type="button"
                  :disabled="scanning || dryRunning || importing"
                  @click="$emit('scan-inbox')"
                >
                  <RefreshCw v-if="!scanning" :size="14" />
                  <Loader2 v-else :size="14" class="animate-spin" />
                  <span>{{ scanning ? 'Scanning' : 'Scan' }}</span>
                </button>
              </div>
              <p v-if="inboxError" class="warroom-error">
                <AlertCircle :size="16" />
                <span>{{ inboxError }}</span>
              </p>
              <div v-if="pendingBundles.length" class="warroom-pending-list">
                <button
                  v-for="bundle in pendingBundles"
                  :key="bundle.sourcePath"
                  class="warroom-pending"
                  :class="{ selected: bundle.sourcePath === sourcePath }"
                  type="button"
                  @click="$emit('select-pending', bundle)"
                >
                  <span>{{ bundle.bundleId || 'pending-bundle' }}</span>
                  <small>{{ bundle.producer || 'unknown producer' }} - {{ bundle.assetCount ?? 0 }} assets</small>
                </button>
              </div>
              <div v-if="rejectedBundles.length" class="warroom-rejected">
                <span v-for="item in rejectedBundles" :key="item.sourcePath || item.error">
                  {{ item.error }}
                </span>
              </div>
            </section>

            <p v-if="error" class="warroom-error">
              <AlertCircle :size="16" />
              <span>{{ error }}</span>
            </p>

            <div v-if="dryRunResult?.ok" class="warroom-preview">
              <div class="warroom-metrics">
                <div>
                  <span class="warroom-metric-value">{{ dryRunResult.folderCount ?? 0 }}</span>
                  <span class="warroom-metric-label">Folders</span>
                </div>
                <div>
                  <span class="warroom-metric-value">{{ dryRunResult.templateCount ?? 0 }}</span>
                  <span class="warroom-metric-label">Recipe assets</span>
                </div>
                <div>
                  <span class="warroom-metric-value">{{ scenarioCount }}</span>
                  <span class="warroom-metric-label">Scenarios</span>
                </div>
              </div>

              <div class="warroom-section">
                <div class="warroom-section-title">
                  <FolderTree :size="15" />
                  Folder plan
                </div>
                <ul>
                  <li v-for="path in dryRunResult.folderPaths || []" :key="path.join('/')">
                    {{ path.join(' / ') }}
                  </li>
                </ul>
              </div>

              <div class="warroom-section">
                <div class="warroom-section-title">
                  <PlayCircle :size="15" />
                  Scenarios
                </div>
                <div class="warroom-scenarios">
                  <span v-for="scenario in dryRunResult.scenarioIds || []" :key="scenario">
                    {{ scenario }}
                  </span>
                </div>
              </div>
            </div>

            <div v-if="importResult?.ok" class="warroom-success">
              <CheckCircle2 :size="16" />
              <span>Imported {{ importResult.createdCount ?? 0 }} new and updated {{ importResult.updatedCount ?? 0 }} existing recipe assets.</span>
            </div>

            <footer class="warroom-actions">
              <button class="warroom-secondary" type="button" @click="$emit('close')">
                Close
              </button>
              <button class="warroom-primary" type="submit" :disabled="dryRunning || importing">
                <Loader2 v-if="dryRunning" :size="16" class="animate-spin" />
                <span>{{ dryRunning ? 'Checking' : 'Dry Run' }}</span>
              </button>
              <button
                v-if="dryRunResult?.ok"
                class="warroom-primary"
                type="button"
                :disabled="importing || dryRunning"
                @click="$emit('import')"
              >
                <Loader2 v-if="importing" :size="16" class="animate-spin" />
                <span>{{ importing ? 'Importing' : sourcePath ? 'Approve Bundle' : 'Import Recipes' }}</span>
              </button>
            </footer>
          </form>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import {
  AlertCircle,
  CheckCircle2,
  FolderTree,
  Inbox,
  Loader2,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  X,
} from 'lucide-vue-next'

const props = defineProps({
  show: { type: Boolean, default: false },
  projectSlug: { type: String, default: '' },
  baseUrl: { type: String, default: '' },
  sourcePath: { type: String, default: '' },
  pendingBundles: { type: Array, default: () => [] },
  rejectedBundles: { type: Array, default: () => [] },
  dryRunResult: { type: Object, default: null },
  importResult: { type: Object, default: null },
  error: { type: String, default: '' },
  inboxError: { type: String, default: '' },
  scanning: { type: Boolean, default: false },
  dryRunning: { type: Boolean, default: false },
  importing: { type: Boolean, default: false },
})

defineEmits([
  'close',
  'dry-run',
  'import',
  'scan-inbox',
  'select-pending',
  'update:projectSlug',
  'update:baseUrl',
])

const scenarioCount = computed(() => props.dryRunResult?.scenarioIds?.length ?? 0)
</script>

<style scoped>
.warroom-backdrop {
  position: fixed;
  inset: 0;
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(15, 23, 42, 0.68);
}

.warroom-dialog {
  width: min(760px, 100%);
  max-height: min(760px, calc(100vh - 48px));
  overflow: auto;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 8px;
  background: #0f172a;
  color: #e5e7eb;
  box-shadow: 0 24px 80px rgba(2, 6, 23, 0.5);
}

.warroom-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 22px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.18);
}

.warroom-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  letter-spacing: 0;
}

.warroom-header p {
  margin: 6px 0 0;
  color: #94a3b8;
  font-size: 14px;
}

.warroom-icon-btn {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.8);
  color: #cbd5e1;
}

.warroom-form {
  display: grid;
  gap: 16px;
  padding: 20px 22px 22px;
}

.warroom-form label {
  display: grid;
  gap: 7px;
}

.warroom-form label span {
  color: #cbd5e1;
  font-size: 13px;
  font-weight: 600;
}

.warroom-form input {
  min-height: 42px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 6px;
  background: rgba(15, 23, 42, 0.72);
  color: #f8fafc;
  padding: 0 12px;
  font-size: 14px;
  outline: none;
}

.warroom-form input:focus {
  border-color: #38bdf8;
}

.warroom-policy,
.warroom-error,
.warroom-success {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
}

.warroom-policy {
  background: rgba(14, 165, 233, 0.12);
  color: #bae6fd;
}

.warroom-error {
  background: rgba(220, 38, 38, 0.14);
  color: #fecaca;
}

.warroom-success {
  background: rgba(22, 163, 74, 0.14);
  color: #bbf7d0;
}

.warroom-preview {
  display: grid;
  gap: 14px;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  padding-top: 16px;
}

.warroom-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.warroom-metrics > div {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.5);
}

.warroom-metric-value {
  display: block;
  color: #f8fafc;
  font-size: 22px;
  font-weight: 700;
}

.warroom-metric-label {
  color: #94a3b8;
  font-size: 12px;
}

.warroom-section {
  display: grid;
  gap: 8px;
}

.warroom-section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #e2e8f0;
  font-size: 13px;
  font-weight: 700;
}

.warroom-small-btn {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 4px 10px;
  border: 1px solid rgba(148, 163, 184, 0.24);
  border-radius: 6px;
  color: #dbeafe;
  background: rgba(30, 41, 59, 0.82);
  font-size: 12px;
  font-weight: 700;
}

.warroom-small-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.warroom-section ul {
  display: grid;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.warroom-section li {
  overflow-wrap: anywhere;
  border-radius: 6px;
  background: rgba(30, 41, 59, 0.58);
  padding: 7px 9px;
  color: #cbd5e1;
  font-size: 13px;
}

.warroom-scenarios {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.warroom-scenarios span {
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 999px;
  padding: 5px 8px;
  color: #cbd5e1;
  font-size: 12px;
}

.warroom-pending-list {
  display: grid;
  gap: 8px;
}

.warroom-pending {
  display: grid;
  gap: 3px;
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.65);
  color: #e5e7eb;
  text-align: left;
}

.warroom-pending.selected {
  border-color: #60a5fa;
  background: rgba(37, 99, 235, 0.16);
}

.warroom-pending span {
  font-size: 13px;
  font-weight: 700;
}

.warroom-pending small {
  color: #94a3b8;
  font-size: 12px;
}

.warroom-rejected {
  display: grid;
  gap: 6px;
}

.warroom-rejected span {
  color: #fca5a5;
  font-size: 12px;
}

.warroom-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid rgba(148, 163, 184, 0.18);
  padding-top: 16px;
}

.warroom-primary,
.warroom-secondary {
  display: inline-flex;
  min-height: 38px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 6px;
  padding: 0 14px;
  font-size: 14px;
  font-weight: 600;
}

.warroom-primary {
  background: #0ea5e9;
  color: #082f49;
}

.warroom-primary:disabled,
.warroom-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.warroom-secondary {
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: rgba(15, 23, 42, 0.8);
  color: #cbd5e1;
}

@media (max-width: 640px) {
  .warroom-backdrop {
    align-items: stretch;
    padding: 10px;
  }

  .warroom-dialog {
    max-height: calc(100vh - 20px);
  }

  .warroom-header,
  .warroom-form {
    padding-left: 16px;
    padding-right: 16px;
  }

  .warroom-metrics {
    grid-template-columns: 1fr;
  }

  .warroom-actions {
    flex-direction: column;
  }

  .warroom-primary,
  .warroom-secondary {
    width: 100%;
  }
}
</style>
