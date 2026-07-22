/** Local-only CE API client. No identity, analytics, or hosted fallback. */
import axios from 'axios'
import { API_URL, REQUEST_TIMEOUT } from './config'
import { convertKeysToSnake, convertKeysToCamel } from './caseConversion'
import { setRuntimeConfig } from '@/config/runtime'

const LOOPBACK_HOSTS = new Set(['127.0.0.1', 'localhost', '[::1]', '::1'])

function assertLocalApiTarget(value) {
  if (!value || value.startsWith('/')) return
  const target = new URL(value, window.location.origin)
  if (target.origin === window.location.origin || LOOPBACK_HOSTS.has(target.hostname)) return
  throw new Error(`CE refuses a non-local API target: ${target.origin}`)
}

const client = axios.create({
  baseURL: API_URL,
  timeout: REQUEST_TIMEOUT,
  headers: { 'Content-Type': 'application/json' }
})

client.interceptors.request.use(config => {
  assertLocalApiTarget(config.baseURL || API_URL)
  if (config.data && !(config.data instanceof FormData)) {
    config.data = convertKeysToSnake(config.data)
  } else if (config.data instanceof FormData) {
    delete config.headers['Content-Type']
  }
  if (config.params) config.params = convertKeysToSnake(config.params)
  return config
})

client.interceptors.response.use(
  response => {
    if (response.data && typeof response.data === 'object') {
      response.data = convertKeysToCamel(response.data)
    }
    return response
  },
  error => {
    const data = error.response?.data
    error.userMessage = data?.detail || data?.error || error.message || 'Request failed'
    return Promise.reject(error)
  }
)

function request(method, url, data, config = {}) {
  const { retry: _retry, ...axiosConfig } = config
  return client.request({ method, url, data, ...axiosConfig }).then(response => response.data)
}

export function get(url, config = {}) { return request('get', url, undefined, config) }
export function post(url, data = {}, config = {}) { return request('post', url, data, config) }
export function put(url, data = {}, config = {}) { return request('put', url, data, config) }
export function patch(url, data = {}, config = {}) { return request('patch', url, data, config) }
export function del(url, config = {}) { return request('delete', url, undefined, config) }

export async function upload(url, formData, onUploadProgress) {
  return post(url, formData, { onUploadProgress })
}

export async function download(url, filename) {
  const response = await client.get(url, { responseType: 'blob' })
  const downloadUrl = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = downloadUrl
  link.download = filename
  link.click()
  window.URL.revokeObjectURL(downloadUrl)
  return response.data
}

export async function initClient() {
  if (typeof window === 'undefined') return
  assertLocalApiTarget(API_URL)
  if (!import.meta.env.VITE_API_URL && !import.meta.env.VITE_API_BASE_URL) {
    client.defaults.baseURL = `${window.location.origin}/api`
  }
  try {
    const response = await client.get('/runtime-config')
    setRuntimeConfig(response.data)
  } catch {
    setRuntimeConfig(null)
  }
}

export { client as axiosInstance }
export default { get, post, put, patch, delete: del, upload, download, client, initClient }
