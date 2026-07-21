import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { issuesAPI } from '@/api/issues'

export function useIssueFilters() {
  const { t } = useI18n()

  const issues = ref([])
  const loading = ref(true)
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = 20
  const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

  const openCount = ref(0)
  const closedCount = ref(0)

  const filterStatus = ref('open')
  const filterType = ref(null)
  const sortBy = ref('newest')
  const typeDropdownOpen = ref(false)
  const sortDropdownOpen = ref(false)
  const typeDropdownRef = ref(null)
  const sortDropdownRef = ref(null)

  const statusTabs = [
    { value: 'open', label: 'issues.status.open', fallback: 'Open' },
    { value: 'closed', label: 'issues.status.closed', fallback: 'Closed' },
    { value: null, label: 'issues.statusAll', fallback: 'All' },
  ]

  const typeOptions = ['bug', 'feature', 'question']
  const priorityOptions = ['low', 'medium', 'high']
  const sortOptions = ['newest', 'oldest', 'most_upvoted', 'recently_updated']

  async function loadIssues() {
    loading.value = true
    const result = await issuesAPI.list({
      status: filterStatus.value,
      type: filterType.value,
      sort: sortBy.value,
      page: currentPage.value,
      page_size: pageSize,
    })
    if (result.ok) {
      issues.value = result.issues
      total.value = result.total
    }
    loading.value = false
  }

  async function loadStats() {
    const [openResult, closedResult] = await Promise.all([
      issuesAPI.list({ status: 'open', page: 1, page_size: 1 }),
      issuesAPI.list({ status: 'closed', page: 1, page_size: 1 }),
    ])
    if (openResult.ok) openCount.value = openResult.total
    if (closedResult.ok) closedCount.value = closedResult.total
  }

  function handleClickOutside(e) {
    if (typeDropdownRef.value && !typeDropdownRef.value.contains(e.target)) {
      typeDropdownOpen.value = false
    }
    if (sortDropdownRef.value && !sortDropdownRef.value.contains(e.target)) {
      sortDropdownOpen.value = false
    }
  }

  watch([filterStatus, filterType, sortBy], () => {
    currentPage.value = 1
    loadIssues()
  })

  watch(currentPage, () => {
    loadIssues()
  })

  onMounted(() => {
    loadIssues()
    loadStats()
    document.addEventListener('click', handleClickOutside)
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
  })

  return {
    issues,
    loading,
    total,
    currentPage,
    totalPages,
    openCount,
    closedCount,
    filterStatus,
    filterType,
    sortBy,
    typeDropdownOpen,
    sortDropdownOpen,
    typeDropdownRef,
    sortDropdownRef,
    statusTabs,
    typeOptions,
    priorityOptions,
    sortOptions,
    loadIssues,
    loadStats,
  }
}
