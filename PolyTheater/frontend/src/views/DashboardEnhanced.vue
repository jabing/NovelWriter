<template>
  <div class="dashboard-enhanced">
    <header class="dashboard-header">
      <h1>📊 仪表盘</h1>
      <button @click="handleRefresh" :disabled="loading" class="btn-refresh">↻ 刷新</button>
    </header>
    
    <div v-if="loading" class="loading">加载中...</div>
    
    <main v-else>
      <section class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon">📁</div>
          <div class="stat-value">{{ stats.projects }}</div>
          <div class="stat-label">项目</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">👥</div>
          <div class="stat-value">{{ stats.characters }}</div>
          <div class="stat-label">角色</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⚡</div>
          <div class="stat-value">{{ stats.events }}</div>
          <div class="stat-label">事件</div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">💚</div>
          <div class="stat-value" :class="healthClass">{{ healthStatus }}</div>
          <div class="stat-label">系统</div>
        </div>
      </section>
      
      <div class="charts-container">
        <div class="chart-box">
          <h3>📊 数据分布</h3>
          <v-chart class="chart" :option="pieOption" autoresize />
        </div>
        <div class="chart-box">
          <h3>📈 趋势</h3>
          <v-chart class="chart" :option="lineOption" autoresize />
        </div>
      </div>
      
      <section class="activity">
        <h3>📋 最近活动</h3>
        <div v-for="item in activity" :key="item.id" class="activity-item">
          <span>{{ getActivityIcon(item.type) }}</span>
          <span>{{ formatAction(item.action) }} {{ item.entity_name }}</span>
          <span class="time">{{ formatTime(item.timestamp) }}</span>
        </div>
        <div v-if="!activity.length" class="empty">暂无活动</div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useDashboardStore } from '@/stores/dashboardStore'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart } from 'echarts/charts'
import { TooltipComponent, LegendComponent } from 'echarts/components'

use([CanvasRenderer, PieChart, LineChart, TooltipComponent, LegendComponent])

const dashboardStore = useDashboardStore()
const loading = ref(false)

const stats = computed(() => dashboardStore.stats)
const activity = computed(() => dashboardStore.activity)
const healthStatus = computed(() => 
  dashboardStore.health.database?.status === 'connected' ? '正常' : '异常'
)
const healthClass = computed(() => 
  dashboardStore.health.database?.status === 'connected' ? 'ok' : 'error'
)

const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [{
    type: 'pie',
    radius: ['40%', '70%'],
    data: [
      { value: stats.value.projects, name: '项目' },
      { value: stats.value.characters, name: '角色' },
      { value: stats.value.events, name: '事件' }
    ]
  }]
}))

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  xAxis: { type: 'category', data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] },
  yAxis: { type: 'value' },
  series: [
    { name: '项目', type: 'line', smooth: true, data: [1, 2, 3, 4, 5, 6, 7] },
    { name: '角色', type: 'line', smooth: true, data: [2, 3, 4, 5, 6, 7, 8] }
  ]
}))

function getActivityIcon(type) {
  return { project: '📁', character: '👤', event: '⚡' }[type] || '📌'
}

function formatAction(action) {
  return { created: '创建', updated: '更新', deleted: '删除' }[action] || action
}

function formatTime(ts) {
  if (!ts) return ''
  const diff = Date.now() - new Date(ts)
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return Math.floor(diff/60000) + '分钟前'
  return new Date(ts).toLocaleString()
}

async function handleRefresh() {
  loading.value = true
  await dashboardStore.refreshAll()
  loading.value = false
}

onMounted(() => dashboardStore.startAutoRefresh(30000))
onUnmounted(() => dashboardStore.stopAutoRefresh())
</script>

<style scoped>
.dashboard-enhanced { min-height: 100vh; background: linear-gradient(135deg, #667eea, #764ba2); padding: 2rem; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; background: white; padding: 1.5rem; border-radius: 12px; }
.btn-refresh { padding: 0.75rem 1.5rem; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border: none; border-radius: 8px; cursor: pointer; }
.loading { text-align: center; padding: 4rem; color: white; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.stat-card { background: white; padding: 1.5rem; border-radius: 12px; text-align: center; }
.stat-icon { font-size: 2.5rem; }
.stat-value { font-size: 2.5rem; font-weight: bold; margin: 0.5rem 0; }
.stat-value.ok { color: #4CAF50; }
.stat-value.error { color: #f44336; }
.stat-label { color: #718096; }
.charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
.chart-box { background: white; padding: 1.5rem; border-radius: 12px; }
.chart { height: 300px; }
.activity { background: white; padding: 1.5rem; border-radius: 12px; }
.activity-item { display: flex; gap: 1rem; padding: 0.75rem; border-bottom: 1px solid #eee; }
.time { margin-left: auto; color: #a0aec0; }
.empty { text-align: center; padding: 2rem; color: #a0aec0; }
</style>
