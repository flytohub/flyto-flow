<template>
    <div class="flow-control-params">
        <template v-if="isBranch">
            <div class="param-field">
                <label class="param-label">
                    <GitBranch :size="14" />
                    {{ t('flow.branch.condition') }}
                </label>
                <AppTextarea
                    v-model="localParams.condition"
                    :placeholder="t('flow.branch.conditionPlaceholder')"
                    :readonly="readOnly"
                    @update:modelValue="emitUpdateDebounced"
                    :rows="2"
                    size="sm"
                />
                <div class="param-hint">
                    {{ t('flow.branch.conditionHint') }}
                </div>
            </div>

            <div class="output-info">
                <div class="output-item output-true">
                    <div class="output-dot"></div>
                    <span>{{ t('flow.branch.true') }}</span>
                    <span class="output-desc">→ {{ t('flow.branch.trueDesc') }}</span>
                </div>
                <div class="output-item output-false">
                    <div class="output-dot"></div>
                    <span>{{ t('flow.branch.false') }}</span>
                    <span class="output-desc">→ {{ t('flow.branch.falseDesc') }}</span>
                </div>
            </div>
        </template>

        <template v-else-if="isSwitch">
            <div class="param-field">
                <label class="param-label">
                    <GitMerge :size="14" />
                    {{ t('flow.switch.expression') }}
                </label>
                <AppInput
                    v-model="localParams.expression"
                    :placeholder="t('flow.switch.expressionPlaceholder')"
                    :readonly="readOnly"
                    @update:modelValue="emitUpdateDebounced"
                    size="sm"
                />
                <div class="param-hint">
                    {{ t('flow.switch.expressionHint') }}
                </div>
            </div>

            <SwitchCasesEditor
                v-model="localParams.cases"
                :read-only="readOnly"
                @update:modelValue="emitUpdateDebounced"
            />
        </template>

        <template v-else-if="isLoop">
            <div class="param-field">
                <label class="param-label">
                    <RefreshCw :size="14" />
                    {{ t('flow.loop.times') }}
                </label>
                <div class="number-input-wrapper">
                    <input
                        type="number"
                        v-model.number="localParams.times"
                        class="times-input"
                        :placeholder="t('flow.loop.timesPlaceholder')"
                        :readonly="readOnly"
                        :min="1"
                        :max="1000"
                        @input="emitUpdateDebounced"
                    />
                    <div class="spin-buttons" v-if="!readOnly">
                        <button type="button" class="spin-btn" @click="incrementTimes" tabindex="-1" aria-label="Increase value">
                            <ChevronUp :size="14" />
                        </button>
                        <button type="button" class="spin-btn" @click="decrementTimes" tabindex="-1" aria-label="Decrease value">
                            <ChevronDown :size="14" />
                        </button>
                    </div>
                </div>
                <div class="param-hint">
                    {{ t('flow.loop.timesHint') }}
                </div>
            </div>

            <div class="loop-info" v-if="loopTarget">
                <div class="info-item">
                    <CornerUpLeft :size="14" />
                    <span>{{ t('flow.loop.target') }}</span>
                    <code class="target-id">{{ loopTarget }}</code>
                </div>
                <div class="param-hint">
                    {{ t('flow.loop.targetHint') }}
                </div>
            </div>

            <div class="loop-info no-target" v-else>
                <div class="info-item">
                    <CornerUpLeft :size="14" />
                    <span>{{ t('flow.loop.noTarget') }}</span>
                </div>
                <div class="param-hint">
                    {{ t('flow.loop.targetHint') }}</div>
            </div>
        </template>
    </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { GitBranch, GitMerge, RefreshCw, CornerUpLeft, ChevronUp, ChevronDown } from 'lucide-vue-next'
import { useI18n } from 'vue-i18n'
import SwitchCasesEditor from './SwitchCasesEditor.vue'
import AppInput from '@/components/common/AppInput.vue'
import AppTextarea from '@/components/common/AppTextarea.vue'

const { t } = useI18n()

const props = defineProps({
    moduleId: { type: String, required: true },
    params: { type: Object, default: () => ({}) },
    connections: { type: Object, default: () => null },
    readOnly: { type: Boolean, default: false },
    debounceMs: { type: Number, default: 120 }
})

const emit = defineEmits(['update:params'])

const isBranch = computed(() => props.moduleId?.includes('flow.branch'))
const isSwitch = computed(() => props.moduleId?.includes('flow.switch'))
const isLoop = computed(() => props.moduleId?.includes('flow.loop') || props.moduleId?.includes('flow.repeat'))

const loopTarget = computed(() => {
    if (props.connections?.iterate?.length > 0) return props.connections.iterate[0]
    return props.params?.target || ''
})

function isPlainObject(v) {
    return v !== null && typeof v === 'object' && !Array.isArray(v)
}

function shallowEqual(a, b) {
    if (a === b) return true
    if (!isPlainObject(a) || !isPlainObject(b)) return false
    const ak = Object.keys(a)
    const bk = Object.keys(b)
    if (ak.length !== bk.length) return false
    for (const k of ak) if (a[k] !== b[k]) return false
    return true
}

function normalizeParams() {
    if (isBranch.value) {
        return { condition: props.params?.condition || '' }
    }
    if (isSwitch.value) {
        const cases = Array.isArray(props.params?.cases) ? props.params.cases : null
        return {
            expression: props.params?.expression || '',
            cases: cases && cases.length > 0 ? cases : makeDefaultCases()
        }
    }
    if (isLoop.value) {
        const times = Number(props.params?.times ?? 1)
        return { times: Number.isFinite(times) ? Math.max(1, Math.min(1000, times)) : 1 }
    }
    return {}
}

function makeDefaultCases() {
    const base = `case_${Math.random().toString(36).slice(2, 9)}`
    return [
        { id: `${base}_1`, value: 'case1', label: t('switchCase.case1') },
        { id: `${base}_2`, value: 'case2', label: t('switchCase.case2') }
    ]
}

const localParams = ref(normalizeParams())
let lastExternal = localParams.value

function syncFromExternal() {
    const next = normalizeParams()
    if (shallowEqual(next, lastExternal)) return
    lastExternal = next
    localParams.value = next
}

watch(() => props.moduleId, () => syncFromExternal())
watch(() => props.params, () => syncFromExternal(), { deep: true })

let timer = null
function emitUpdateDebounced() {
    if (props.readOnly) return
    if (timer) return
    timer = window.setTimeout(() => {
        timer = null
        emit('update:params', { ...localParams.value })
    }, props.debounceMs)
}

onBeforeUnmount(() => {
    if (timer) window.clearTimeout(timer)
})

function incrementTimes() {
    if (props.readOnly) return
    const current = Number(localParams.value.times) || 1
    localParams.value.times = Math.min(1000, current + 1)
    emitUpdateDebounced()
}

function decrementTimes() {
    if (props.readOnly) return
    const current = Number(localParams.value.times) || 1
    localParams.value.times = Math.max(1, current - 1)
    emitUpdateDebounced()
}
</script>

<style scoped>
.flow-control-params {
    display: flex;
    flex-direction: column;
    gap: 16px;
    padding: 14px;
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid #334155;
    border-radius: 8px;
}

.param-field {
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.param-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 600;
    color: #94a3b8;
}

.condition-input,
.expression-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #475569;
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.6);
    color: #f1f5f9;
    font-size: 13px;
    font-family: 'SF Mono', Monaco, monospace;
    transition: all 0.2s;
    resize: vertical;
}

.condition-input:focus,
.expression-input:focus {
    outline: none;
    border-color: #8B5CF6;
    box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.condition-input[readonly],
.expression-input[readonly] {
    opacity: 0.7;
    cursor: default;
}

.param-hint {
    font-size: 11px;
    color: #64748b;
}

.output-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background: rgba(15, 23, 42, 0.4);
    border-radius: 8px;
}

.output-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #e2e8f0;
}

.output-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
}

.output-true .output-dot {
    background: #10B981;
}

.output-false .output-dot {
    background: #EF4444;
}

.output-desc {
    color: #64748b;
    font-size: 11px;
}

.times-input {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #475569;
    border-radius: 8px;
    background: rgba(15, 23, 42, 0.6);
    color: #f1f5f9;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.2s;
    /* Hide native spinner */
    -moz-appearance: textfield;
    appearance: textfield;
}

.times-input::-webkit-outer-spin-button,
.times-input::-webkit-inner-spin-button {
    -webkit-appearance: none;
    margin: 0;
}

.times-input:focus {
    outline: none;
    border-color: #F59E0B;
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.15);
}

.times-input[readonly] {
    opacity: 0.7;
    cursor: default;
}

.number-input-wrapper {
    position: relative;
    display: flex;
    align-items: stretch;
}

.number-input-wrapper .times-input {
    padding-right: 36px;
}

.spin-buttons {
    position: absolute;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 2px;
}

.spin-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 16px;
    padding: 0;
    background: rgba(71, 85, 105, 0.4);
    border: none;
    border-radius: 4px;
    color: rgba(148, 163, 184, 0.8);
    cursor: pointer;
    transition: all 0.15s ease;
}

.spin-btn:hover {
    background: rgba(245, 158, 11, 0.4);
    color: #f1f5f9;
}

.spin-btn:active {
    background: rgba(245, 158, 11, 0.6);
}

.loop-info {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 8px;
}

.loop-info.no-target {
    background: rgba(100, 116, 139, 0.1);
    border-color: rgba(100, 116, 139, 0.3);
}

.loop-info.no-target .info-item {
    color: #64748b;
}

.info-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 12px;
    color: #F59E0B;
}

.target-id {
    background: rgba(245, 158, 11, 0.2);
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'SF Mono', Monaco, monospace;
    font-size: 11px;
}
</style>
