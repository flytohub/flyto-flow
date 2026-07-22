/** Local execution capabilities exposed by the CE backend. */
import { get } from './client'

export async function getCapabilities() {
  try {
    return await get('/capabilities')
  } catch (error) {
    return { ok: false, capabilities: [], error: error.userMessage || error.message }
  }
}

export const capabilitiesAPI = { getCapabilities }
export default capabilitiesAPI
