/**
 * Wallet Store
 * Manages credit wallet state: balance, transactions, topup packages
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getWalletBalance,
  getWalletTransactions,
  getTopupPackages,
  redirectToTopup
} from '@/api/wallet'
import { formatCurrency } from '@/utils/format'
import { asBoolean, asNonNegativeInteger, asNumber, asObject, asRecordArray } from '@/utils/dataBoundary'

export const useWalletStore = defineStore('wallet', () => {
  // State
  const balance = ref(0)
  const balanceDollars = ref(0)
  const transactions = ref([])
  const transactionsTotal = ref(0)
  const transactionsPage = ref(1)
  const transactionsHasNext = ref(false)
  const packages = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const formattedBalance = computed(() => formatCurrency(balanceDollars.value))

  // Actions
  async function fetchBalance() {
    try {
      const result = await getWalletBalance()
      const normalized = asObject(result)
      if (normalized.ok) {
        balance.value = asNonNegativeInteger(normalized.balance, 0)
        balanceDollars.value = asNumber(normalized.balanceDollars ?? normalized.balance_dollars, 0)
      }
      return result
    } catch (err) {
      error.value = err.message
      return { ok: false, error: err.message }
    }
  }

  async function fetchTransactions(page = 1) {
    loading.value = true
    try {
      const result = await getWalletTransactions(page)
      const normalized = asObject(result)
      if (normalized.ok) {
        transactions.value = asRecordArray(normalized.transactions)
        transactionsTotal.value = asNonNegativeInteger(normalized.total, transactions.value.length)
        transactionsPage.value = asNonNegativeInteger(normalized.page, page) || 1
        transactionsHasNext.value = asBoolean(normalized.hasNext ?? normalized.has_next, false)
      }
      return result
    } catch (err) {
      error.value = err.message
      return { ok: false, error: err.message }
    } finally {
      loading.value = false
    }
  }

  async function fetchPackages() {
    try {
      const result = await getTopupPackages()
      const normalized = asObject(result)
      if (normalized.ok) {
        packages.value = asRecordArray(normalized.packages)
      }
      return result
    } catch (err) {
      error.value = err.message
      return { ok: false, error: err.message }
    }
  }

  async function topup(credits) {
    loading.value = true
    try {
      await redirectToTopup(credits)
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  function reset() {
    balance.value = 0
    balanceDollars.value = 0
    transactions.value = []
    transactionsTotal.value = 0
    transactionsPage.value = 1
    transactionsHasNext.value = false
    packages.value = []
    loading.value = false
    error.value = null
  }

  return {
    // State
    balance,
    balanceDollars,
    transactions,
    transactionsTotal,
    transactionsPage,
    transactionsHasNext,
    packages,
    loading,
    error,
    // Getters
    formattedBalance,
    // Actions
    fetchBalance,
    fetchTransactions,
    fetchPackages,
    topup,
    reset,
  }
})
