<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-content">
        <h1 class="header-title">仪表盘</h1>
        <p class="header-subtitle">故事世界概览</p>
      </div>
      <div class="header-actions">
        <button class="btn-refresh" @click="refreshAll" :disabled="isLoading">
          <span class="refresh-icon" :class="{ spinning: isLoading }">↻</span>
          刷新
        </button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="isLoading && !projects.length" class="loading-state">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <!-- Main Content -->
    <main v-else class="dashboard-content">
      <!-- Project Overview Cards - 3 Column Grid -->
      <section class="overview-section">
        <h2 class="section-title">项目概览</h2>
        <div class="overview-grid">
          <!-- Projects Card -->
          <div class="overview-card">
            <div class="card-icon projects-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <div class="card-content">
              <span class="card-value">{{ projectStore.projects.length }}</span>
              <span class="card-label">项目总数</span>
            </div>
            <div class="card-trend up" v-if="projectStore.projects.length > 0">
              <span>↑ 活跃</span>
            </div>
          </div>

          <!-- Characters Card -->
          <div class="overview-card">
            <div class="card-icon characters-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <div class="card-content">
              <span class="card-value">{{ characterStore.characters.length }}</span>
              <span class="card-label">角色数量</span>
            </div>
            <div class="card-trend up" v-if="characterStore.protagonists.length > 0">
              <span>{{ characterStore.protagonists.length }} 主角</span>
            </div>
          </div>

          <!-- Agents Card -->
          <div class="overview-card">
            <div class="card-icon agents-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="3"/>
                <path d="M12 1v6m0 6v10"/>
                <path d="M4.22 4.22l4.24 4.24m7.08 7.08l4.24 4.24"/>
                <path d="M1 12h6m6 0h10"/>
                <path d="M4.22 19.78l4.24-4.24m7.08-7.08l4.24-4.24"/>
              </svg>
            </div>
            <div class="card-content">
              <span class="card-value">{{ agentStore.activeAgents }}</span>
              <span class="card-label">活跃 Agent</span>
            </div>
            <div class="card-trend" :class="agentStore.activeAgents > 0 ? 'up' : 'neutral'">
              <span>{{ agentStore.agents.length }} 总计</span>
            </div>
          </div>
        </div>
      </section>

      <!-- System Health & Quick Actions Row -->
      <div class="health-actions-row">
        <!-- System Health Indicators -->
        <section class="health-section">
          <h2 class="section-title">系统状态</h2>
          <div class="health-grid">
            <!-- Status Badge -->
            <div class="health-badge" :style="{ '--health-color': agentStore.healthColor }">
              <span class="badge-indicator"></span>
              <span class="badge-text">{{ agentStore.healthBadge }}</span>
            </div>

            <!-- CPU Usage -->
            <div class="health-metric">
              <div class="metric-header">
                <span class="metric-label">CPU</span>
                <span class="metric-value">{{ agentStore.systemHealth.cpu }}%</span>
              </div>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${agentStore.systemHealth.cpu}%` }"
                ></div>
              </div>
            </div>

            <!-- Memory Usage -->
            <div class="health-metric">
              <div class="metric-header">
                <span class="metric-label">内存</span>
                <span class="metric-value">{{ agentStore.systemHealth.memory }}%</span>
              </div>
              <div class="progress-bar">
                <div 
                  class="progress-fill" 
                  :style="{ width: `${agentStore.systemHealth.memory}%` }"
                ></div>
              </div>
            </div>

            <!-- Active Simulations -->
            <div class="health-metric simulations">
              <span class="metric-icon">⚡</span>
              <div class="metric-info">
                <span class="metric-value">{{ agentStore.systemHealth.activeSimulations }}</span>
                <span class="metric-label">运行中模拟</span>
              </div>
            </div>
          </div>
        </section>

        <!-- Quick Actions -->
        <section class="actions-section">
          <h2 class="section-title">快捷操作</h2>
          <div class="actions-grid">
            <button class="action-btn" @click="navigateTo('/world')">
              <span class="action-icon">📖</span>
              <span class="action-text">创建故事</span>
            </button>
            <button class="action-btn" @click="navigateTo('/characters')">
              <span class="action-icon">👤</span>
              <span class="action-text">添加角色</span>
            </button>
            <button class="action-btn" @click="navigateTo('/chapter-editor')">
              <span class="action-icon">✏️</span>
              <span class="action-text">编辑章节</span>
            </button>
            <button class="action-btn" @click="navigateTo('/narrative')">
              <span class="action-icon">🎯</span>
              <span class="action-text">生成叙事</span>
            </button>
          </div>
        </section>
      </div>

      <!-- Activity Feed -->
      <section class="activity-section">
        <h2 class="section-title">最近活动</h2>
        <div class="activity-list">
          <div 
            v-for="activity in agentStore.activityLog" 
            :key="activity.id" 
            class="activity-item"
          >
            <div class="activity-marker" :class="activity.type"></div>
            <div class="activity-content">
              <span class="activity-action">{{ activity.action }}</span>
              <span class="activity-target">{{ activity.target }}</span>
            </div>
            <span class="activity-time">{{ formatTime(activity.timestamp) }}</span>
          </div>
          
          <div v-if="!agentStore.activityLog.length" class="activity-empty">
            <span class="empty-icon">📭</span>
            <span class="empty-text">暂无活动记录</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStoryStore } from '@/stores/storyStore'
import { useCharacterStore } from '@/stores/characterStore'
import { useAgentStore } from '@/stores/agentStore'
import { useDashboardStore } from '@/stores/dashboardStore'

// Router
const router = useRouter()

// Stores
const projectStore = useStoryStore()
const characterStore = useCharacterStore()
const agentStore = useAgentStore()
const dashboardStore = useDashboardStore()

// Loading state
const isLoading = ref(false)

// Computed
const hasData = computed(() => 
  projectStore.projects.length > 0 || 
  characterStore.characters.length > 0
)

// Format relative time
const formatTime = (timestamp) => {
  const now = new Date()
  const date = new Date(timestamp)
  const diff = now - date
  
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes} 分钟前`
  if (hours < 24) return `${hours} 小时前`
  return `${days} 天前`
}

// Navigate to route
const navigateTo = (path) => {
  router.push(path)
}

// Refresh all data
const refreshAll = async () => {
  isLoading.value = true
  try {
    await Promise.all([
      projectStore.fetchProjects(),
      agentStore.fetchAgents(),
      agentStore.fetchSystemHealth(),
      agentStore.fetchActivityLog()
    ])
  } catch (error) {
    console.error('Failed to refresh:', error)
  } finally {
    isLoading.value = false
  }
}

// Initialize data on mount
onMounted(async () => {
  await refreshAll()
})

// Cleanup on unmount
onUnmounted(() => {
  dashboardStore.stopAutoRefresh()
})

</script>

<style scoped>
/* Import design tokens */
@import '@/styles/tokens.css';

/* Dashboard Container */
.dashboard {
  min-height: 100%;
  background: var(--bg-primary);
  padding: var(--space-6);
}

/* Header */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-8);
}

.header-title {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  letter-spacing: var(--letter-spacing-tight);
  margin: 0;
}

.header-subtitle {
  font-size: var(--font-size-base);
  color: var(--text-secondary);
  margin: var(--space-1) 0 0 0;
}

/* Refresh Button */
.btn-refresh {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--bg-secondary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.btn-refresh:hover:not(:disabled) {
  background: var(--bg-tertiary);
}

.btn-refresh:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-icon {
  font-size: var(--font-size-lg);
  transition: transform var(--transition-slow);
}

.refresh-icon.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16);
  color: var(--text-secondary);
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--border-primary);
  border-top-color: var(--apple-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: var(--space-4);
}

/* Section Title */
.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--space-4) 0;
}

/* Overview Grid - 3 Columns */
.overview-section {
  margin-bottom: var(--space-8);
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

/* Overview Card */
.overview-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-card);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  cursor: default;
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-elevated);
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon svg {
  width: 24px;
  height: 24px;
}

.projects-icon {
  background: linear-gradient(135deg, rgba(0, 122, 255, 0.1) 0%, rgba(88, 86, 214, 0.1) 100%);
  color: var(--apple-blue);
}

.characters-icon {
  background: linear-gradient(135deg, rgba(52, 199, 89, 0.1) 0%, rgba(48, 209, 88, 0.1) 100%);
  color: var(--color-success);
}

.agents-icon {
  background: linear-gradient(135deg, rgba(255, 149, 0, 0.1) 0%, rgba(255, 107, 0, 0.1) 100%);
  color: var(--color-warning);
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.card-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  letter-spacing: var(--letter-spacing-tight);
}

.card-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.card-trend {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  width: fit-content;
}

.card-trend.up {
  background: rgba(52, 199, 89, 0.1);
  color: var(--color-success);
}

.card-trend.neutral {
  background: rgba(142, 142, 147, 0.1);
  color: var(--text-tertiary);
}

/* Health & Actions Row */
.health-actions-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

/* Health Section */
.health-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-card);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.health-grid {
  display: grid;
  grid-template-columns: auto 1fr 1fr auto;
  gap: var(--space-6);
  align-items: center;
}

/* Health Badge */
.health-badge {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: color-mix(in srgb, var(--health-color) 10%, transparent);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--health-color);
}

.badge-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--health-color);
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Health Metric */
.health-metric {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.metric-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
}

/* Progress Bar */
.progress-bar {
  height: 6px;
  background: var(--bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

/* Simulations Metric */
.health-metric.simulations {
  flex-direction: row;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--bg-primary);
  border-radius: var(--radius-md);
}

.metric-icon {
  font-size: var(--font-size-xl);
}

.metric-info {
  display: flex;
  flex-direction: column;
}

.health-metric.simulations .metric-value {
  font-size: var(--font-size-lg);
}

/* Actions Section */
.actions-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-card);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-3);
}

.action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  background: var(--bg-primary);
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
}

.action-btn:hover {
  background: var(--bg-tertiary);
  border-color: var(--apple-blue);
  transform: translateY(-2px);
}

.action-icon {
  font-size: var(--font-size-2xl);
}

.action-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

/* Activity Section */
.activity-section {
  background: var(--bg-secondary);
  border-radius: var(--radius-card);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--border-primary);
}

.activity-item:last-child {
  border-bottom: none;
}

/* Activity Timeline Left Border */
.activity-marker {
  width: 4px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--apple-blue);
}

.activity-marker.chapter { background: var(--apple-blue); }
.activity-marker.character { background: var(--color-success); }
.activity-marker.simulation { background: var(--color-warning); }
.activity-marker.graph { background: #AF52DE; }
.activity-marker.project { background: var(--color-info); }

.activity-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.activity-action {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.activity-target {
  font-size: var(--font-size-sm);
  color: var(--text-secondary);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  white-space: nowrap;
}

/* Empty Activity */
.activity-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.empty-icon {
  font-size: var(--font-size-3xl);
}

.empty-text {
  font-size: var(--font-size-sm);
}

/* Responsive */
@media (max-width: 1024px) {
  .overview-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .health-actions-row {
    grid-template-columns: 1fr;
  }
  
  .health-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .dashboard {
    padding: var(--space-4);
  }
  
  .overview-grid {
    grid-template-columns: 1fr;
  }
  
  .health-grid {
    grid-template-columns: 1fr;
  }
  
  .dashboard-header {
    flex-direction: column;
    gap: var(--space-4);
  }
}
</style>
