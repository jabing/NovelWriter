/**
 * Dashboard Store - 管理 Dashboard 状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:5001/api',
  timeout: 30000
})

export const useDashboardStore = defineStore('dashboard', () => {
  // ============================================
  // State
  // ============================================
  
  const stats = ref({
    projects: 0,
    active_projects: 0,
    characters: 0,
    events: 0
  })
  
  const activity = ref([])
  
  const health = ref({
    database: {
      status: 'unknown',
      response_time_ms: null
    }
  })
  
  const loading = ref(false)
  const error = ref(null)
  const lastUpdated = ref(null)
  const refreshInterval = ref(null)

  // ============================================
  // Computed
  // ============================================
  
  const hasData = computed(() => {
    return stats.value.projects > 0 || stats.value.characters > 0
  })
  
  const isEmpty = computed(() => {
    return !hasData.value && !loading.value && !error.value
  })

  // ============================================
  // Actions
  // ============================================
  
  /**
   * 获取统计数据
   */
  async function fetchStats() {
    loading.value = true
    error.value = null
    
    try {
      const response = await api.get('/dashboard/stats')
      if (response.data.success) {
        stats.value = response.data.data
        lastUpdated.value = new Date()
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || err.message
      console.error('Failed to fetch stats:', error.value)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取活动日志
   */
  async function fetchActivity() {
    try {
      const response = await api.get('/dashboard/activity')
      if (response.data.success) {
        activity.value = response.data.data
      }
    } catch (err) {
      console.error('Failed to fetch activity:', err.message)
    }
  }
  
  /**
   * 获取健康状态
   */
  async function fetchHealth() {
    try {
      const response = await api.get('/dashboard/health/detailed')
      if (response.data.success) {
        health.value = response.data.data
      }
    } catch (err) {
      console.error('Failed to fetch health:', err.message)
    }
  }
  
  /**
   * 刷新所有数据
   */
  async function refreshAll() {
    await Promise.all([
      fetchStats(),
      fetchActivity(),
      fetchHealth()
    ])
  }
  
  /**
   * 启动自动刷新
   * @param {number} intervalMs - 刷新间隔（毫秒），默认 30 秒
   */
  function startAutoRefresh(intervalMs = 30000) {
    // 清除已有的定时器
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
    }
    
    // 立即刷新一次
    refreshAll()
    
    // 设置定时器
    refreshInterval.value = setInterval(() => {
      refreshAll()
    }, intervalMs)
  }
  
  /**
   * 停止自动刷新
   */
  function stopAutoRefresh() {
    if (refreshInterval.value) {
      clearInterval(refreshInterval.value)
      refreshInterval.value = null
    }
  }

  return {
    // State
    stats,
    activity,
    health,
    loading,
    error,
    lastUpdated,
    
    // Computed
    hasData,
    isEmpty,
    
    // Actions
    fetchStats,
    fetchActivity,
    fetchHealth,
    refreshAll,
    startAutoRefresh,
    stopAutoRefresh
  }
})
