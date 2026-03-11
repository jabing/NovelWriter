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
/* ========================================
   Dashboard - Literary/Book Aesthetic
   Modern Editorial Style
   ======================================== */

.dashboard {
  min-height: 100%;
  padding: var(--space-8);
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn 0.6s ease-out;
}

/* ========================================
   Header Section - Editorial Header
   ======================================== */

.dashboard-header {
  margin-bottom: var(--space-12);
  position: relative;
  padding-bottom: var(--space-6);
  border-bottom: 2px solid var(--color-border-light);
}

.dashboard-header::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 120px;
  height: 2px;
  background: linear-gradient(
    90deg,
    var(--color-primary) 0%,
    var(--color-primary-light) 70%,
    transparent 100%
  );
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-6);
}

.header-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h2);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.header-subtitle {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-tertiary);
  max-width: 500px;
  line-height: 1.6;
}

/* Primary Button - Leather-bound style */
.btn-primary {
  background: var(--color-primary);
  border: 1px solid var(--color-primary);
  color: #fff;
  font-family: var(--font-sans);
  font-weight: 500;
  padding: var(--space-3) var(--space-6);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 2px 4px rgba(139, 90, 43, 0.2);
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
  transform: translateY(-2px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 4px 12px rgba(139, 90, 43, 0.3);
}

.btn-primary:active {
  background: var(--color-primary-active);
  border-color: var(--color-primary-active);
  transform: translateY(0);
}

/* ========================================
   Sections - Editorial Section Headers
   ======================================== */

.section {
  margin-bottom: var(--space-8);
  animation: fadeInUp 0.5s ease-out backwards;
}

.section:nth-child(2) { animation-delay: 0.1s; }
.section:nth-child(3) { animation-delay: 0.2s; }

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.section-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h4);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.01em;
}

.section-count {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-tertiary);
  background: var(--color-bg-tertiary);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-border);
}

/* ========================================
   Grid Layouts
   ======================================== */

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-6);
}

@media (max-width: 1024px) {
  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .grid-3 {
    grid-template-columns: 1fr;
  }
}

/* ========================================
   Cards - Book-texture Cards
   ======================================== */

.card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  transition: all var(--transition-base);
}

/* ========================================
   Project Cards - Literary Book Cards
   ======================================== */

.project-card {
  cursor: pointer;
  background: linear-gradient(
    180deg,
    var(--color-bg-elevated) 0%,
    var(--color-bg-secondary) 100%
  );
  border: 1px solid var(--color-border);
  position: relative;
  overflow: hidden;
}

.project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(
    90deg,
    var(--color-primary) 0%,
    var(--color-primary-light) 50%,
    transparent 100%
  );
  opacity: 0;
  transition: opacity var(--transition-base);
}

.project-card:hover,
.project-card:focus {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
  border-color: var(--color-border-focus);
  outline: none;
}

.project-card:hover::before,
.project-card:focus::before {
  opacity: 1;
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-3);
}

.project-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h4);
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-genre {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-primary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}

.project-premise {
  font-family: var(--font-serif);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
  line-height: 1.7;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: var(--space-4);
  min-height: 2.75rem;
  font-style: italic;
}

/* Status Badges */
.badge {
  font-family: var(--font-sans);
  font-size: var(--font-size-xs);
  font-weight: 500;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  white-space: nowrap;
}

.badge-success {
  background: rgba(74, 124, 89, 0.15);
  color: var(--color-success);
  border: 1px solid rgba(74, 124, 89, 0.3);
}

.badge-info {
  background: rgba(91, 124, 153, 0.15);
  color: var(--color-info);
  border: 1px solid rgba(91, 124, 153, 0.3);
}

.badge-warning {
  background: rgba(184, 134, 11, 0.15);
  color: var(--color-warning);
  border: 1px solid rgba(184, 134, 11, 0.3);
}

.badge-error {
  background: rgba(155, 44, 44, 0.15);
  color: var(--color-error);
  border: 1px solid rgba(155, 44, 44, 0.3);
}

/* Project Stats */
.project-stats {
  display: flex;
  gap: var(--space-6);
  margin-bottom: var(--space-4);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}

.stat {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-value {
  font-family: var(--font-serif);
  font-size: var(--font-size-body);
  font-weight: 700;
  color: var(--color-text-primary);
}

.stat-label {
  font-family: var(--font-sans);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

/* Progress Bar - Ink fill style */
.progress-bar {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  box-shadow: inset 0 1px 2px rgba(44, 36, 22, 0.08);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(
    90deg,
    var(--color-primary) 0%,
    var(--color-primary-hover) 100%
  );
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
  box-shadow: 0 1px 2px rgba(139, 90, 43, 0.3);
}

/* ========================================
   Loading Skeleton - Ghost writing
   ======================================== */

.loading-container {
  margin-bottom: var(--space-8);
}

.skeleton-card {
  pointer-events: none;
  background: linear-gradient(
    90deg,
    var(--color-bg-secondary) 0%,
    var(--color-bg-tertiary) 50%,
    var(--color-bg-secondary) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.skeleton {
  background: var(--color-border);
  border-radius: var(--radius-sm);
  opacity: 0.5;
}

.skeleton-title {
  height: 28px;
  width: 70%;
  margin-bottom: var(--space-3);
}

.skeleton-text {
  height: 16px;
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
  height: 22px;
  width: 80px;
}

.skeleton-progress {
  height: 6px;
  width: 100px;
}

/* ========================================
   Empty State - Blank page
   ======================================== */

.empty-state {
  padding: var(--space-16) var(--space-8);
  text-align: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  border: 2px dashed var(--color-border);
}

.empty-state-icon {
  color: var(--color-border);
  margin-bottom: var(--space-4);
}

.empty-state-icon .el-icon {
  font-size: 64px;
  color: var(--color-text-placeholder);
}

.empty-state-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-state-description {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  max-width: 400px;
  margin: 0 auto var(--space-6);
  line-height: 1.6;
}

.empty-state-action {
  margin: 0 auto;
}

/* ========================================
   Bottom Grid - Activity & Health
   ======================================== */

.bottom-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr;
  gap: var(--space-6);
  animation: fadeInUp 0.5s ease-out 0.3s backwards;
}

@media (max-width: 1024px) {
  .bottom-grid {
    grid-template-columns: 1fr;
  }
}

/* ========================================
   Activity Section - Manuscript Timeline
   ======================================== */

.activity-section {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
}

.empty-activity {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-tertiary);
  font-family: var(--font-sans);
}

/* Timeline - Literary manuscript style */
.timeline {
  position: relative;
}

.timeline-item {
  position: relative;
  padding-left: var(--space-8);
  padding-bottom: var(--space-5);
}

.timeline-item:last-child {
  padding-bottom: 0;
}

.timeline-item::before {
  content: '';
  position: absolute;
  left: 8px;
  top: 4px;
  width: 12px;
  height: 12px;
  background: var(--color-primary);
  border-radius: 50%;
  border: 3px solid var(--color-bg-elevated);
  box-shadow: 0 0 0 2px var(--color-primary-light);
  transition: all var(--transition-base);
}

.timeline-item:hover::before {
  background: var(--color-primary-hover);
  transform: scale(1.1);
}

.timeline-item::after {
  content: '';
  position: absolute;
  left: 13px;
  top: 20px;
  bottom: 0;
  width: 2px;
  background: linear-gradient(
    180deg,
    var(--color-border) 0%,
    var(--color-border-light) 100%
  );
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
  font-family: var(--font-serif);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.activity-description {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-left: 22px;
}

.activity-time {
  font-family: var(--font-sans);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-left: 22px;
  font-style: italic;
}

/* ========================================
   Health Section - Library card style
   ======================================== */

.health-section {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
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
  padding: var(--space-4);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  transition: all var(--transition-base);
}

.health-item:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border);
}

.health-icon {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-md);
  color: var(--color-primary);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.health-icon .el-icon {
  font-size: 20px;
  color: var(--color-primary);
}

.health-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.health-label {
  font-family: var(--font-sans);
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.health-value {
  font-family: var(--font-serif);
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Storage Bar */
.storage-bar {
  height: 8px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-top: var(--space-1);
  box-shadow: inset 0 1px 2px rgba(44, 36, 22, 0.08);
}

.storage-fill {
  height: 100%;
  background: linear-gradient(
    90deg,
    var(--color-success) 0%,
    var(--color-success) 70%,
    var(--color-warning) 85%,
    var(--color-error) 100%
  );
  border-radius: var(--radius-full);
  transition: width var(--transition-slow);
}

/* ========================================
   Animations
   ======================================== */

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

/* ========================================
   Dark Theme Overrides
   ======================================== */

[data-theme="dark"] .dashboard {
  background: transparent;
}

[data-theme="dark"] .dashboard-header {
  border-bottom-color: var(--color-border);
}

[data-theme="dark"] .dashboard-header::after {
  background: linear-gradient(
    90deg,
    var(--color-primary) 0%,
    var(--color-primary-light) 70%,
    transparent 100%
  );
}

[data-theme="dark"] .project-card {
  background: linear-gradient(
    180deg,
    var(--color-bg-elevated) 0%,
    var(--color-bg-secondary) 100%
  );
}

[data-theme="dark"] .project-card::before {
  background: linear-gradient(
    90deg,
    var(--color-primary) 0%,
    var(--color-primary-hover) 50%,
    transparent 100%
  );
}

[data-theme="dark"] .project-premise {
  color: var(--color-text-secondary);
}

[data-theme="dark"] .skeleton-card {
  background: linear-gradient(
    90deg,
    var(--color-bg-secondary) 0%,
    var(--color-bg-tertiary) 50%,
    var(--color-bg-secondary) 100%
  );
}

[data-theme="dark"] .timeline-item::before {
  border-color: var(--color-bg-elevated);
  box-shadow: 0 0 0 2px rgba(166, 123, 91, 0.4);
}

[data-theme="dark"] .timeline-item::after {
  background: linear-gradient(
    180deg,
    var(--color-border) 0%,
    var(--color-border-light) 100%
  );
}

[data-theme="dark"] .empty-state {
  background: var(--color-bg-elevated);
  border-color: var(--color-border);
}

[data-theme="dark"] .activity-section,
[data-theme="dark"] .health-section {
  background: var(--color-bg-elevated);
  border-color: var(--color-border);
}

[data-theme="dark"] .health-item {
  background: var(--color-bg-secondary);
  border-color: var(--color-border);
}

[data-theme="dark"] .health-icon {
  background: var(--color-bg-elevated);
  border-color: var(--color-border);
}

[data-theme="dark"] .progress-bar,
[data-theme="dark"] .storage-bar {
  background: var(--color-bg-tertiary);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.2);
}

[data-theme="dark"] .empty-state-icon .el-icon {
  color: var(--color-text-tertiary);
}

/* ========================================
   Responsive Design
   ======================================== */

@media (max-width: 768px) {
  .dashboard {
    padding: var(--space-4);
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-title {
    font-size: var(--font-size-h3);
  }
  
  .project-stats {
    gap: var(--space-4);
  }
  
  .btn-primary {
    width: 100%;
    justify-content: center;
  }
}

@media (prefers-reduced-motion: reduce) {
  .dashboard,
  .section,
  .bottom-grid,
  .project-card,
  .skeleton-card {
    animation: none;
  }
  
  .project-card:hover,
  .health-item:hover,
  .btn-primary:hover {
    transform: none;
  }
}
</style>
