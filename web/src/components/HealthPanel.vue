<template>
  <div class="health-panel card">
    <div class="health-panel__header">
      <h2 class="health-panel__title">Health Status</h2>
      <button 
        class="health-panel__refresh-btn btn btn-secondary"
        @click="handleRefresh"
        :disabled="isLoading"
      >
        <span v-if="isLoading" class="spinner"></span>
        <span v-else>Refresh</span>
      </button>
    </div>
    
    <div class="health-panel__timestamp">
      Last checked: {{ lastChecked }}
    </div>
    
    <div class="health-panel__checks">
      <div 
        v-for="check in healthChecks" 
        :key="check.name"
        class="health-check-item"
        :class="{
          'health-check-item--success': check.status === 'online',
          'health-check-item--warning': check.status === 'busy',
          'health-check-item--error': check.status === 'offline' || check.status === 'error'
        }"
      >
        <div class="health-check-item__status-indicator">
          <div class="status-dot"></div>
        </div>
        <div class="health-check-item__content">
          <div class="health-check-item__name">{{ check.name }}</div>
          <div class="health-check-item__status">{{ getStatusText(check.status) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

interface HealthCheck {
  name: string;
  status: string;
  lastSeen?: string;
}

interface Props {
  healthChecks: HealthCheck[];
  lastChecked: string;
  onRefresh: () => void;
}

const props = defineProps<Props>();
const isLoading = ref(false);

const getStatusText = (status: string): string => {
  switch (status) {
    case 'online':
      return 'Online';
    case 'busy':
      return 'Busy';
    case 'offline':
      return 'Offline';
    case 'error':
      return 'Error';
    default:
      return status;
  }
};

const handleRefresh = async () => {
  isLoading.value = true;
  try {
    await props.onRefresh();
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.health-panel {
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.health-panel__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.health-panel__title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.health-panel__refresh-btn {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
}

.health-panel__timestamp {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-5);
}

.health-panel__checks {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.health-check-item {
  display: flex;
  align-items: center;
  padding: var(--space-3);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
}

.health-check-item:hover {
  transform: translateX(var(--space-1));
  border-color: var(--color-border);
}

.health-check-item--success {
  border-left: 4px solid var(--color-success);
}

.health-check-item--warning {
  border-left: 4px solid var(--color-warning);
}

.health-check-item--error {
  border-left: 4px solid var(--color-error);
}

.health-check-item__status-indicator {
  margin-right: var(--space-4);
  flex-shrink: 0;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--color-border);
}

.health-check-item--success .status-dot {
  background: var(--color-success);
}

.health-check-item--warning .status-dot {
  background: var(--color-warning);
}

.health-check-item--error .status-dot {
  background: var(--color-error);
}

.health-check-item__content {
  flex: 1;
}

.health-check-item__name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.health-check-item__status {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>