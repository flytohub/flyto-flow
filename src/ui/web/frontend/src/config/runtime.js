/** Runtime deployment contract loaded before the local UI starts. */

let runtimeConfig = null

export function setRuntimeConfig(value) {
  runtimeConfig = value && typeof value === 'object' ? { ...value } : null
}

export function getRuntimeConfig() {
  return runtimeConfig ? { ...runtimeConfig } : null
}

export function resetRuntimeConfig() {
  runtimeConfig = null
}
