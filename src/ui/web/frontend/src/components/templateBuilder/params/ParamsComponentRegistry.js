/**
 * Params Component Registry
 *
 * 後端 paramsSchema 為唯一真相源，前端只渲染。
 * 有 schema → SchemaParamsRenderer
 * 特殊 UI (FlowControl, Code, HTTP 等) → 自訂元件
 */

import { defineAsyncComponent, markRaw } from 'vue'
import SchemaParamsRenderer from '../SchemaParamsRenderer.vue'

const asyncComponents = {
  FlowControlParams: defineAsyncComponent(() => import('../FlowControlParams.vue')),
  CodeNodeParams: defineAsyncComponent(() => import('../CodeNodeParams.vue')),
  HttpNodeParams: defineAsyncComponent(() => import('../HttpNodeParamsSimplified.vue')),
  LLMChainParams: defineAsyncComponent(() => import('../LLMChainParams.vue')),
  VectorStoreParams: defineAsyncComponent(() => import('../VectorStoreParams.vue')),
  AIAgentParams: defineAsyncComponent(() => import('../AIAgentParams.vue')),
  FormInputParams: defineAsyncComponent(() => import('../FormInputParams.vue')),
}

const PARAMS_COMPONENTS = {
  SchemaParamsRenderer: markRaw(SchemaParamsRenderer),
  ...asyncComponents,
  // Aliases
  BranchParams: asyncComponents.FlowControlParams,
  SwitchParams: asyncComponents.FlowControlParams,
  LoopParams: asyncComponents.FlowControlParams,
  CodeParams: asyncComponents.CodeNodeParams,
  HttpParams: asyncComponents.HttpNodeParams,
}

function hasVisibleSchema(schema) {
  if (!schema?.properties) return false
  return Object.values(schema.properties).some(v => !v.hidden)
}

/**
 * 從模組資料取得參數元件
 */
export function getParamsComponentForModule(moduleData, modulesStore = null) {
  // 1. 有 paramsSchema → SchemaParamsRenderer
  if (hasVisibleSchema(moduleData?.paramsSchema)) {
    return PARAMS_COMPONENTS.SchemaParamsRenderer
  }

  // 2. 從 modulesStore 查詢
  if (modulesStore && moduleData?.module_id) {
    const metadata = modulesStore.modulesMetadata?.[moduleData.module_id]
    if (hasVisibleSchema(metadata?.paramsSchema)) {
      return PARAMS_COMPONENTS.SchemaParamsRenderer
    }
  }

  // 3. 自訂元件（排除已棄用的 GenericParams）
  const componentName = moduleData?.uiConfig?.paramsComponent
  if (componentName && componentName !== 'GenericParams') {
    const component = PARAMS_COMPONENTS[componentName] || null
    if (component) return component
  }

  // 4. Fallback：有 params 就用 generic mode
  if (moduleData?.params && Object.keys(moduleData.params).length > 0) {
    return PARAMS_COMPONENTS.SchemaParamsRenderer
  }

  return null
}

export { PARAMS_COMPONENTS }
