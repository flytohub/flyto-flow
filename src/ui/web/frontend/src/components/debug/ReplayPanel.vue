<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-x-full"
      enter-to-class="opacity-100 translate-x-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-x-0"
      leave-to-class="opacity-0 translate-x-full"
    >
      <div
        v-if="isOpen"
        class="fixed top-0 right-0 h-full w-[720px] bg-[#0a0a0f] border-l border-gray-700 shadow-2xl z-40 flex flex-col"
      >
        <!-- Background Pattern -->
        <div class="absolute inset-0 opacity-[0.02] pointer-events-none" style="background-image: linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px); background-size: 20px 20px;" />

        <!-- Header -->
        <div class="relative flex items-center justify-between px-5 py-4 border-b border-gray-700/50 bg-gradient-to-r from-emerald-950/30 to-transparent">
          <div class="flex items-center gap-4">
            <div class="relative">
              <div class="p-2.5 bg-emerald-600/20 rounded-xl border border-emerald-500/30">
                <RotateCcw :size="22" class="text-emerald-400" />
              </div>
              <div class="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
            </div>
            <div>
              <h3 class="text-lg font-semibold text-white tracking-wide">{{ $t('debug.replay.title') }}</h3>
              <p class="text-xs text-gray-400 mt-0.5">{{ $t('debug.replay.subtitle') }}</p>
            </div>
          </div>
          <button
            @click="$emit('close')"
            class="p-2 text-gray-400 hover:text-white hover:bg-gray-700/50 rounded-lg transition-all"
            aria-label="Close"
          >
            <X :size="20" />
          </button>
        </div>

        <!-- No Execution ID State -->
        <div v-if="!executionId" class="flex-1 flex flex-col items-center justify-center text-gray-400 relative">
          <div class="w-24 h-24 mb-4 rounded-2xl bg-gradient-to-br from-gray-800 to-gray-900 flex items-center justify-center border border-gray-700/50 shadow-2xl">
            <Play :size="40" class="text-gray-600" />
          </div>
          <p class="text-sm font-medium">{{ $t('debug.replay.runWorkflowFirst', 'Run workflow first') }}</p>
          <p class="text-xs mt-2 text-gray-600">{{ $t('debug.replay.runFirstHint', 'Execute the workflow to enable replay') }}</p>
        </div>

        <!-- Main Content -->
        <div v-else class="flex-1 flex flex-col overflow-hidden relative">
          <!-- Tab Navigation -->
          <div class="flex items-center gap-1 px-4 py-2 border-b border-gray-700/30 bg-gray-900/50">
            <button
              v-for="tab in tabs"
              :key="tab.id"
              @click="activeTab = tab.id"
              :class="[
                'px-4 py-2 rounded-lg text-sm font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              ]"
            >
              <component :is="tab.icon" :size="14" class="inline mr-1.5 -mt-0.5" />
              {{ tab.label }}
            </button>
          </div>

          <!-- Replay Setup Tab -->
          <div v-if="activeTab === 'setup'" class="flex-1 overflow-auto p-4 space-y-4">
            <!-- Mode Selection -->
            <div class="bg-gray-900/50 rounded-xl border border-gray-700/30 p-4">
              <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">{{ $t('debug.replay.replayModeLabel') }}</h4>
              <div class="grid grid-cols-2 gap-3">
                <button
                  @click="replayMode = 'full'"
                  :class="[
                    'p-4 rounded-xl border transition-all text-left',
                    replayMode === 'full'
                      ? 'bg-emerald-950/50 border-emerald-500/50 shadow-lg shadow-emerald-500/10'
                      : 'bg-gray-800/50 border-gray-700/50 hover:border-gray-600'
                  ]"
                >
                  <div class="flex items-center gap-2 mb-2">
                    <RotateCcw :size="18" :class="replayMode === 'full' ? 'text-emerald-400' : 'text-gray-500'" />
                    <span :class="replayMode === 'full' ? 'text-emerald-300' : 'text-gray-300'" class="font-semibold">{{ $t('debug.replay.fullReplayOption') }}</span>
                  </div>
                  <p class="text-xs text-gray-500">{{ $t('debug.replay.fullReplayDesc') }}</p>
                </button>

                <button
                  @click="replayMode = 'step'"
                  :class="[
                    'p-4 rounded-xl border transition-all text-left',
                    replayMode === 'step'
                      ? 'bg-emerald-950/50 border-emerald-500/50 shadow-lg shadow-emerald-500/10'
                      : 'bg-gray-800/50 border-gray-700/50 hover:border-gray-600'
                  ]"
                >
                  <div class="flex items-center gap-2 mb-2">
                    <FastForward :size="18" :class="replayMode === 'step' ? 'text-emerald-400' : 'text-gray-500'" />
                    <span :class="replayMode === 'step' ? 'text-emerald-300' : 'text-gray-300'" class="font-semibold">{{ $t('debug.replay.fromStep') }}</span>
                  </div>
                  <p class="text-xs text-gray-500">{{ $t('debug.replay.fromStepDesc') }}</p>
                </button>
              </div>
            </div>

            <!-- Step Selection (when mode is 'step') -->
            <Transition
              enter-active-class="transition ease-out duration-200"
              enter-from-class="opacity-0 -translate-y-2"
              enter-to-class="opacity-100 translate-y-0"
            >
              <div v-if="replayMode === 'step'" class="bg-gray-900/50 rounded-xl border border-gray-700/30 p-4">
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">{{ $t('debug.replay.selectStartingStep') }}</h4>

                <div v-if="executionSteps.length" class="space-y-2 max-h-64 overflow-auto">
                  <button
                    v-for="step in executionSteps"
                    :key="step.stepId"
                    @click="selectedStepId = step.stepId"
                    :class="[
                      'w-full p-3 rounded-lg border transition-all text-left flex items-center gap-3',
                      selectedStepId === step.stepId
                        ? 'bg-emerald-950/50 border-emerald-500/50'
                        : 'bg-gray-800/30 border-gray-700/30 hover:border-gray-600'
                    ]"
                  >
                    <!-- Step Number -->
                    <div
                      :class="[
                        'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold',
                        step.status === 'failed'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      ]"
                    >
                      {{ step.stepIndex + 1 }}
                    </div>

                    <!-- Step Info -->
                    <div class="flex-1 min-w-0">
                      <div class="flex items-center gap-2">
                        <span class="font-medium text-white truncate">{{ step.stepId }}</span>
                        <span v-if="step.loopCount > 1" class="px-1.5 py-0.5 text-[10px] font-bold bg-violet-500/20 text-violet-300 rounded border border-violet-500/30">
                          x{{ step.loopCount }}
                        </span>
                      </div>
                      <p class="text-xs text-gray-500 font-mono truncate">{{ step.moduleId }}</p>
                    </div>

                    <!-- Duration -->
                    <div class="text-xs text-gray-500 tabular-nums">
                      {{ step.durationMs }}ms
                    </div>
                  </button>
                </div>

                <div v-else-if="isLoadingSteps" class="flex items-center justify-center py-8">
                  <Loader :size="24" class="text-emerald-400 animate-spin" />
                </div>

                <div v-else class="text-center py-8 text-gray-500">
                  <p class="text-sm">{{ $t('debug.replay.noStepsFound') }}</p>
                </div>
              </div>
            </Transition>

            <!-- Context Overrides -->
            <div class="bg-gray-900/50 rounded-xl border border-gray-700/30 p-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-xs font-bold text-gray-400 uppercase tracking-widest">{{ $t('debug.replay.contextOverrides') }}</h4>
                <button
                  @click="showContextEditor = !showContextEditor"
                  class="text-xs text-emerald-400 hover:text-emerald-300 flex items-center gap-1"
                >
                  <Edit3 :size="12" />
                  {{ showContextEditor ? $t('debug.replay.hideContext') : $t('debug.replay.editContext') }}
                </button>
              </div>

              <p class="text-xs text-gray-500 mb-3">{{ $t('debug.replay.modifyVariables') }}</p>

              <Transition
                enter-active-class="transition ease-out duration-200"
                enter-from-class="opacity-0 max-h-0"
                enter-to-class="opacity-100 max-h-48"
              >
                <div v-if="showContextEditor">
                  <AppTextarea
                    v-model="contextOverridesJson"
                    :rows="6"
                    placeholder='{ "variable_name": "new_value" }'
                    size="sm"
                  />
                  <p v-if="jsonError" class="text-xs text-red-400 mt-2 flex items-center gap-1">
                    <AlertCircle :size="12" />
                    {{ jsonError }}
                  </p>
                </div>
              </Transition>

              <!-- Quick Context Keys -->
              <div v-if="contextKeys.length && !showContextEditor" class="flex flex-wrap gap-2 mt-2">
                <span
                  v-for="key in contextKeys.slice(0, 6)"
                  :key="key"
                  class="px-2 py-1 text-xs bg-gray-800/50 text-gray-400 rounded-lg border border-gray-700/30"
                >
                  {{ key }}
                </span>
                <span v-if="contextKeys.length > 6" class="px-2 py-1 text-xs text-gray-500">
                  {{ $t('debug.replay.more', { count: contextKeys.length - 6 }) }}
                </span>
              </div>
            </div>

            <!-- Validation Status -->
            <div v-if="validationResult" class="bg-gray-900/50 rounded-xl border border-gray-700/30 p-4">
              <div class="flex items-center gap-3">
                <div
                  :class="[
                    'w-10 h-10 rounded-xl flex items-center justify-center',
                    validationResult.canReplay
                      ? 'bg-emerald-500/20 border border-emerald-500/30'
                      : 'bg-red-500/20 border border-red-500/30'
                  ]"
                >
                  <Check v-if="validationResult.canReplay" :size="20" class="text-emerald-400" />
                  <X v-else :size="20" class="text-red-400" />
                </div>
                <div>
                  <p :class="validationResult.canReplay ? 'text-emerald-300' : 'text-red-300'" class="font-medium">
                    {{ validationResult.canReplay ? $t('debug.replay.readyToReplay') : $t('debug.replay.cannotReplay') }}
                  </p>
                  <p v-if="!validationResult.canReplay" class="text-xs text-gray-400 mt-0.5">
                    {{ validationResult.reason }}
                  </p>
                  <p v-else class="text-xs text-gray-400 mt-0.5">
                    {{ $t('debug.replay.stepsRemaining', { count: validationResult.remainingSteps }) }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- Steps Inspector Tab -->
          <div v-else-if="activeTab === 'inspect'" class="flex-1 overflow-auto">
            <div v-if="executionSteps.length" class="divide-y divide-gray-700/30">
              <div
                v-for="step in executionSteps"
                :key="step.stepId"
                class="p-4 hover:bg-gray-800/30 transition-colors cursor-pointer"
                @click="inspectStep(step)"
              >
                <div class="flex items-center gap-3">
                  <!-- Status Icon -->
                  <div
                    :class="[
                      'w-10 h-10 rounded-xl flex items-center justify-center text-sm font-bold',
                      step.status === 'failed'
                        ? 'bg-red-500/20 border border-red-500/30 text-red-400'
                        : 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400'
                    ]"
                  >
                    <Check v-if="step.status === 'success'" :size="18" />
                    <X v-else-if="step.status === 'failed'" :size="18" />
                    <span v-else>{{ step.stepIndex + 1 }}</span>
                  </div>

                  <!-- Step Info -->
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                      <span class="font-semibold text-white">{{ step.stepId }}</span>
                      <span v-if="step.loopCount > 1" class="px-1.5 py-0.5 text-[10px] font-bold bg-violet-500/20 text-violet-300 rounded border border-violet-500/30">
                        x{{ step.loopCount }}
                      </span>
                    </div>
                    <div class="flex items-center gap-3 mt-1 text-xs text-gray-500">
                      <code class="font-mono">{{ step.moduleId }}</code>
                      <span class="tabular-nums">{{ step.durationMs }}ms</span>
                    </div>
                  </div>

                  <!-- Chevron -->
                  <ChevronRight :size="18" class="text-gray-600" />
                </div>

                <!-- Error Message -->
                <div v-if="step.error" class="mt-3 ml-13 p-2 bg-red-950/30 rounded-lg border border-red-500/20">
                  <code class="text-xs text-red-300 font-mono">{{ step.error }}</code>
                </div>

                <!-- Result Preview -->
                <div v-if="step.resultPreview && !step.error" class="mt-3 ml-13">
                  <pre class="text-xs text-gray-500 font-mono overflow-hidden whitespace-pre-wrap">{{ formatResult(step.resultPreview) }}</pre>
                </div>
              </div>
            </div>

            <div v-else class="flex items-center justify-center h-full text-gray-500">
              <div class="text-center">
                <Loader v-if="isLoadingSteps" :size="32" class="mx-auto mb-2 animate-spin text-emerald-400" />
                <p v-else class="text-sm">{{ $t('debug.replay.noStepsToInspect') }}</p>
              </div>
            </div>
          </div>

          <!-- History Tab -->
          <div v-else-if="activeTab === 'history'" class="flex-1 overflow-auto p-4">
            <div v-if="replayHistory.length" class="space-y-3">
              <div
                v-for="replay in replayHistory"
                :key="replay.id"
                @click="handleCompare(replay.id)"
                class="p-4 bg-gray-800/50 hover:bg-gray-700/50 rounded-xl border border-gray-700/30 cursor-pointer transition-all group"
              >
                <div class="flex items-center justify-between mb-2">
                  <div class="flex items-center gap-2">
                    <RotateCcw :size="14" class="text-emerald-400" />
                    <span class="text-sm font-medium text-white capitalize">{{ $t('debug.replay.replayType', { type: replay.type }) }}</span>
                  </div>
                  <span class="text-xs text-gray-500">{{ formatTimeAgo(replay.createdAt) }}</span>
                </div>
                <p v-if="replay.fromStep" class="text-xs text-gray-400">
                  {{ $t('debug.replay.from') }}: <code class="text-emerald-300">{{ replay.fromStep }}</code>
                </p>
                <div class="mt-3 flex items-center gap-2">
                  <button
                    class="px-3 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  >
                    {{ $t('debug.replay.compareBtn') }}
                  </button>
                  <code class="text-xs text-gray-500 font-mono truncate flex-1">{{ replay.id }}</code>
                </div>
              </div>
            </div>

            <div v-else class="flex flex-col items-center justify-center h-full text-gray-500">
              <History :size="40" class="mb-3 opacity-50" />
              <p class="text-sm">{{ $t('debug.replay.noHistory') }}</p>
              <p class="text-xs mt-1 text-gray-600">{{ $t('debug.replay.runReplayHint') }}</p>
            </div>
          </div>

          <!-- Comparison Tab -->
          <div v-else-if="activeTab === 'compare'" class="flex-1 overflow-hidden">
            <ReplayDiffViewer
              v-if="comparison"
              :original="comparison.original"
              :replay="comparison.replay"
              :differences="comparison.differences"
              @step-selected="handleDiffStepSelect"
            />
            <div v-else class="flex flex-col items-center justify-center h-full text-gray-500">
              <GitCompare :size="40" class="mb-3 opacity-50" />
              <p class="text-sm">{{ $t('debug.replay.noComparisonData') }}</p>
              <p class="text-xs mt-1 text-gray-600">{{ $t('debug.replay.selectReplayToCompare') }}</p>
            </div>
          </div>

          <!-- Execution Status Bar -->
          <div v-if="isReplaying || executionStatus" class="px-4 py-3 border-t border-gray-700/30" :class="executionStatusClass">
            <div class="flex items-center gap-3">
              <!-- Status Icon -->
              <div class="relative">
                <Loader v-if="executionStatus?.isRunning || isReplaying" :size="18" class="text-emerald-400 animate-spin" />
                <Check v-else-if="executionStatus?.isCompleted" :size="18" class="text-emerald-400" />
                <X v-else-if="executionStatus?.isFailed" :size="18" class="text-red-400" />
              </div>

              <!-- Status Info -->
              <div class="flex-1">
                <p class="text-sm font-medium" :class="executionStatus?.isFailed ? 'text-red-300' : 'text-emerald-300'">
                  {{ executionStatusText }}
                </p>
                <p class="text-xs text-gray-400 mt-0.5">
                  <span v-if="executionStatus?.isRunning && executionStatus?.currentStep !== undefined">
                    {{ $t('debug.replay.stepProgress', { current: executionStatus.currentStep + 1, total: executionStatus.totalSteps }) }}
                  </span>
                  <span v-else-if="executionStatus?.isCompleted">
                    {{ $t('debug.replay.completedIn', { duration: formatDuration(executionStatus.startTime, executionStatus.endTime) }) }}
                  </span>
                  <span v-else-if="executionStatus?.isFailed">
                    {{ executionStatus.error }}
                  </span>
                  <span v-else>
                    {{ $t('debug.replay.initializing') }}
                  </span>
                </p>

                <!-- Progress Bar -->
                <div v-if="executionStatus?.isRunning && executionStatus?.totalSteps" class="mt-2">
                  <div class="w-full h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-emerald-500 transition-all duration-300"
                      :style="{ width: `${((executionStatus.currentStep || 0) / executionStatus.totalSteps) * 100}%` }"
                    />
                  </div>
                </div>
              </div>

              <!-- Actions -->
              <div class="flex gap-2">
                <button
                  v-if="executionStatus?.isCompleted && currentReplayId"
                  @click="handleAutoCompare"
                  class="px-3 py-1.5 text-xs bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg transition-colors flex items-center gap-1"
                  aria-label="Compare"
                >
                  <GitCompare :size="12" />
                  {{ $t('debug.replay.compareBtn') }}
                </button>
                <button
                  v-if="executionStatus?.isRunning || isReplaying"
                  @click="handleCancel"
                  class="px-3 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  aria-label="Cancel replay"
                >
                  {{ $t('debug.replay.cancel') }}
                </button>
                <button
                  v-if="executionStatus?.isCompleted || executionStatus?.isFailed"
                  @click="clearExecutionStatus"
                  class="px-3 py-1.5 text-xs bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
                  aria-label="Dismiss"
                >
                  {{ $t('debug.replay.dismiss') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Footer Actions -->
        <div v-if="executionId" class="px-4 py-3 border-t border-gray-700/50 bg-gray-900/50">
          <!-- Action Feedback -->
          <div v-if="actionMessage" class="mb-3 p-3 rounded-lg text-sm" :class="actionMessage.type === 'success' ? 'bg-emerald-950/50 text-emerald-300 border border-emerald-500/30' : 'bg-red-950/50 text-red-300 border border-red-500/30'">
            {{ actionMessage.text }}
          </div>

          <div class="flex gap-3">
            <button
              v-if="comparison"
              @click="comparison = null; activeTab = 'setup'"
              class="flex-1 py-2.5 px-4 bg-gray-700 hover:bg-gray-600 text-white text-sm font-medium rounded-xl transition-colors cursor-pointer"
              aria-label="Back"
            >
              <ArrowLeft :size="16" class="inline mr-2 -mt-0.5" />
              {{ $t('debug.replay.back') }}
            </button>
            <button
              v-if="activeTab !== 'compare'"
              @click="handleValidate"
              :disabled="isValidating || (replayMode === 'step' && !selectedStepId)"
              class="flex-1 py-2.5 px-4 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:text-gray-500 disabled:cursor-not-allowed text-white text-sm font-medium rounded-xl transition-colors cursor-pointer"
            >
              <Loader v-if="isValidating" :size="16" class="inline mr-2 -mt-0.5 animate-spin" />
              <Zap v-else :size="16" class="inline mr-2 -mt-0.5" />
              {{ isValidating ? $t('debug.replay.validating') : $t('debug.replay.validate') }}
            </button>
            <button
              @click="handleStartReplay"
              :disabled="isReplaying || isStartingReplay || (replayMode === 'step' && !selectedStepId) || !!jsonError"
              class="flex-1 py-2.5 px-4 bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed text-white text-sm font-semibold rounded-xl transition-all shadow-lg shadow-emerald-500/20 disabled:shadow-none flex items-center justify-center gap-2 cursor-pointer"
            >
              <Loader v-if="isStartingReplay" :size="16" class="animate-spin" />
              <Play v-else :size="16" />
              {{ isStartingReplay ? $t('debug.replay.starting') : $t('debug.replay.startReplayBtn') }}
            </button>
          </div>
        </div>

        <!-- Step Detail Drawer -->
        <Transition
          enter-active-class="transition ease-out duration-200"
          enter-from-class="opacity-0 translate-y-full"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition ease-in duration-150"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-full"
        >
          <div
            v-if="inspectedStep"
            class="absolute bottom-0 left-0 right-0 bg-gray-900 border-t border-gray-700 shadow-2xl rounded-t-2xl max-h-[60%] flex flex-col"
          >
            <!-- Drawer Header -->
            <div class="flex items-center justify-between px-5 py-3 border-b border-gray-700/50">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-blue-400 text-sm font-bold">
                  {{ inspectedStep.stepIndex + 1 }}
                </div>
                <div>
                  <h4 class="text-sm font-semibold text-white">{{ inspectedStep.stepId }}</h4>
                  <code class="text-xs text-gray-500 font-mono">{{ inspectedStep.moduleId }}</code>
                </div>
              </div>
              <button @click="inspectedStep = null" class="p-1.5 text-gray-400 hover:text-white rounded-lg" aria-label="Close">
                <X :size="18" />
              </button>
            </div>

            <!-- Drawer Content -->
            <div class="flex-1 overflow-auto p-4 space-y-4">
              <!-- Params -->
              <div>
                <h5 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">{{ $t('debug.replay.parameters') }}</h5>
                <pre class="p-3 bg-gray-800/50 rounded-lg text-xs text-gray-300 font-mono overflow-auto">{{ JSON.stringify(inspectedStep.params || {}, null, 2) }}</pre>
              </div>

              <!-- Result -->
              <div>
                <h5 class="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">{{ $t('debug.replay.result') }}</h5>
                <pre class="p-3 bg-gray-800/50 rounded-lg text-xs text-gray-300 font-mono overflow-auto">{{ JSON.stringify(inspectedStep.resultPreview || {}, null, 2) }}</pre>
              </div>

              <!-- Error -->
              <div v-if="inspectedStep.error">
                <h5 class="text-xs font-bold text-red-400 uppercase tracking-widest mb-2">{{ $t('debug.error') }}</h5>
                <pre class="p-3 bg-red-950/30 rounded-lg border border-red-500/20 text-xs text-red-300 font-mono overflow-auto">{{ inspectedStep.error }}</pre>
              </div>
            </div>

            <!-- Drawer Actions -->
            <div class="px-4 py-3 border-t border-gray-700/50 flex gap-2">
              <button
                @click="selectStepForReplay(inspectedStep)"
                class="flex-1 py-2 px-4 bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-medium rounded-lg transition-colors"
                aria-label="Replay from here"
              >
                {{ $t('debug.replay.replayFromHere') }}
              </button>
              <button
                @click="inspectedStep = null"
                class="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white text-sm rounded-lg transition-colors"
                aria-label="Close"
              >
                {{ $t('debug.replay.close') }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  RotateCcw,
  X,
  Loader,
  History,
  Play,
  FastForward,
  Edit3,
  AlertCircle,
  Check,
  ChevronRight,
  ArrowLeft,
  Zap,
  GitCompare
} from 'lucide-vue-next'
import AppTextarea from '@/components/common/AppTextarea.vue'
import {
  useReplay,
  useReplayPanelState,
  useReplayStatusPolling,
  useReplayUtils
} from '@/composables/debug'
import { replayAPI } from '@/api/replay'
import ReplayDiffViewer from './ReplayDiffViewer.vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false
  },
  executionId: {
    type: String,
    default: null
  },
  steps: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'replay-started', 'compare-selected'])

const { t } = useI18n()

// ===== Replay API Composable =====
const {
  replayId,
  comparison,
  replayHistory,
  isReplaying,
  startReplay,
  compareExecutions,
  loadHistory,
  validateReplay,
  reset
} = useReplay({
  onSuccess: (event) => {
    if (event === 'replay_completed') {
      emit('replay-started', { replayId: replayId.value })
    }
  }
})

// ===== Panel State Composable =====
const {
  tabs,
  activeTab,
  replayMode,
  selectedStepId,
  showContextEditor,
  contextOverridesJson,
  jsonError,
  validationResult,
  inspectedStep,
  executionSteps,
  isLoadingSteps,
  contextKeys,
  isValidating,
  isStartingReplay,
  actionMessage,
  showMessage,
  inspectStep,
  selectStepForReplay
} = useReplayPanelState()

// ===== Status Polling Composable =====
const {
  executionStatus,
  currentReplayId,
  executionStatusClass,
  executionStatusText,
  startStatusPolling,
  stopStatusPolling,
  clearExecutionStatus,
  handleCancel: handleCancelBase
} = useReplayStatusPolling({ showMessage })

// ===== Utils Composable =====
const { formatDuration, formatTimeAgo, formatResult } = useReplayUtils()

// Load execution steps when panel opens
watch(() => props.isOpen, async (open) => {
  if (open && props.executionId) {
    await loadExecutionData()
  } else if (!open) {
    // Cleanup when panel closes
    stopStatusPolling()
  }
}, { immediate: true })

// Validate when step changes
watch(selectedStepId, async (stepId) => {
  if (stepId && props.executionId) {
    await handleValidate()
  }
})

async function loadExecutionData() {
  isLoadingSteps.value = true

  try {
    // Load steps
    const stepsData = await replayAPI.getExecutionSteps(props.executionId)
    executionSteps.value = stepsData.steps || []

    // Load history
    await loadHistory(props.executionId)

    // Get context keys from first step
    if (executionSteps.value.length > 0) {
      try {
        const contextData = await replayAPI.getContextAtStep(
          props.executionId,
          executionSteps.value[0].stepId,
          true
        )
        contextKeys.value = Object.keys(contextData.context || {})
      } catch (e) {
        contextKeys.value = []
      }
    }
  } catch (e) {
  } finally {
    isLoadingSteps.value = false
  }
}

// showMessage is provided by useReplayPanelState composable

async function handleValidate() {
  if (replayMode.value === 'step' && !selectedStepId.value) {
    validationResult.value = null
    return
  }

  isValidating.value = true
  actionMessage.value = null

  try {
    const stepId = replayMode.value === 'step' ? selectedStepId.value : executionSteps.value[0]?.stepId

    if (!stepId) {
      showMessage(t('error.noStepsToValidate'), 'error')
      isValidating.value = false
      return
    }

    const result = await validateReplay(props.executionId, stepId)
    validationResult.value = result.data || result

    if (validationResult.value?.canReplay) {
      showMessage(t('debug.replay.validationPassed', { count: validationResult.value.remainingSteps }), 'success')
    } else {
      showMessage(validationResult.value?.reason || t('validation.failed'), 'error')
    }
  } catch (e) {
    validationResult.value = { canReplay: false, reason: e.message }
    showMessage(`${t('validation.error')}: ${e.message}`, 'error')
  } finally {
    isValidating.value = false
  }
}

async function handleStartReplay() {
  if (jsonError.value) {
    showMessage(t('error.fixJsonFirst'), 'error')
    return
  }

  let overrides = {}
  try {
    overrides = JSON.parse(contextOverridesJson.value)
  } catch (e) {
    showMessage(t('error.invalidJsonContext'), 'error')
    return
  }

  isStartingReplay.value = true
  actionMessage.value = null
  executionStatus.value = null
  currentReplayId.value = null

  try {
    const config = {
      contextOverrides: overrides
    }

    if (replayMode.value === 'step' && selectedStepId.value) {
      config.stepId = selectedStepId.value
    }

    const result = await startReplay(props.executionId, config)

    if (result.ok) {
      currentReplayId.value = result.replayId
      showMessage(`Replay started! ID: ${result.replayId?.substring(0, 8)}...`, 'success')
      emit('replay-started', { replayId: result.replayId })

      // Start polling for status if actually executed (not dry run)
      if (result.executed) {
        startStatusPolling(result.replayId)
      } else {
        // Dry run - just show prepared message
        executionStatus.value = {
          isCompleted: true,
          status: 'prepared'
        }
      }

      // Reload history
      await loadHistory(props.executionId)
    } else {
      showMessage(result.error || t('error.failedToStartReplay'), 'error')
    }
  } catch (e) {
    showMessage(`Error: ${e.message}`, 'error')
  } finally {
    isStartingReplay.value = false
  }
}

// Status polling functions are provided by useReplayStatusPolling composable

async function handleAutoCompare() {
  if (currentReplayId.value) {
    await handleCompare(currentReplayId.value)
  }
}

// clearExecutionStatus and formatDuration are provided by composables
// Cleanup is handled by useReplayStatusPolling composable

async function handleCompare(replayExecutionId) {
  await compareExecutions(props.executionId, replayExecutionId)
  activeTab.value = 'compare'
  emit('compare-selected', { originalId: props.executionId, replayId: replayExecutionId })
}

function handleDiffStepSelect(stepId) {
  emit('compare-selected', { stepId })
}

function handleCancel() {
  handleCancelBase(reset)
}

// inspectStep, selectStepForReplay, formatTimeAgo, formatResult are provided by composables
</script>
