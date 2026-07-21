import { get, post, put, del } from './client'

const BASE = '/packages'

export const packagesAPI = {
  async getStatus() { return get(`${BASE}/status`) },
  async updatePackage(id) { return post(`${BASE}/${id}/update`) },
  async installPackage(id) { return post(`${BASE}/${id}/install`) },
  async removePackage(id) { return del(`${BASE}/${id}`) },
  async setAutoUpdate(id, enabled) { return put(`${BASE}/${id}/auto-update`, { enabled }) },
}
