<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useProjectStore } from '../stores/projectStore';
import { useAgentStore } from '../stores/agentStore';
import { 
  FolderOpened, 
  Document, 
  TrendCharts, 
  Plus,
  Clock,
  CircleCheck,
  Warning,
  Loading
} from '@element-plus/icons-vue';
import type { Project } from '../types';

const router = useRouter();
const { t } = useI18n();
const projectStore = useProjectStore();
const agentStore = useAgentStore();

// Local state for activity feed
const activities = ref<Array<{
  id: string;
  type: 'created' | 'updated' | 'completed' | 'warning';
  title: string;
  description: string;
  timestamp: Date;
}>>([]);

// System health state
const systemHealth = ref<{
  status: 'healthy' | 'warning' | 'error';
  agents: { online: number; total: number };
  lastBackup: string;
  storage: { used: number; total: number };
}>({
  status: 'healthy',
  agents: { online: 0, total: 0 },
  lastBackup: '2 hours ago',
  storage: { used: 45, total: 100 }
});

// Computed properties
const isLoading = computed(() => projectStore.isLoading);
const projects = computed(() => projectStore.projectList);
const hasProjects = computed(() => projects.value.length > 0);

// Generate activity feed from projects
function generateActivities(projectList: Project[]) {
  const activityList: typeof activities.value = [];
  
  projectList.slice(0, 5).forEach((project, index) => {
    activityList.push({
      id: `activity-${index}`,
      type: project.status === 'completed' ? 'completed' : 
            project.status === 'in_progress' ? 'updated' : 'created',
      title: project.title,
      description: t('dashboard.activityDescription', {
        completed: project.completed_chapters,
        total: project.target_chapters,
        words: project.total_words.toLocaleString()
      }),
      timestamp: new Date(project.updated_at)
    });
  });
  
  return activityList;
}

// Format relative time
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);
  
  if (days > 0) return t('common.daysAgo', { n: days });
  if (hours > 0) return t('common.hoursAgo', { n: hours });
  if (minutes > 0) return t('common.minutesAgo', { n: minutes });
  return t('common.justNow');
}

// Get activity icon
function getActivityIcon(type: string) {
  switch (type) {
    case 'completed': return CircleCheck;
    case 'warning': return Warning;
    case 'updated': return TrendCharts;
    default: return Document;
  }
}

// Get status badge class
function getStatusBadgeClass(status: string) {
  switch (status) {
    case 'completed': return 'badge-success';
    case 'in_progress': return 'badge-info';
    case 'error': return 'badge-error';
    default: return 'badge-warning';
  }
}

// Get health status class
function getHealthStatusClass(status: string) {
  switch (status) {
    case 'healthy': return 'badge-success';
    case 'warning': return 'badge-warning';
    case 'error': return 'badge-error';
    default: return 'badge-info';
  }
}

// Navigate to project
function openProject(projectId: string) {
  router.push(`/projects/${projectId}`);
}

// Create new project
function createNewProject() {
  router.push('/projects/new');
}

// Initialize data
onMounted(async () => {
  await projectStore.fetchProjects();
  agentStore.fetchAgents();
  
  // Generate activity feed
  activities.value = generateActivities(projects.value);
  
  // Update system health
  const activeAgents = agentStore.activeAgents;
  systemHealth.value = {
    status: activeAgents.length > 0 ? 'healthy' : 'warning',
    agents: { 
      online: activeAgents.length, 
      total: agentStore.agents.length 
    },
    lastBackup: '2 hours ago',
    storage: { used: 45, total: 100 }
  };
});
</script>

<template>
  <div class="dashboard">
    <!-- Header Section -->
    <header class="dashboard-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="header-title">{{ t('nav.dashboard') }}</h1>
          <p class="header-subtitle">{{ t('dashboard.welcomeSubtitle') }}</p>
        </div>
        <button class="btn btn-primary" @click="createNewProject">
          <el-icon><Plus /></el-icon>
          {{ t('dashboard.newProject') }}
        </button>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="grid-3">
        <div v-for="i in 3" :key="`skeleton-${i}`" class="card skeleton-card">
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-text"></div>
          <div class="skeleton skeleton-text skeleton-text-short"></div>
          <div class="skeleton-footer">
            <div class="skeleton skeleton-badge"></div>
            <div class="skeleton skeleton-progress"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="!hasProjects" class="empty-state">
      <div class="empty-state-icon">
        <el-icon :size="64"><FolderOpened /></el-icon>
      </div>
      <h3 class="empty-state-title">{{ t('dashboard.noProjects') }}</h3>
      <p class="empty-state-description">
        {{ t('dashboard.noProjectsDesc') }}
      </p>
      <button class="btn btn-primary empty-state-action" @click="createNewProject">
        <el-icon><Plus /></el-icon>
        {{ t('dashboard.createFirstProject') }}
      </button>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Projects Section -->
      <section class="section">
        <div class="section-header">
          <h2 class="section-title">{{ t('project.projects') }}</h2>
          <span class="section-count">{{ t('dashboard.total', { count: projects.length }) }}</span>
        </div>
        
        <div class="grid-3">
          <article 
            v-for="project in projects" 
            :key="project.id"
            class="card project-card"
            @click="openProject(project.id)"
            tabindex="0"
            @keypress.enter="openProject(project.id)"
          >
            <div class="project-header">
              <h3 class="project-title">{{ project.title }}</h3>
              <span :class="['badge', getStatusBadgeClass(project.status)]">
                {{ t(`project.${project.status}`) }}
              </span>
            </div>
            
            <p class="project-genre">{{ project.genre }}</p>
            <p class="project-premise">{{ project.premise }}</p>
            
            <div class="project-stats">
              <div class="stat">
                <span class="stat-value">{{ project.completed_chapters }}/{{ project.target_chapters }}</span>
                <span class="stat-label">{{ t('project.chapters') }}</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ (project.total_words / 1000).toFixed(1) }}k</span>
                <span class="stat-label">{{ t('project.words') }}</span>
              </div>
              <div class="stat">
                <span class="stat-value">{{ project.progress_percent }}%</span>
                <span class="stat-label">{{ t('dashboard.complete') }}</span>
              </div>
            </div>
            
            <div class="progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${project.progress_percent}%` }"
              ></div>
            </div>
          </article>
        </div>
      </section>

      <!-- Bottom Grid: Activity & System Health -->
      <div class="bottom-grid">
        <!-- Activity Feed -->
        <section class="section activity-section">
          <div class="section-header">
            <h2 class="section-title">{{ t('dashboard.recentActivity') }}</h2>
          </div>
          
          <div v-if="activities.length === 0" class="empty-activity">
            <el-icon><Clock /></el-icon>
            <span>{{ t('dashboard.noRecentActivity') }}</span>
          </div>
          
          <div v-else class="timeline">
            <div 
              v-for="activity in activities" 
              :key="activity.id"
              class="timeline-item"
            >
              <div class="activity-content">
                <div class="activity-header">
                  <el-icon class="activity-icon">
                    <component :is="getActivityIcon(activity.type)" />
                  </el-icon>
                  <span class="activity-title">{{ activity.title }}</span>
                </div>
                <p class="activity-description">{{ activity.description }}</p>
                <span class="activity-time">{{ formatRelativeTime(activity.timestamp) }}</span>
              </div>
            </div>
          </div>
        </section>

        <!-- System Health -->
        <section class="section health-section">
          <div class="section-header">
            <h2 class="section-title">{{ t('dashboard.systemHealth') }}</h2>
          </div>
          
          <div class="health-grid">
            <div class="health-item">
              <div class="health-icon">
                <el-icon><CircleCheck /></el-icon>
              </div>
              <div class="health-details">
                <span class="health-label">{{ t('dashboard.overallStatus') }}</span>
                <span :class="['badge', getHealthStatusClass(systemHealth.status)]">
                  {{ t(`status.${systemHealth.status}`) }}
                </span>
              </div>
            </div>
            
            <div class="health-item">
              <div class="health-icon">
                <el-icon><Loading /></el-icon>
              </div>
              <div class="health-details">
                <span class="health-label">{{ t('dashboard.activeAgents') }}</span>
                <span class="health-value">
                  {{ systemHealth.agents.online }}/{{ systemHealth.agents.total }}
                </span>
              </div>
            </div>
            
            <div class="health-item">
              <div class="health-icon">
                <el-icon><Clock /></el-icon>
              </div>
              <div class="health-details">
                <span class="health-label">{{ t('dashboard.lastBackup') }}</span>
                <span class="health-value">{{ systemHealth.lastBackup }}</span>
              </div>
            </div>
            
            <div class="health-item">
              <div class="health-icon">
                <el-icon><TrendCharts /></el-icon>
              </div>
              <div class="health-details">
                <span class="health-label">{{ t('dashboard.storageUsed') }}</span>
                <div class="storage-bar">
                  <div 
                    class="storage-fill"
                    :style="{ width: `${systemHealth.storage.used}%` }"
                  ></div>
                </div>
                <span class="health-value">{{ systemHealth.storage.used }}%</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<style scoped>
.dashboard {
  min-height: 100%;
  padding: var(--space-8);
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.dashboard-header {
  margin-bottom: var(--space-10);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-6);
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

/* Project Cards */
.project-card {
  cursor: pointer;
  border: 1px solid transparent;
  transition: transform var(--transition-base), 
              box-shadow var(--transition-base),
              border-color var(--transition-base);
}

.project-card:hover,
.project-card:focus {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
  border-color: var(--color-border);
  outline: none;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.project-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-genre {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--space-2);
}

.project-premise {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: var(--space-4);
  min-height: 2.75rem;
}

.project-stats {
  display: flex;
  gap: var(--space-6);
  margin-bottom: var(--space-4);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.stat-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.progress-bar {
  height: 4px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

/* Loading Skeleton */
.loading-container {
  margin-bottom: var(--space-8);
}

.skeleton-card {
  pointer-events: none;
}

.skeleton-title {
  height: 24px;
  width: 70%;
  margin-bottom: var(--space-3);
}

.skeleton-text {
  height: 14px;
  width: 100%;
  margin-bottom: var(--space-2);
}

.skeleton-text-short {
  width: 60%;
}

.skeleton-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-4);
}

.skeleton-badge {
  height: 20px;
  width: 80px;
}

.skeleton-progress {
  height: 4px;
  width: 100px;
}

/* Empty State */
.empty-state {
  padding: var(--space-16) var(--space-8);
}

.empty-state-action {
  margin-top: var(--space-6);
}

/* Bottom Grid */
.bottom-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

/* Activity Section */
.activity-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.empty-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-tertiary);
}

.timeline-item {
  position: relative;
  padding-left: var(--space-6);
  padding-bottom: var(--space-5);
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: 5px;
  top: 6px;
  width: 10px;
  height: 10px;
  background: var(--color-primary);
  border-radius: 50%;
  border: 2px solid var(--color-surface);
  box-shadow: 0 0 0 2px var(--color-primary-light, rgba(0, 122, 255, 0.2));
}

.timeline-item::after {
  content: '';
  position: absolute;
  left: 9px;
  top: 20px;
  bottom: 0;
  width: 2px;
  background: var(--color-border);
}

.timeline-item:last-child::after {
  display: none;
}

.activity-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.activity-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.activity-icon {
  color: var(--color-primary);
  font-size: 14px;
}

.activity-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.activity-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.activity-time {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Health Section */
.health-section {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
}

.health-grid {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.health-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3);
  background: var(--color-background);
  border-radius: var(--radius-lg);
}

.health-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border-radius: var(--radius-md);
  color: var(--color-primary);
}

.health-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.health-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.health-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.storage-bar {
  height: 6px;
  background: var(--color-border);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--space-1);
}

.storage-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard {
    padding: var(--space-4);
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-title {
    font-size: var(--font-size-2xl);
  }
  
  .project-stats {
    gap: var(--space-4);
  }
}
</style>
