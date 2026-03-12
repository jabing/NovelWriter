<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAgentStore } from '@/stores/agentStore'

const { t } = useI18n()
const agentStore = useAgentStore()

const agents = computed(() => agentStore.agents)
const activeAgents = computed(() => agentStore.activeAgents)

onMounted(() => {
  agentStore.fetchAgents()
})

function getStatusClass(status: string): string {
  return status === 'active' ? 'badge-success' : 'badge-warning'
}
</script>

<template>
  <div class="agents-page">
    <header class="page-header">
      <h1>{{ t('agents.page.title') }}</h1>
      <p>{{ t('agents.page.subtitle') }}</p>
    </header>

    <div class="agents-stats">
      <div class="stat-card card">
        <h3>{{ t('agents.stats.activeAgents') }}</h3>
        <p class="stat-value">{{ activeAgents.length }}</p>
      </div>
      <div class="stat-card card">
        <h3>{{ t('agents.stats.totalAgents') }}</h3>
        <p class="stat-value">{{ agents.length }}</p>
      </div>
    </div>

    <div class="agents-list">
      <div v-for="agent in agents" :key="agent.id" class="agent-item card">
        <div class="agent-header">
          <h3 class="agent-name">{{ agent.name }}</h3>
          <span :class="['badge', getStatusClass(agent.status)]">
            {{ agent.status }}
          </span>
        </div>
        <p class="agent-id">{{ t('agents.list.id', { id: agent.id }) }}</p>
        <p v-if="agent.last_seen" class="agent-meta">
          {{ t('agents.list.lastSeen', { time: agent.last_seen }) }}
        </p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agents-page {
  padding: var(--space-6);
  animation: fadeIn var(--transition-slow);
}

.page-header {
  margin-bottom: var(--space-8);
  animation: fadeInUp var(--transition-slow) backwards;
  animation-delay: 0.05s;
}

.page-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.page-header p {
  color: var(--color-text-secondary);
}

.agents-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.stat-card {
  text-align: center;
  transition: all var(--transition-fast);
  will-change: transform, box-shadow;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.stat-card:nth-child(1) {
  animation: fadeInUp var(--transition-slow) backwards;
  animation-delay: 0.1s;
}

.stat-card:nth-child(2) {
  animation: fadeInUp var(--transition-slow) backwards;
  animation-delay: 0.15s;
}

.stat-card h3 {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
}

.stat-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
}

.agents-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
  animation: fadeInUp var(--transition-slow) backwards;
  animation-delay: 0.2s;
}

.agent-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  transition: all var(--transition-fast);
  will-change: transform, box-shadow;
  cursor: pointer;
}

.agent-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-focus);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.agent-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.agent-id {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  font-family: var(--font-family);
}

.agent-meta {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { 
    opacity: 0; 
    transform: translateY(12px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

@media (prefers-reduced-motion: reduce) {
  .agents-page,
  .page-header,
  .stat-card,
  .agents-list {
    animation: none;
  }
  
  .stat-card:hover,
  .agent-item:hover {
    transform: none;
  }
}
</style>
