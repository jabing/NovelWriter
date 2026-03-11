<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const platforms = ref<Array<{
  id: string
  name: string
  status: string
  publishedChapters: number
  totalReads: number
}>>([])

onMounted(() => {
  // Placeholder data
  platforms.value = [
    { id: '1', name: 'Wattpad', status: 'connected', publishedChapters: 12, totalReads: 1543 },
    { id: '2', name: 'Royal Road', status: 'connected', publishedChapters: 8, totalReads: 892 },
    { id: '3', name: 'AO3', status: 'disconnected', publishedChapters: 0, totalReads: 0 }
  ]
})

function getStatusClass(status: string): string {
  return status === 'connected' ? 'badge-success' : 'badge-warning'
}
</script>

<template>
  <div class="publish-page" data-testid="publish-page">
    <header class="page-header">
      <h1 data-testid="publish-page-title">{{ t('publish.title') }}</h1>
      <p>{{ t('publish.subtitle') }}</p>
    </header>

    <div class="platforms-list">
      <div v-for="platform in platforms" :key="platform.id" class="platform-item card" data-testid="platform-item">
        <div class="platform-header">
          <h3 class="platform-name" data-testid="platform-name">{{ platform.name }}</h3>
          <span :class="['badge', getStatusClass(platform.status)]" data-testid="platform-status-badge">
            {{ platform.status === 'connected' ? t('status.connected') : t('status.disconnected') }}
          </span>
        </div>
        <div class="platform-stats">
          <div class="stat">
            <span class="stat-value" data-testid="platform-chapters-count">{{ platform.publishedChapters }}</span>
            <span class="stat-label">{{ t('publish.chapters') }}</span>
          </div>
          <div class="stat">
            <span class="stat-value" data-testid="platform-reads-count">{{ platform.totalReads.toLocaleString() }}</span>
            <span class="stat-label">{{ t('publish.reads') }}</span>
          </div>
        </div>
        <button class="btn btn-secondary" data-testid="platform-connect-button">
          {{ platform.status === 'connected' ? t('publish.manage') : t('publish.connect') }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.publish-page {
  padding: var(--space-6);
}

.page-header {
  margin-bottom: var(--space-8);
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

.platforms-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.platform-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.platform-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.platform-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.platform-stats {
  display: flex;
  gap: var(--space-6);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}
</style>
