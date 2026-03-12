<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { useAgentStore } from '../stores/agentStore';
import { 
  Cpu, 
  Activity, 
  Wifi, 
  WifiOff, 
  AlertCircle,
  Clock,
  Play,
  Pause,
  RefreshCw,
  Plus
} from '@element-plus/icons-vue';

const agentStore = useAgentStore();

// Local state for execution queue
const executionQueue = ref<Array<{
  id: string;
  agentId: string;
  task: string;
  startTime: Date;
  status: 'pending' | 'running' | 'completed' | 'error';
}>>([]);

// Computed properties
const agents = computed(() => agentStore.agents);
const connectionState = computed(() => agentStore.connectionState);
const isConnected = computed(() => agentStore.isConnected);
const isConnecting = computed(() => agentStore.isConnecting);

// Get agent status badge class
function getAgentStatusClass(status: string) {
  switch (status) {
    case 'online': return 'badge-success';
    case 'busy': return 'badge-info';
    case 'offline': return 'badge-warning';
    case 'error': return 'badge-error';
    default: return 'badge-info';
  }
}

// Get agent status icon
function getAgentStatusIcon(status: string) {
  switch (status) {
    case 'online': return Wifi;
    case 'busy': return Activity;
    case 'offline': return WifiOff;
    case 'error': return AlertCircle;
    default: return Wifi;
  }
}

// Format connection state
function formatConnectionState(state: string) {
  switch (state) {
    case 'connected': return 'Connected';
    case 'connecting': return 'Connecting...';
    case 'reconnecting': return 'Reconnecting...';
    case 'disconnected': return 'Disconnected';
    default: return 'Unknown';
  }
}

// Format connection color
function getConnectionColor(state: string) {
  switch (state) {
    case 'connected': return 'badge-success';
    case 'connecting': return 'badge-info';
    case 'reconnecting': return 'badge-warning';
    case 'disconnected': return 'badge-error';
    default: return 'badge-info';
  }
}

// Format last seen time
function formatLastSeen(lastSeen: string) {
  const date = new Date(lastSeen);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  
  if (minutes < 1) return 'Just now';
  if (minutes < 60) return `${minutes}m ago`;
  if (minutes < 1440) return `${Math.floor(minutes / 60)}h ago`;
  return `${Math.floor(minutes / 1440)}d ago`;
}

// Trigger agent action (FAB)
function triggerAgentAction() {
  console.log('Triggering agent action...');
}

// Initialize data
onMounted(() => {
  agentStore.subscribeToStatus();
  
  // Simulate some execution queue data for demo
  executionQueue.value = [
    {
      id: 'task-1',
      agentId: 'agent-1',
      task: 'Generate chapter 5',
      startTime: new Date(Date.now() - 300000),
      status: 'running'
    },
    {
      id: 'task-2',
      agentId: 'agent-2',
      task: 'Edit scene 3',
      startTime: new Date(Date.now() - 600000),
      status: 'completed'
    },
    {
      id: 'task-3',
      agentId: 'agent-3',
      task: 'Analyze character arc',
      startTime: new Date(Date.now() - 1800000),
      status: 'pending'
    }
  ];
});
</script>

<template>
  <div class="agent-dashboard">
    <!-- Header Section -->
    <header class="dashboard-header" data-testid="dashboard-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="header-title" data-testid="dashboard-title">Agent Monitor</h1>
          <p class="header-subtitle" data-testid="dashboard-subtitle">Real-time status of your writing agents and execution queue</p>
        </div>
        <div class="connection-indicator" data-testid="connection-indicator">
          <el-icon :size="20" :class="getConnectionColor(connectionState)" data-testid="connection-icon">
            <component :is="isConnecting ? Clock : (isConnected ? Wifi : WifiOff)" />
          </el-icon>
          <span class="connection-text" data-testid="connection-text">{{ formatConnectionState(connectionState) }}</span>
        </div>
      </div>
    </header>

    <!-- Main Content Grid -->
    <div class="main-grid">
      <!-- Agent Status Cards -->
      <section class="agents-section" data-testid="agents-section">
        <div class="section-header">
          <h2 class="section-title">Agent Status</h2>
          <span class="section-count" data-testid="agent-count">{{ agents.length }} agents</span>
        </div>

        <div class="agents-grid">
          <div
            v-for="agent in agents"
            :key="agent.id"
            class="agent-card"
            :class="{ 'agent-active': agent.status === 'online' || agent.status === 'busy' }"
            data-testid="agent-card"
          >
            <div class="agent-header">
              <div class="agent-icon" data-testid="agent-status-icon">
                <el-icon :size="24">
                  <component :is="getAgentStatusIcon(agent.status)" />
                </el-icon>
              </div>
              <div class="agent-info">
                <h3 class="agent-name" data-testid="agent-name">Agent {{ agent.id }}</h3>
                <span :class="['badge', getAgentStatusClass(agent.status)]" data-testid="agent-status">
                  {{ agent.status }}
                </span>
              </div>
            </div>

            <div class="agent-details">
              <div class="agent-stat">
                <span class="stat-label">Last Seen</span>
                <span class="stat-value" data-testid="agent-last-seen">{{ formatLastSeen(agent.last_seen) }}</span>
              </div>
              <div class="agent-stat">
                <span class="stat-label">Tasks Completed</span>
                <span class="stat-value" data-testid="agent-tasks-completed">24</span>
              </div>
              <div class="agent-stat">
                <span class="stat-label">Success Rate</span>
                <span class="stat-value" data-testid="agent-success-rate">98%</span>
              </div>
            </div>

            <div class="agent-actions">
              <button class="btn btn-secondary" @click="triggerAgentAction">
                <el-icon><RefreshCw /></el-icon>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Execution Queue Timeline -->
      <section class="queue-section" data-testid="queue-section">
        <div class="section-header">
          <h2 class="section-title">Execution Queue</h2>
          <span class="section-count" data-testid="queue-task-count">{{ executionQueue.length }} tasks</span>
        </div>

        <div class="timeline">
          <div
            v-for="task in executionQueue"
            :key="task.id"
            class="timeline-item"
            :class="{
              'timeline-running': task.status === 'running',
              'timeline-completed': task.status === 'completed',
              'timeline-pending': task.status === 'pending',
              'timeline-error': task.status === 'error'
            }"
            data-testid="timeline-item"
          >
            <div class="timeline-content">
              <div class="timeline-header">
                <el-icon class="timeline-icon" data-testid="timeline-icon">
                  <component :is="task.status === 'running' ? Play :
                              task.status === 'completed' ? CircleCheck :
                              task.status === 'error' ? AlertCircle : Clock" />
                </el-icon>
                <span class="timeline-title" data-testid="timeline-title">{{ task.task }}</span>
              </div>
              <p class="timeline-description" data-testid="timeline-agent-id">Agent {{ task.agentId }}</p>
              <span class="timeline-time" data-testid="timeline-timestamp">{{ formatLastSeen(task.startTime.toISOString()) }}</span>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- Floating Action Button -->
    <button class="fab" data-testid="fab" @click="triggerAgentAction">
      <el-icon><Plus /></el-icon>
    </button>
  </div>
</template>

<style scoped>
.agent-dashboard {
  min-height: 100%;
  padding: var(--space-8);
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.dashboard-header {
  margin-bottom: var(--space-10);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-6);
  width: 100%;
}

.header-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.header-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
  max-width: 500px;
}

.connection-indicator {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
}

.connection-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

/* Main Grid */
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-6);
  margin-bottom: var(--space-8);
}

/* Sections */
.section {
  margin-bottom: var(--space-8);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.section-count {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  background: var(--color-border-light);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
}

/* Agent Cards */
.agents-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
}

.agent-card {
  background: var(--color-background);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  cursor: pointer;
}

.agent-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.agent-active {
  animation: pulse 2s infinite;
  border: 1px solid var(--color-primary);
}

.agent-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.agent-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  color: var(--color-primary);
}

.agent-info {
  flex: 1;
}

.agent-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.agent-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  margin-bottom: var(--space-4);
}

.agent-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.stat-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.agent-actions {
  display: flex;
  justify-content: flex-end;
}

/* Timeline */
.queue-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.timeline {
  position: relative;
  padding-left: var(--space-6);
}

.timeline-item {
  position: relative;
  padding-bottom: var(--space-5);
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: var(--space-2);
  bottom: 0;
  width: 2px;
  background: var(--color-border);
  border-radius: var(--radius-full);
}

.timeline-item.timeline-running::before {
  background: var(--color-primary);
}

.timeline-item.timeline-completed::before {
  background: var(--color-success);
}

.timeline-item.timeline-pending::before {
  background: var(--color-warning);
}

.timeline-item.timeline-error::before {
  background: var(--color-error);
}

.timeline-content {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  border: 1px solid var(--color-border);
  transition: transform var(--transition-base);
}

.timeline-content:hover {
  transform: translateX(4px);
}

.timeline-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.timeline-icon {
  color: var(--color-primary);
  font-size: 16px;
}

.timeline-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.timeline-description {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.timeline-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Floating Action Button */
.fab {
  position: fixed;
  bottom: var(--space-6);
  right: var(--space-6);
  width: 56px;
  height: 56px;
  border-radius: var(--radius-full);
  background: var(--gradient-primary);
  color: white;
  border: none;
  box-shadow: var(--shadow-lg);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  z-index: var(--z-sticky);
}

.fab:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-xl);
}

.fab:active {
  transform: translateY(0);
}

/* Pulse Animation */
@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

/* Responsive */
@media (max-width: 1024px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
  
  .agents-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .agent-dashboard {
    padding: var(--space-4);
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-4);
  }
  
  .header-title {
    font-size: var(--font-size-2xl);
  }
}
</style>