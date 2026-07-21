/** Ensure value is an array, returning empty array for non-array values */
const normalizeList = (value) => (Array.isArray(value) ? value : [])

/** Normalize raw robot data with safe defaults */
export function normalizeRobot(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    machineName: raw.machineName,
    machineIp: raw.machineIp,
    status: raw.status,
    osType: raw.osType,
    lastHeartbeat: raw.lastHeartbeat,
    capabilities: normalizeList(raw.capabilities),
    maxConcurrentJobs: raw.maxConcurrentJobs ?? 1,
    tags: normalizeList(raw.tags)
  }
}

/** Normalize robot fleet statistics */
export function normalizeRobotStats(raw = {}) {
  return {
    total: raw.total ?? 0,
    online: raw.online ?? 0,
    offline: raw.offline ?? 0,
    busy: raw.busy ?? 0
  }
}

/** Normalize raw job data with safe defaults */
export function normalizeJob(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    workflowId: raw.workflowId,
    workflowName: raw.workflowName,
    robotId: raw.robotId,
    robotName: raw.robotName,
    status: raw.status,
    startedAt: raw.startedAt,
    durationMs: raw.durationMs ?? null,
    enabled: raw.enabled ?? true,
    nextRun: raw.nextRun ?? null,
    scheduleType: raw.scheduleType,
    cron: raw.cron,
    intervalValue: raw.intervalValue,
    intervalUnit: raw.intervalUnit
  }
}

/** Normalize raw queue data with safe defaults */
export function normalizeQueue(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    workflowId: raw.workflowId ?? null,
    workflowName: raw.workflowName ?? '-',
    itemCount: raw.itemCount ?? 0,
    pending: raw.pending ?? 0,
    processing: raw.processing ?? 0,
    completed: raw.completed ?? 0,
    failed: raw.failed ?? 0,
    maxRetries: raw.maxRetries ?? 0
  }
}

/** Normalize queue item statistics */
export function normalizeQueueStats(raw = {}) {
  return {
    totalItems: raw.totalItems ?? 0,
    pending: raw.pending ?? 0,
    processing: raw.processing ?? 0,
    completed: raw.completed ?? 0,
    failed: raw.failed ?? 0
  }
}

/** Normalize raw transaction data with safe defaults */
export function normalizeTransaction(raw = {}) {
  return {
    id: raw.id,
    workflowName: raw.workflowName ?? '-',
    status: raw.status ?? 'in_progress',
    checkpoints: normalizeList(raw.checkpoints)
  }
}

/** Normalize raw state machine data with safe defaults */
export function normalizeStateMachine(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description ?? '',
    active: raw.active ?? true,
    stateCount: raw.stateCount ?? 0,
    instanceCount: raw.instanceCount ?? 0,
    states: normalizeList(raw.states),
    transitions: normalizeList(raw.transitions)
  }
}

/** Normalize state machine statistics */
export function normalizeStateMachineStats(raw = {}) {
  return {
    machines: raw.machines ?? 0,
    instances: raw.instances ?? 0,
    activeInstances: raw.activeInstances ?? 0,
    completed: raw.completed ?? 0,
    transitionsToday: raw.transitionsToday ?? 0
  }
}

/** Normalize process mining statistics */
export function normalizeProcessStats(raw = {}) {
  return {
    totalCases: raw.totalCases ?? 0,
    variants: raw.variants ?? 0,
    avgDuration: raw.avgDuration ?? 0,
    conformance: raw.conformance ?? 0
  }
}

/** Normalize raw IDP document data with safe defaults */
export function normalizeDocument(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    type: raw.type,
    size: raw.size ?? 0,
    status: raw.status ?? 'pending',
    progress: raw.progress ?? 0,
    model: raw.model ?? null,
    confidence: raw.confidence ?? null,
    extractedData: raw.extractedData ?? null,
    completedAt: raw.completedAt ?? null,
    updatedAt: raw.updatedAt ?? null
  }
}

/** Normalize IDP model data with safe defaults */
export function normalizeIdpModel(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    description: raw.description ?? '',
    accuracy: raw.accuracy ?? 0
  }
}

/** Normalize IDP processing statistics */
export function normalizeIdpStats(raw = {}) {
  return {
    processed: raw.processed ?? raw.completed ?? 0,
    pending: raw.pending ?? 0,
    accuracy: raw.accuracy ?? raw.avgAccuracy ?? 0,
    activeModels: raw.activeModels ?? raw.models ?? 0
  }
}

/** Normalize raw agent data with safe defaults */
export function normalizeAgent(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    status: raw.status ?? 'offline',
    os: raw.os ?? 'unknown',
    lastSeen: raw.lastSeen ?? '',
    currentTask: raw.currentTask ?? null,
    taskProgress: raw.taskProgress ?? 0
  }
}

/** Normalize agent fleet statistics */
export function normalizeAgentStats(raw = {}) {
  return {
    total: raw.total ?? 0,
    online: raw.online ?? 0,
    offline: raw.offline ?? 0,
    busy: raw.busy ?? 0,
    successRate: raw.successRate ?? 0
  }
}

/** Normalize raw recording data with safe defaults */
export function normalizeRecording(raw = {}) {
  return {
    id: raw.id,
    name: raw.name,
    steps: raw.steps ?? 0,
    duration: raw.duration ?? '-',
    createdAt: raw.createdAt ?? '-'
  }
}

/** Normalize raw process data with safe defaults */
export function normalizeProcess(raw = {}) {
  return {
    id: raw.id ?? raw.name,
    name: raw.name
  }
}

/** Normalize process discovery result with safe defaults */
export function normalizeDiscoveryResult(raw = {}) {
  return {
    processModel: raw.processModel ?? null,
    variants: normalizeList(raw.variants),
    bottlenecks: normalizeList(raw.bottlenecks),
    suggestions: normalizeList(raw.suggestions),
    stats: raw.stats || {}
  }
}
