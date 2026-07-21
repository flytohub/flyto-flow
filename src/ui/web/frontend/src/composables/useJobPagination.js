import { ref, computed } from 'vue'

/**
 * Job pagination and status styling for Dashboard
 * @param {Object} options
 * @param {import('@/stores/deviceStore').DeviceStore} options.deviceStore - Device store instance
 * @param {number} [options.pageSize=5] - Number of jobs per page
 */
export function useJobPagination({ deviceStore, pageSize = 5 }) {
  const jobPage = ref(1)

  const jobTotalPages = computed(() => Math.ceil(deviceStore.jobs.length / pageSize) || 1)

  const paginatedJobs = computed(() => {
    const start = (jobPage.value - 1) * pageSize
    return deviceStore.jobs.slice(start, start + pageSize)
  })

  function jobStatusClass(status) {
    const m = {
      pending: 'bg-gray-200 dark:bg-gray-700 text-gray-500',
      claimed: 'bg-blue-100 dark:bg-blue-500/20 text-blue-600 dark:text-blue-400',
      running: 'bg-primary-100 dark:bg-primary-500/20 text-primary-600 dark:text-primary-400',
      success: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-600 dark:text-emerald-400',
      failed: 'bg-red-100 dark:bg-red-500/20 text-red-600 dark:text-red-400',
      cancelled: 'bg-gray-200 dark:bg-gray-700 text-gray-400',
    }
    return m[status] || m.pending
  }

  function jobBadgeClass(status) {
    const m = {
      pending: 'bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
      claimed: 'bg-blue-100 dark:bg-blue-500/20 text-blue-700 dark:text-blue-300',
      running: 'bg-primary-100 dark:bg-primary-500/20 text-primary-700 dark:text-primary-300',
      success: 'bg-emerald-100 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-300',
      failed: 'bg-red-100 dark:bg-red-500/20 text-red-700 dark:text-red-300',
      cancelled: 'bg-gray-200 dark:bg-gray-700 text-gray-500',
    }
    return m[status] || m.pending
  }

  return {
    jobPage,
    jobTotalPages,
    paginatedJobs,
    jobStatusClass,
    jobBadgeClass,
  }
}
