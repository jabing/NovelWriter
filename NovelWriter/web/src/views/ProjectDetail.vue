<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectStore } from '@/stores/projectStore';
import { useI18n } from 'vue-i18n';
import {
  Document,
  User,
  Setting,
  Edit,
  Plus,
  Download,
  Delete,
  ArrowLeft
} from '@element-plus/icons-vue';
import type { Project } from '@/types';

const route = useRoute();
const router = useRouter();
const projectStore = useProjectStore();
const { t } = useI18n();

// Tab state
const activeTab = ref<'overview' | 'chapters' | 'characters' | 'settings'>('overview');
const tabs = computed(() => [
  { key: 'overview', label: t('projectDetail.tabs.overview'), icon: Document },
  { key: 'chapters', label: t('projectDetail.tabs.chapters'), icon: Document },
  { key: 'characters', label: t('projectDetail.tabs.characters'), icon: User },
  { key: 'settings', label: t('projectDetail.tabs.settings'), icon: Setting }
] as const);

// Quick actions
const quickActions = computed(() => [
  { key: 'edit', icon: Edit, label: t('projectDetail.actions.edit') },
  { key: 'add-chapter', icon: Plus, label: t('projectDetail.actions.addChapter') },
  { key: 'export', icon: Download, label: t('projectDetail.actions.export') },
  { key: 'delete', icon: Delete, label: t('common.delete') }
] as const);

// Loading state
const isLoading = ref(true);

// Get project ID from route
const projectId = computed(() => route.params.id as string);

// Get project from store
const project = computed<Project | undefined>(() => {
  return projectStore.projects.find(p => p.id === projectId.value);
});

// Progress calculation for SVG ring
const progressOffset = computed(() => {
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const progress = project.value?.progress_percent ?? 0;
  return circumference - (progress / 100) * circumference;
});

// Format number with locale
function formatNumber(num: number): string {
  return num.toLocaleString();
}

// Handle quick action click
function handleAction(action: string) {
  switch (action) {
    case 'edit':
      // Navigate to edit (future implementation)
      break;
    case 'add-chapter':
      // Open add chapter modal (future implementation)
      break;
    case 'export':
      // Export project (future implementation)
      break;
    case 'delete':
      // Delete project (future implementation)
      break;
  }
}

// Go back to projects list
function goBack() {
  router.push('/projects');
}

// Fetch project data on mount
onMounted(async () => {
  if (projectStore.projects.length === 0) {
    await projectStore.fetchProjects();
  }
  isLoading.value = false;
});
</script>

<template>
  <div class="project-detail">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="skeleton skeleton-header"></div>
      <div class="skeleton skeleton-content"></div>
    </div>

    <!-- Not Found State -->
    <div v-else-if="!project" class="not-found">
      <div class="not-found-icon">
        <el-icon :size="64"><Document /></el-icon>
      </div>
      <h2 class="not-found-title">{{ t('projectDetail.notFound.title') }}</h2>
      <p class="not-found-description">
        {{ t('projectDetail.notFound.description') }}
      </p>
      <button class="btn btn-primary" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ t('projectDetail.notFound.backButton') }}
      </button>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Header -->
      <header class="detail-header">
        <button class="back-button" @click="goBack" :aria-label="t('projectDetail.aria.goBack')">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <div class="header-content">
          <div class="header-info">
            <h1 class="project-title">{{ project.title }}</h1>
            <p class="project-genre">{{ project.genre }}</p>
          </div>
          <div class="progress-ring-container">
            <svg class="progress-ring" viewBox="0 0 100 100">
              <!-- Background circle -->
              <circle
                class="progress-ring-bg"
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke-width="8"
              />
              <!-- Progress circle -->
              <circle
                class="progress-ring-fill"
                cx="50"
                cy="50"
                r="45"
                fill="none"
                stroke-width="8"
                :stroke-dashoffset="progressOffset"
              />
            </svg>
            <div class="progress-text">
              <span class="progress-value">{{ project.progress_percent }}</span>
              <span class="progress-unit">{{ t('projectDetail.progress.unit') }}</span>
            </div>
          </div>
        </div>
      </header>

      <!-- Tabs (Apple Segmented Control Style) -->
      <nav class="tabs-container" role="tablist">
        <div class="tabs-segmented">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab-button', { active: activeTab === tab.key }]"
            :aria-selected="activeTab === tab.key"
            role="tab"
            @click="activeTab = tab.key"
          >
            <el-icon class="tab-icon">
              <component :is="tab.icon" />
            </el-icon>
            <span class="tab-label">{{ tab.label }}</span>
          </button>
        </div>
      </nav>

      <!-- Content Area -->
      <main class="content-area">
        <Transition name="fade" mode="out-in">
          <!-- Overview Tab -->
          <section
            v-if="activeTab === 'overview'"
            key="overview"
            class="tab-content"
            role="tabpanel"
          >
            <div class="overview-grid">
              <div class="card stat-card">
                <h3 class="stat-title">{{ t('projectDetail.overview.premise') }}</h3>
                <p class="stat-text">{{ project.premise }}</p>
              </div>
              
              <div class="card stat-card">
                <h3 class="stat-title">{{ t('projectDetail.overview.statistics') }}</h3>
                <div class="stats-grid">
                  <div class="stat-item">
                    <span class="stat-value">{{ project.completed_chapters }}/{{ project.target_chapters }}</span>
                    <span class="stat-label">{{ t('projectDetail.overview.chapters') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ formatNumber(project.total_words) }}</span>
                    <span class="stat-label">{{ t('projectDetail.overview.words') }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ formatNumber(project.target_words) }}</span>
                    <span class="stat-label">{{ t('projectDetail.overview.target') }}</span>
                  </div>
                </div>
              </div>

              <div class="card stat-card">
                <h3 class="stat-title">{{ t('projectDetail.overview.themes') }}</h3>
                <div class="tags-container">
                  <span
                    v-for="theme in project.themes"
                    :key="theme"
                    class="theme-tag"
                  >
                    {{ theme }}
                  </span>
                </div>
              </div>

              <div class="card stat-card">
                <h3 class="stat-title">{{ t('projectDetail.overview.details') }}</h3>
                <dl class="details-list">
                  <div class="detail-row">
                    <dt>{{ t('projectDetail.overview.pov') }}</dt>
                    <dd>{{ project.pov }}</dd>
                  </div>
                  <div class="detail-row">
                    <dt>{{ t('projectDetail.overview.tone') }}</dt>
                    <dd>{{ project.tone }}</dd>
                  </div>
                  <div class="detail-row">
                    <dt>{{ t('projectDetail.overview.audience') }}</dt>
                    <dd>{{ project.target_audience }}</dd>
                  </div>
                  <div class="detail-row">
                    <dt>{{ t('projectDetail.overview.structure') }}</dt>
                    <dd>{{ project.story_structure }}</dd>
                  </div>
                </dl>
              </div>
            </div>
          </section>

          <!-- Chapters Tab -->
          <section
            v-else-if="activeTab === 'chapters'"
            key="chapters"
            class="tab-content"
            role="tabpanel"
          >
            <div class="empty-content">
              <el-icon :size="48"><Document /></el-icon>
              <h3>{{ t('projectDetail.tabs.chapters') }}</h3>
              <p>{{ t('projectDetail.empty.chapters') }}</p>
              <p class="content-hint">{{ t('projectDetail.empty.chaptersHint', { completed: project.completed_chapters, total: project.target_chapters }) }}</p>
            </div>
          </section>

          <!-- Characters Tab -->
          <section
            v-else-if="activeTab === 'characters'"
            key="characters"
            class="tab-content"
            role="tabpanel"
          >
            <div class="empty-content">
              <el-icon :size="48"><User /></el-icon>
              <h3>{{ t('projectDetail.tabs.characters') }}</h3>
              <p>{{ t('projectDetail.empty.characters') }}</p>
            </div>
          </section>

          <!-- Settings Tab -->
          <section
            v-else-if="activeTab === 'settings'"
            key="settings"
            class="tab-content"
            role="tabpanel"
          >
            <div class="empty-content">
              <el-icon :size="48"><Setting /></el-icon>
              <h3>{{ t('projectDetail.settings.title') }}</h3>
              <p>{{ t('projectDetail.empty.settings') }}</p>
            </div>
          </section>
        </Transition>
      </main>

      <!-- Floating Action Buttons -->
      <div class="quick-actions">
        <button
          v-for="action in quickActions"
          :key="action.key"
          class="action-button"
          :aria-label="action.label"
          :title="action.label"
          @click="handleAction(action.key)"
        >
          <el-icon><component :is="action.icon" /></el-icon>
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.project-detail {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-border-light) 25%,
    var(--color-border) 50%,
    var(--color-border-light) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
  border-radius: var(--radius-md);
}

.skeleton-header {
  height: 80px;
}

.skeleton-content {
  height: 400px;
}

@keyframes skeleton-loading {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Not Found State */
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
}

.not-found-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-6);
}

.not-found-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.not-found-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 320px;
  margin-bottom: var(--space-6);
}

/* Header */
.detail-header {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.back-button:hover {
  background: var(--color-border-light);
  color: var(--color-text-primary);
}

.header-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-6);
}

.header-info {
  flex: 1;
  min-width: 0;
}

.project-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  margin-bottom: var(--space-1);
}

.project-genre {
  font-size: var(--font-size-base);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
}

/* Progress Ring */
.progress-ring-container {
  position: relative;
  width: 100px;
  height: 100px;
  flex-shrink: 0;
}

.progress-ring {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}

.progress-ring-bg {
  stroke: var(--color-border-light);
}

.progress-ring-fill {
  stroke: var(--color-primary);
  stroke-linecap: round;
  stroke-dasharray: 283;
  transition: stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  align-items: baseline;
  gap: 1px;
}

.progress-value {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
}

.progress-unit {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Tabs (Segmented Control) */
.tabs-container {
  margin-bottom: var(--space-6);
}

.tabs-segmented {
  display: inline-flex;
  background: var(--color-border-light);
  padding: 4px;
  border-radius: var(--radius-lg);
}

.tab-button {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-base);
}

.tab-button:hover {
  color: var(--color-text-primary);
}

.tab-button.active {
  background: var(--color-primary);
  color: white;
  box-shadow: var(--shadow-sm);
}

.tab-icon {
  font-size: 16px;
}

.tab-label {
  display: inline;
}

/* Content Area */
.content-area {
  padding: var(--space-6);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  min-height: 400px;
}

/* Fade Transition */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Overview Grid */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-6);
}

@media (max-width: 768px) {
  .overview-grid {
    grid-template-columns: 1fr;
  }
}

.stat-card {
  padding: var(--space-5);
}

.stat-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.stat-text {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-4);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Tags */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.theme-tag {
  display: inline-flex;
  padding: var(--space-1) var(--space-3);
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
}

/* Details List */
.details-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
}

.detail-row dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.detail-row dd {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

/* Empty Content */
.empty-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16);
  text-align: center;
  color: var(--color-text-tertiary);
}

.empty-content h3 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-top: var(--space-4);
  margin-bottom: var(--space-2);
}

.empty-content p {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.content-hint {
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--color-border-light);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Quick Actions (Floating) */
.quick-actions {
  position: fixed;
  right: var(--space-6);
  bottom: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  z-index: var(--z-sticky);
}

.action-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-full);
  cursor: pointer;
  box-shadow: var(--shadow-lg);
  color: var(--color-text-secondary);
  transition: all var(--transition-base);
}

.action-button:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
  transform: scale(1.05);
}

.action-button:first-child {
  background: var(--gradient-primary);
  border: none;
  color: white;
}

.action-button:first-child:hover {
  opacity: 0.9;
}

/* Responsive */
@media (max-width: 768px) {
  .project-detail {
    padding: var(--space-4);
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .progress-ring-container {
    align-self: flex-end;
  }

  .tab-label {
    display: none;
  }

  .tab-button {
    padding: var(--space-2) var(--space-3);
  }

  .quick-actions {
    right: var(--space-4);
    bottom: var(--space-4);
  }

  .action-button {
    width: 44px;
    height: 44px;
  }
}
</style>
