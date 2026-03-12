<template>
  <div class="agent-history">
    <div class="header">
      <h2 class="title">Agent Execution History</h2>
      <div class="controls">
        <select v-model="selectedAgentType" class="agent-filter">
          <option value="">All Agents</option>
          <option value="writer">Writer</option>
          <option value="editor">Editor</option>
          <option value="reviewer">Reviewer</option>
          <option value="planner">Planner</option>
        </select>
      </div>
    </div>

    <div class="timeline">
      <div 
        v-for="(execution, index) in filteredExecutions" 
        :key="execution.id" 
        class="timeline-item"
        :class="{ 'timeline-item--active': execution.status === 'completed' }"
      >
        <div class="timeline-content">
          <div class="timeline-header">
            <div class="status-badge" :class="getStatusClass(execution.status)">
              <span class="status-icon">{{ getStatusIcon(execution.status) }}</span>
              <span class="status-text">{{ execution.status }}</span>
            </div>
            <div class="timestamp">{{ formatTimestamp(execution.timestamp) }}</div>
          </div>
          
          <div class="agent-info">
            <h3 class="agent-name">{{ execution.agentName }}</h3>
            <p class="agent-type">{{ execution.agentType }}</p>
          </div>
          
          <div class="execution-details">
            <p class="task-description">{{ execution.taskDescription }}</p>
            <div class="meta-info">
              <span class="duration">Duration: {{ execution.duration }}</span>
              <span class="result">Result: {{ execution.result }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal" @click.stop>
        <div class="modal-header">
          <h3 class="modal-title">Execution Details</h3>
          <button class="modal-close" @click="closeModal">&times;</button>
        </div>
        <div class="modal-body">
          <div class="detail-item">
            <label class="detail-label">Agent:</label>
            <span class="detail-value">{{ selectedExecution?.agentName }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Type:</label>
            <span class="detail-value">{{ selectedExecution?.agentType }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Status:</label>
            <span class="detail-value" :class="getStatusClass(selectedExecution?.status)">{{ selectedExecution?.status }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Task:</label>
            <span class="detail-value">{{ selectedExecution?.taskDescription }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Duration:</label>
            <span class="detail-value">{{ selectedExecution?.duration }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Started:</label>
            <span class="detail-value">{{ formatFullTimestamp(selectedExecution?.timestamp) }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Result:</label>
            <span class="detail-value">{{ selectedExecution?.result }}</span>
          </div>
          <div class="detail-item">
            <label class="detail-label">Output:</label>
            <div class="detail-value detail-output">
              <pre>{{ selectedExecution?.output || 'No output available' }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

// Define Execution type
interface Execution {
  id: string
  agentId: string
  agentName: string
  agentType: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  timestamp: Date | string
  duration: string
  taskDescription: string
  result: string
  output?: string
  projectId: string
}

// Props
const props = defineProps<{
  executions: Execution[]
  projectId: string
}>()

// State
const selectedAgentType = ref('')
const showModal = ref(false)
const selectedExecution = ref<Execution | null>(null)

// Computed properties
const filteredExecutions = computed(() => {
  if (!selectedAgentType.value) return props.executions
  
  return props.executions.filter(execution => 
    execution.agentType.toLowerCase() === selectedAgentType.value.toLowerCase()
  )
})

// Methods
const getStatusClass = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'badge-info',
    running: 'badge-warning',
    completed: 'badge-success',
    failed: 'badge-error',
    cancelled: 'badge-error'
  }
  return statusMap[status] || 'badge-info'
}

const getStatusIcon = (status: string) => {
  const iconMap: Record<string, string> = {
    pending: '●',
    running: '⚡',
    completed: '✓',
    failed: '✕',
    cancelled: '⚠'
  }
  return iconMap[status] || '●'
}

const formatTimestamp = (timestamp: Date | string) => {
  if (!timestamp) return ''
  
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: true 
  })
}

const formatFullTimestamp = (timestamp: Date | string) => {
  if (!timestamp) return ''
  
  const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp
  return date.toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: '2-digit', 
    minute: '2-digit',
    second: '2-digit',
    hour12: true 
  })
}

const openModal = (execution: Execution) => {
  selectedExecution.value = execution
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  selectedExecution.value = null
}
</script>

<style scoped>
.agent-history {
  font-family: var(--font-family);
  padding: var(--space-6);
  max-width: 800px;
  margin: 0 auto;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-8);
}

.title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.controls {
  display: flex;
  gap: var(--space-3);
}

.agent-filter {
  padding: var(--space-2) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  background: var(--color-surface);
  color: var(--color-text-primary);
  min-width: 150px;
}

.agent-filter:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.2);
}

.timeline {
  position: relative;
  padding-left: var(--space-6);
}

.timeline::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2px;
  background: var(--color-border);
  border-radius: var(--radius-full);
}

.timeline-item {
  position: relative;
  padding-bottom: var(--space-6);
  cursor: pointer;
  transition: transform var(--transition-base);
}

.timeline-item:hover {
  transform: translateX(4px);
}

.timeline-item--active::before {
  background: var(--color-success);
}

.timeline-content {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-5);
  box-shadow: var(--shadow-card);
  transition: all var(--transition-base);
}

.timeline-item:hover .timeline-content {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-icon {
  font-size: var(--font-size-lg);
}

.status-text {
  text-transform: capitalize;
}

.timestamp {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-medium);
}

.agent-info {
  margin-bottom: var(--space-4);
}

.agent-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.agent-type {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.execution-details {
  color: var(--color-text-secondary);
}

.task-description {
  font-size: var(--font-size-base);
  margin-bottom: var(--space-3);
  line-height: var(--line-height-normal);
}

.meta-info {
  display: flex;
  gap: var(--space-4);
  font-size: var(--font-size-xs);
}

.duration, .result {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: var(--shadow-xl);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.modal-close {
  background: none;
  border: none;
  font-size: var(--font-size-2xl);
  color: var(--color-text-tertiary);
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background var(--transition-fast);
}

.modal-close:hover {
  background: var(--color-border-light);
}

.modal-body {
  color: var(--color-text-secondary);
}

.detail-item {
  margin-bottom: var(--space-4);
  display: flex;
  flex-direction: column;
}

.detail-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-1);
}

.detail-value {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.detail-output {
  background: var(--color-background);
  padding: var(--space-3);
  border-radius: var(--radius-md);
  font-family: monospace;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
}

/* Status badge colors */
.badge-info {
  background: rgba(90, 200, 250, 0.12);
  color: var(--color-info);
}

.badge-warning {
  background: rgba(255, 149, 0, 0.12);
  color: var(--color-warning);
}

.badge-success {
  background: rgba(52, 199, 89, 0.12);
  color: var(--color-success);
}

.badge-error {
  background: rgba(255, 59, 48, 0.12);
  color: var(--color-error);
}
</style>