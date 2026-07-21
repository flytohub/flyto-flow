import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post } from '@/api/client'
import { ENDPOINTS } from '@/api/config'

export const useDeviceStore = defineStore('device', () => {
  const devices = ref([])
  const jobs = ref([])
  const loading = ref(false)
  const jobsLoading = ref(false)

  const onlineDevices = computed(() => devices.value.filter(d => d.isOnline))
  const onlineCount = computed(() => onlineDevices.value.length)

  async function fetchDevices() {
    loading.value = true
    try {
      const res = await get(ENDPOINTS.DEVICES.LIST)
      devices.value = res.devices || []
    } catch {
      devices.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchJobs(limit = 20) {
    jobsLoading.value = true
    try {
      const res = await get(ENDPOINTS.DEVICES.JOBS, { params: { limit } })
      jobs.value = res.jobs || []
    } catch {
      jobs.value = []
    } finally {
      jobsLoading.value = false
    }
  }

  async function cancelJob(jobId) {
    try {
      await post(ENDPOINTS.DEVICES.JOB_CANCEL(jobId))
      const job = jobs.value.find(j => j.id === jobId)
      if (job) job.status = 'cancelled'
      return true
    } catch {
      return false
    }
  }

  async function revokeDevice(deviceId) {
    try {
      await post(ENDPOINTS.DEVICES.REVOKE(deviceId))
      devices.value = devices.value.filter(d => d.id !== deviceId)
      return true
    } catch {
      return false
    }
  }

  function getDeviceName(deviceId) {
    const d = devices.value.find(d => d.id === deviceId)
    return d?.name || deviceId?.slice(0, 8) || '-'
  }

  async function setRemoteWake(deviceId, enabled) {
    try {
      await post(ENDPOINTS.DEVICES.REMOTE_WAKE_SETTING(deviceId), { enabled })
      const device = devices.value.find(d => d.id === deviceId)
      if (device) device.remoteWakeEnabled = enabled
      return true
    } catch {
      return false
    }
  }

  function reset() {
    devices.value = []
    jobs.value = []
  }

  return {
    devices, jobs, loading, jobsLoading,
    onlineDevices, onlineCount,
    fetchDevices, fetchJobs, cancelJob, revokeDevice, getDeviceName, setRemoteWake, reset,
  }
})
