import { useI18n } from 'vue-i18n'
import { MS_PER_MINUTE, MS_PER_HOUR, MS_PER_DAY } from '@/constants/time'

export function useRelativeTime() {
  const { t } = useI18n()

  function formatRelativeTime(dateStr) {
    if (!dateStr) return ''
    const diff = Date.now() - new Date(dateStr).getTime()

    if (diff < MS_PER_MINUTE) return t('dashboardPage.recentActivity.justNow')
    if (diff < MS_PER_HOUR) return t('dashboardPage.recentActivity.minutesAgo', { count: Math.floor(diff / MS_PER_MINUTE) })
    if (diff < MS_PER_DAY) return t('dashboardPage.recentActivity.hoursAgo', { count: Math.floor(diff / MS_PER_HOUR) })
    if (diff < 2 * MS_PER_DAY) return t('dashboardPage.recentActivity.yesterday')
    if (diff < 7 * MS_PER_DAY) return t('dashboardPage.recentActivity.daysAgo', { count: Math.floor(diff / MS_PER_DAY) })
    return new Date(dateStr).toLocaleDateString()
  }

  return { formatRelativeTime }
}
