<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/projectStore'
import {
  Plus,
  Search,
  Grid,
  List,
  FolderOpened,
  Document
} from '@element-plus/icons-vue'

const { t } = useI18n()
const router = useRouter()
const projectStore = useProjectStore()

// View mode state
const viewMode = ref<'card' | 'table'>('card')

// Search and filter state
const searchQuery = ref('')
const selectedGenre = ref('')
const selectedStatus = ref('')

// Computed properties
const projects = computed(() => projectStore.projectList)
const isLoading = computed(() => projectStore.isLoading)

// Extract unique genres and statuses for filters
const availableGenres = computed(() => {
  const genres = new Set(projects.value.map(p => p.genre).filter(Boolean))
  return Array.from(genres).sort()
})

const availableStatuses = computed(() => {
  const statuses = new Set(projects.value.map(p => p.status).filter(Boolean))
  return Array.from(statuses).sort()
})

// Filtered projects
const filteredProjects = computed(() => {
  let result = projects.value

  // Search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(p =>
      p.title.toLowerCase().includes(query) ||
      p.premise?.toLowerCase().includes(query) ||
      p.genre?.toLowerCase().includes(query)
    )
  }

  // Genre filter
  if (selectedGenre.value) {
    result = result.filter(p => p.genre === selectedGenre.value)
  }

  // Status filter
  if (selectedStatus.value) {
    result = result.filter(p => p.status === selectedStatus.value)
  }

  return result
})

// Get status badge class
function getStatusClass(status: string): string {
  const statusMap: Record<string, string> = {
    'active': 'badge-success',
    'writing': 'badge-success',
    'in_progress': 'badge-info',
    'draft': 'badge-warning',
    'planning': 'badge-warning',
    'completed': 'badge-success',
    'published': 'badge-success',
    'error': 'badge-error'
  }
  return statusMap[status.toLowerCase()] || 'badge-warning'
}

// Format status for display
function formatStatus(status: string): string {
  return status.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
}

// Navigate to project detail
function openProject(projectId: string) {
  router.push(`/projects/${projectId}`)
}

// Create new project
function createNewProject() {
  router.push('/projects/new')
}

// Clear filters
function clearFilters() {
  searchQuery.value = ''
  selectedGenre.value = ''
  selectedStatus.value = ''
}

// Initialize data
onMounted(() => {
  projectStore.fetchProjects()
})
</script>

<template>
  <div class="projects-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="page-title">{{ t('project.projects') }}</h1>
          <p class="page-subtitle">{{ t('project.description') }}</p>
        </div>
        <button class="btn btn-primary create-btn" @click="createNewProject">
          <el-icon><Plus /></el-icon>
          {{ t('project.create') }}
        </button>
      </div>
    </header>

    <!-- Toolbar -->
    <div class="toolbar">
      <!-- Search Bar -->
      <div class="search-wrapper">
        <el-icon class="search-icon"><Search /></el-icon>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          :placeholder="t('project.searchPlaceholder')"
        />
      </div>

      <!-- Filters -->
      <div class="filters">
        <select v-model="selectedGenre" class="filter-select">
          <option value="">{{ t('project.allGenres') }}</option>
          <option v-for="genre in availableGenres" :key="genre" :value="genre">
            {{ genre }}
          </option>
        </select>

        <select v-model="selectedStatus" class="filter-select">
          <option value="">{{ t('project.allStatuses') }}</option>
          <option v-for="status in availableStatuses" :key="status" :value="status">
            {{ formatStatus(status) }}
          </option>
        </select>
      </div>

      <!-- View Toggle -->
      <div class="view-toggle">
        <button
          :class="['toggle-btn', { active: viewMode === 'card' }]"
          @click="viewMode = 'card'"
          :title="t('project.viewCard')"
        >
          <el-icon><Grid /></el-icon>
        </button>
        <button
          :class="['toggle-btn', { active: viewMode === 'table' }]"
          @click="viewMode = 'table'"
          :title="t('project.viewTable')"
        >
          <el-icon><List /></el-icon>
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div v-if="viewMode === 'card'" class="grid-3">
        <div v-for="i in 6" :key="`skeleton-${i}`" class="card skeleton-card">
          <div class="skeleton skeleton-cover"></div>
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-text"></div>
          <div class="skeleton-footer">
            <div class="skeleton skeleton-badge"></div>
            <div class="skeleton skeleton-progress"></div>
          </div>
        </div>
      </div>
      <div v-else class="skeleton-table">
        <div v-for="i in 5" :key="`row-${i}`" class="skeleton-row">
          <div class="skeleton skeleton-cell"></div>
          <div class="skeleton skeleton-cell"></div>
          <div class="skeleton skeleton-cell"></div>
          <div class="skeleton skeleton-cell"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="projects.length === 0" class="empty-state">
      <div class="empty-state-icon">
        <el-icon :size="64"><FolderOpened /></el-icon>
      </div>
      <h3 class="empty-state-title">{{ t('common.noData') }}</h3>
      <p class="empty-state-description">
        {{ t('dashboard.noRecentActivity') }}
      </p>
      <button class="btn btn-primary empty-state-action" @click="createNewProject">
        <el-icon><Plus /></el-icon>
        {{ t('project.create') }}
      </button>
    </div>

    <!-- No Results State -->
    <div v-else-if="filteredProjects.length === 0" class="empty-state">
      <div class="empty-state-icon">
        <el-icon :size="64"><Document /></el-icon>
      </div>
      <h3 class="empty-state-title">{{ t('project.noResults') }}</h3>
      <p class="empty-state-description">
        {{ t('project.noResultsDesc') }}
      </p>
      <button class="btn btn-secondary" @click="clearFilters">
        {{ t('common.cancel') }}
      </button>
    </div>

    <!-- Card View -->
    <div v-else-if="viewMode === 'card'" class="projects-grid">
      <article
        v-for="project in filteredProjects"
        :key="project.id"
        class="card project-card"
        @click="openProject(project.id)"
        tabindex="0"
        @keypress.enter="openProject(project.id)"
      >
        <!-- Cover Placeholder -->
        <div class="project-cover">
          <div class="cover-placeholder">
            <el-icon :size="32"><Document /></el-icon>
          </div>
          <span :class="['status-badge', getStatusClass(project.status)]">
            {{ formatStatus(project.status) }}
          </span>
        </div>

        <!-- Content -->
        <div class="project-content">
          <h3 class="project-title">{{ project.title }}</h3>
          <p class="project-genre">{{ project.genre }}</p>
          <p class="project-premise">{{ project.premise }}</p>

          <!-- Stats -->
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
              <span class="stat-label">{{ t('project.complete') }}</span>
            </div>
          </div>

          <!-- Progress Bar -->
          <div class="progress-bar">
            <div
              class="progress-fill"
              :style="{ width: `${project.progress_percent}%` }"
            ></div>
          </div>
        </div>
      </article>
    </div>

    <!-- Table View -->
    <div v-else class="projects-table-wrapper">
      <table class="projects-table">
        <thead>
          <tr>
            <th class="col-title">{{ t('project.name') }}</th>
            <th class="col-genre">{{ t('project.genre') }}</th>
            <th class="col-status">{{ t('chapter.status') }}</th>
            <th class="col-progress">{{ t('project.complete') }}</th>
            <th class="col-words">{{ t('project.wordCount') }}</th>
            <th class="col-chapters">{{ t('project.chapterCount') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="project in filteredProjects"
            :key="project.id"
            class="table-row"
            @click="openProject(project.id)"
            tabindex="0"
            @keypress.enter="openProject(project.id)"
          >
            <td class="col-title">
              <div class="title-cell">
                <div class="cover-mini">
                  <el-icon><Document /></el-icon>
                </div>
                <span class="title-text">{{ project.title }}</span>
              </div>
            </td>
            <td class="col-genre">{{ project.genre }}</td>
            <td class="col-status">
              <span :class="['badge', getStatusClass(project.status)]">
                {{ formatStatus(project.status) }}
              </span>
            </td>
            <td class="col-progress">
              <div class="progress-cell">
                <div class="progress-bar-mini">
                  <div
                    class="progress-fill"
                    :style="{ width: `${project.progress_percent}%` }"
                  ></div>
                </div>
                <span class="progress-text">{{ project.progress_percent }}%</span>
              </div>
            </td>
            <td class="col-words">{{ project.total_words.toLocaleString() }}</td>
            <td class="col-chapters">{{ project.completed_chapters }}/{{ project.target_chapters }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.projects-page {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.page-header {
  margin-bottom: var(--space-6);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-6);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.page-subtitle {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

.create-btn {
  flex-shrink: 0;
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  flex-wrap: wrap;
}

.search-wrapper {
  position: relative;
  flex: 1;
  min-width: 200px;
  max-width: 400px;
}

.search-icon {
  position: absolute;
  left: var(--space-4);
  top: 50%;
  transform: translateY(-50%);
  color: var(--color-text-tertiary);
  font-size: 16px;
  pointer-events: none;
}

.search-input {
  width: 100%;
  height: 40px;
  padding: 0 var(--space-4) 0 var(--space-10);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  outline: none;
  transition: border-color var(--transition-fast), box-shadow var(--transition-fast);
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.search-input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.filters {
  display: flex;
  gap: var(--space-3);
}

.filter-select {
  height: 40px;
  padding: 0 var(--space-4);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  outline: none;
  cursor: pointer;
  transition: border-color var(--transition-fast);
  min-width: 120px;
}

.filter-select:focus {
  border-color: var(--color-primary);
}

/* View Toggle */
.view-toggle {
  display: flex;
  background: var(--color-border-light);
  border-radius: var(--radius-lg);
  padding: var(--space-1);
  gap: var(--space-1);
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 32px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  color: var(--color-text-primary);
}

.toggle-btn.active {
  background: var(--color-surface);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
}

/* Projects Grid */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-6);
}

/* Project Card */
.project-card {
  cursor: pointer;
  padding: 0;
  overflow: hidden;
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

/* Cover */
.project-cover {
  position: relative;
  height: 140px;
  background: var(--gradient-surface);
  overflow: hidden;
}

.cover-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-border-light) 0%, var(--color-border) 100%);
  color: var(--color-text-tertiary);
}

.status-badge {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  backdrop-filter: blur(8px);
}

.status-badge.badge-success {
  background: rgba(52, 199, 89, 0.9);
  color: white;
}

.status-badge.badge-warning {
  background: rgba(255, 149, 0, 0.9);
  color: white;
}

.status-badge.badge-info {
  background: rgba(90, 200, 250, 0.9);
  color: white;
}

.status-badge.badge-error {
  background: rgba(255, 59, 48, 0.9);
  color: white;
}

/* Content */
.project-content {
  padding: var(--space-5);
}

.project-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
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
  min-height: 2.5rem;
}

/* Stats */
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

/* Progress Bar */
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

.skeleton-cover {
  height: 140px;
  border-radius: 0;
  margin: calc(-1 * var(--space-6));
  margin-bottom: var(--space-4);
  width: calc(100% + var(--space-12));
}

.skeleton-title {
  height: 20px;
  width: 70%;
  margin-bottom: var(--space-3);
}

.skeleton-text {
  height: 14px;
  width: 100%;
  margin-bottom: var(--space-2);
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

/* Skeleton Table */
.skeleton-table {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  overflow: hidden;
}

.skeleton-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr 1fr 1fr;
  gap: var(--space-4);
  padding: var(--space-4) var(--space-6);
  border-bottom: 1px solid var(--color-border-light);
}

.skeleton-cell {
  height: 20px;
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-16) var(--space-8);
  text-align: center;
}

.empty-state-icon {
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
  margin-bottom: var(--space-6);
}

/* Table View */
.projects-table-wrapper {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  overflow: hidden;
  box-shadow: var(--shadow-card);
}

.projects-table {
  width: 100%;
  border-collapse: collapse;
}

.projects-table th {
  text-align: left;
  padding: var(--space-4) var(--space-6);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: var(--color-background);
  border-bottom: 1px solid var(--color-border);
}

.projects-table td {
  padding: var(--space-4) var(--space-6);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-light);
}

.table-row {
  cursor: pointer;
  transition: background var(--transition-fast);
}

.table-row:hover {
  background: var(--color-background);
}

.table-row:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}

.title-cell {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.cover-mini {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--color-border-light);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.title-text {
  font-weight: var(--font-weight-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.progress-bar-mini {
  flex: 1;
  height: 4px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
  max-width: 80px;
}

.progress-text {
  color: var(--color-text-secondary);
  font-size: var(--font-size-xs);
  min-width: 36px;
}

/* Responsive */
@media (max-width: 768px) {
  .projects-page {
    padding: var(--space-4);
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }

  .search-wrapper {
    max-width: none;
  }

  .filters {
    width: 100%;
  }

  .filter-select {
    flex: 1;
  }

  .view-toggle {
    align-self: flex-end;
  }

  .projects-grid {
    grid-template-columns: 1fr;
  }

  .projects-table-wrapper {
    overflow-x: auto;
  }

  .projects-table {
    min-width: 600px;
  }
}
</style>
