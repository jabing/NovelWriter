<template>
  <div class="alert-list">
    <!-- Filter Controls -->
    <div class="alert-filter-controls">
      <div class="filter-group">
        <label class="filter-label" for="severity-filter">
          {{ $t('alerts.filterBySeverity') }}
        </label>
        <select 
          id="severity-filter" 
          v-model="selectedSeverity"
          class="filter-select"
          @change="onSeverityFilterChange"
        >
          <option value="all">{{ $t('alerts.allSeverities') }}</option>
          <option value="info">{{ $t('alerts.info') }}</option>
          <option value="warning">{{ $t('alerts.warning') }}</option>
          <option value="error">{{ $t('alerts.error') }}</option>
          <option value="critical">{{ $t('alerts.critical') }}</option>
        </select>
      </div>
    </div>

    <!-- Alert List -->
    <div class="alert-container">
      <div 
        v-for="alert in filteredAlerts" 
        :key="alert.id"
        class="alert-card"
        :class="`severity-${alert.severity}`"
      >
        <div class="alert-header">
          <div class="alert-icon">
            <span class="badge" :class="`badge-${alert.severity}`">
              {{ getSeverityIcon(alert.severity) }}
            </span>
          </div>
          <div class="alert-title">
            <h3 class="alert-title-text">{{ alert.title }}</h3>
            <p class="alert-subtitle">{{ formatDate(alert.timestamp) }}</p>
          </div>
        </div>
        
        <div class="alert-content">
          <p class="alert-message">{{ alert.message }}</p>
          <div class="alert-details" v-if="alert.details">
            <span class="detail-label">{{ $t('alerts.details') }}:</span>
            <span class="detail-value">{{ alert.details }}</span>
          </div>
        </div>
        
        <div class="alert-actions">
          <button 
            class="btn btn-secondary acknowledge-btn"
            @click="acknowledgeAlert(alert.id)"
          >
            {{ $t('alerts.acknowledge') }}
          </button>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-if="filteredAlerts.length === 0" class="empty-state">
        <div class="empty-state-icon">ℹ️</div>
        <h3 class="empty-state-title">{{ $t('alerts.noAlerts') }}</h3>
        <p class="empty-state-description">{{ $t('alerts.noAlertsDescription') }}</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

interface Alert {
  id: string
  title: string
  message: string
  severity: 'info' | 'warning' | 'error' | 'critical'
  timestamp: string
  details?: string
  acknowledged?: boolean
}

export default defineComponent({
  name: 'AlertList',
  
  props: {
    alerts: {
      type: Array as () => Alert[],
      required: true
    }
  },
  
  setup(props, { emit }) {
    const { t } = useI18n()
    
    const selectedSeverity = ref('all')
    
    const formatDate = (timestamp: string) => {
      const date = new Date(timestamp)
      return new Intl.DateTimeFormat('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      }).format(date)
    }
    
    const filteredAlerts = computed(() => {
      if (selectedSeverity.value === 'all') {
        return props.alerts
      }
      return props.alerts.filter(alert => alert.severity === selectedSeverity.value)
    })
    
    const getSeverityIcon = (severity: string) => {
      const icons: Record<string, string> = {
        info: 'ℹ️',
        warning: '⚠️',
        error: '❌',
        critical: '🚨'
      }
      return icons[severity] || 'ℹ️'
    }
    
    const onSeverityFilterChange = () => {
      // Filter change handled by computed property
    }
    
    const acknowledgeAlert = (alertId: string) => {
      // Acknowledge action - emit event for parent to handle
      emit('acknowledge', alertId)
    }
    
    return {
      t,
      selectedSeverity,
      filteredAlerts,
      formatDate,
      getSeverityIcon,
      onSeverityFilterChange,
      acknowledgeAlert
    }
  }
})
</script>

<style scoped>
.alert-list {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  padding: var(--space-6);
}

.alert-filter-controls {
  margin-bottom: var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.filter-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.filter-select {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-2) var(--space-3);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  min-width: 180px;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.2);
}

.alert-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.alert-card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-5);
  transition: all var(--transition-base);
  border-left: 4px solid transparent;
}

.alert-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-card-hover);
}

.alert-card.severity-info {
  border-left-color: var(--color-info);
}

.alert-card.severity-warning {
  border-left-color: var(--color-warning);
}

.alert-card.severity-error {
  border-left-color: var(--color-error);
}

.alert-card.severity-critical {
  border-left-color: var(--color-error);
  background: rgba(255, 59, 48, 0.05);
}

.alert-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.alert-icon {
  flex-shrink: 0;
}

.alert-title {
  flex: 1;
}

.alert-title-text {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-1);
  color: var(--color-text-primary);
}

.alert-subtitle {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-normal);
}

.alert-content {
  margin-bottom: var(--space-4);
}

.alert-message {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  margin-bottom: var(--space-2);
}

.alert-details {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.detail-label {
  font-weight: var(--font-weight-medium);
}

.detail-value {
  color: var(--color-text-secondary);
}

.alert-actions {
  display: flex;
  justify-content: flex-end;
}

.acknowledge-btn {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
}

/* Badge styles */
.badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
}

.badge-info {
  background: rgba(90, 200, 250, 0.12);
  color: var(--color-info);
}

.badge-warning {
  background: rgba(255, 149, 0, 0.12);
  color: var(--color-warning);
}

.badge-error {
  background: rgba(255, 59, 48, 0.12);
  color: var(--color-error);
}

.badge-critical {
  background: rgba(255, 59, 48, 0.2);
  color: var(--color-error);
  font-weight: var(--font-weight-bold);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-8);
  text-align: center;
}

.empty-state-icon {
  font-size: var(--font-size-4xl);
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-state-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-state-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 320px;
}

/* Responsive */
@media (max-width: 768px) {
  .alert-list {
    padding: var(--space-4);
  }
  
  .filter-group {
    flex-direction: column;
    align-items: flex-start;
    width: 100%;
  }
  
  .filter-select {
    width: 100%;
  }
}
</style>