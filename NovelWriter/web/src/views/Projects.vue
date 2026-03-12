<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/projectStore'
import type { CreateProjectPayload } from '@/types'
import {
  Plus,
  Search,
  Grid,
  List,
  FolderOpened,
  Document,
  Close,
  Warning,
  Loading
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

// Create project modal state
const isCreateModalOpen = ref(false)
const isSubmitting = ref(false)
const formError = ref('')

const newProjectForm = reactive<CreateProjectPayload>({
  title: '',
  genre: '',
  language: 'zh',
  premise: ''
})

// Genre options
const genreOptions = [
  { value: 'fantasy', label: '奇幻' },
  { value: 'sci-fi', label: '科幻' },
  { value: 'romance', label: '言情' },
  { value: 'mystery', label: '悬疑' },
  { value: 'thriller', label: '惊悚' },
  { value: 'horror', label: '恐怖' },
  { value: 'literary', label: '文学' },
  { value: 'historical', label: '历史' },
  { value: 'adventure', label: '冒险' },
  { value: 'young_adult', label: '青春' }
]

// Language options
const languageOptions = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' }
]

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

// Open create project modal
function openCreateModal() {
  isCreateModalOpen.value = true
  formError.value = ''
  // Reset form
  newProjectForm.title = ''
  newProjectForm.genre = ''
  newProjectForm.language = 'zh'
  newProjectForm.premise = ''
}

// Close create project modal
function closeCreateModal() {
  isCreateModalOpen.value = false
  formError.value = ''
}

// Validate form
function validateForm(): boolean {
  if (!newProjectForm.title || newProjectForm.title.trim().length < 2) {
    formError.value = t('project.validation.titleRequired') || '项目标题至少需要2个字符'
    return false
  }
  formError.value = ''
  return true
}

// Submit create project
async function submitCreateProject() {
  if (!validateForm()) return

  isSubmitting.value = true
  formError.value = ''

  try {
    const newProject = await projectStore.createProject({
      title: newProjectForm.title.trim(),
      genre: newProjectForm.genre || undefined,
      language: newProjectForm.language,
      premise: newProjectForm.premise || undefined
    })

    if (newProject) {
      closeCreateModal()
      // Refresh projects list
      await projectStore.fetchProjects()
    } else {
      formError.value = projectStore.error || t('project.createFailed') || '创建项目失败'
    }
  } catch (err) {
    formError.value = err instanceof Error ? err.message : t('project.createFailed') || '创建项目失败'
  } finally {
    isSubmitting.value = false
  }
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
        <button class="btn btn-primary create-btn" @click="openCreateModal">
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
      <button class="btn btn-primary empty-state-action" @click="openCreateModal">
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
    <!-- Create Project Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="isCreateModalOpen" class="modal-overlay" @click.self="closeCreateModal">
          <div class="modal-container">
            <!-- Modal Header -->
            <div class="modal-header">
              <h2 class="modal-title">创建新项目</h2>
              <button class="modal-close" @click="closeCreateModal" :disabled="isSubmitting">
                <el-icon><Close /></el-icon>
              </button>
            </div>

            <!-- Modal Body -->
            <div class="modal-body">
              <form class="create-project-form" @submit.prevent="submitCreateProject">
                <!-- Title Field -->
                <div class="form-group">
                  <label class="form-label" for="project-title">
                    项目标题 <span class="required">*</span>
                  </label>
                  <input
                    id="project-title"
                    v-model="newProjectForm.title"
                    type="text"
                    class="form-input"
                    placeholder="请输入项目名称"
                    :disabled="isSubmitting"
                    @blur="validateForm"
                  />
                </div>

                <!-- Genre Field -->
                <div class="form-group">
                  <label class="form-label" for="project-genre">类型</label>
                  <select
                    id="project-genre"
                    v-model="newProjectForm.genre"
                    class="form-select"
                    :disabled="isSubmitting"
                  >
                    <option value="">请选择类型</option>
                    <option v-for="genre in genreOptions" :key="genre.value" :value="genre.value">
                      {{ genre.label }}
                    </option>
                  </select>
                </div>

                <!-- Language Field -->
                <div class="form-group">
                  <label class="form-label" for="project-language">语言</label>
                  <select
                    id="project-language"
                    v-model="newProjectForm.language"
                    class="form-select"
                    :disabled="isSubmitting"
                  >
                    <option v-for="lang in languageOptions" :key="lang.value" :value="lang.value">
                      {{ lang.label }}
                    </option>
                  </select>
                </div>

                <!-- Premise Field -->
                <div class="form-group">
                  <label class="form-label" for="project-premise">故事前提</label>
                  <textarea
                    id="project-premise"
                    v-model="newProjectForm.premise"
                    class="form-textarea"
                    rows="4"
                    placeholder="简要描述你的故事..."
                    :disabled="isSubmitting"
                  ></textarea>
                </div>

                <!-- Error Message -->
                <div v-if="formError" class="form-error">
                  <el-icon><Warning /></el-icon>
                  <span>{{ formError }}</span>
                </div>
              </form>
            </div>

            <!-- Modal Footer -->
            <div class="modal-footer">
              <button
                class="btn btn-secondary"
                @click="closeCreateModal"
                :disabled="isSubmitting"
              >
                取消
              </button>
              <button
                class="btn btn-primary"
                @click="submitCreateProject"
                :disabled="isSubmitting || !newProjectForm.title.trim()"
              >
                <el-icon v-if="isSubmitting" class="spinning"><Loading /></el-icon>
                <span v-else>创建项目</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.projects-page {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
  animation: fadeIn var(--transition-slow);
}

/* Header */
.page-header {
  margin-bottom: var(--space-8);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-6);
}

.page-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h2);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  font-weight: 400;
}

.create-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: var(--shadow-md);
}

.create-btn:hover {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-lg);
  transform: translateY(-1px);
}

.create-btn:active {
  background: var(--color-primary-active);
  transform: translateY(0);
}

/* Toolbar */
.toolbar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-8);
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
  z-index: 1;
}

.search-input {
  width: 100%;
  height: 44px;
  padding: 0 var(--space-4) 0 calc(var(--space-4) + 24px);
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: all var(--transition-fast);
  box-shadow: inset 0 1px 2px rgba(44, 36, 22, 0.04);
}

.search-input::placeholder {
  color: var(--color-text-placeholder);
}

.search-input:focus {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-muted), inset 0 1px 2px rgba(44, 36, 22, 0.04);
}

.filters {
  display: flex;
  gap: var(--space-3);
}

.filter-select {
  height: 44px;
  padding: 0 var(--space-4);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-width: 120px;
}

.filter-select:focus {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 2px var(--color-primary-muted);
}

/* View Toggle */
.view-toggle {
  display: flex;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-md);
  padding: var(--space-1);
  gap: var(--space-1);
  border: 1px solid var(--color-border);
}

.toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toggle-btn:hover {
  color: var(--color-text-secondary);
  background: var(--color-bg-elevated);
}

.toggle-btn.active {
  background: var(--color-bg-elevated);
  color: var(--color-primary);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--color-border);
}

/* Projects Grid */
.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--space-6);
  animation: fadeInUp var(--transition-slow);
}

/* Project Card - Book Style */
.project-card {
  cursor: pointer;
  padding: 0;
  overflow: hidden;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  transition: all var(--transition-base);
  position: relative;
}

/* Book spine effect */
.project-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(
    180deg,
    var(--color-primary-light) 0%,
    var(--color-primary) 50%,
    var(--color-primary-active) 100%
  );
  opacity: 0;
  transition: opacity var(--transition-base);
}

.project-card:hover,
.project-card:focus {
  transform: translateY(-4px) rotateX(2deg);
  box-shadow: var(--shadow-card-hover);
  border-color: var(--color-primary-light);
  outline: none;
}

.project-card:hover::before,
.project-card:focus::before {
  opacity: 1;
}

/* Cover */
.project-cover {
  position: relative;
  height: 160px;
  background: linear-gradient(
    135deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 100%
  );
  overflow: hidden;
  border-bottom: 1px solid var(--color-border);
}

/* Paper texture overlay */
.project-cover::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E");
  opacity: 0.03;
  pointer-events: none;
}

.cover-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    145deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 100%
  );
  color: var(--color-text-tertiary);
}

.cover-placeholder .el-icon {
  opacity: 0.5;
}

.status-badge {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  font-family: var(--font-sans);
  font-size: 0.75rem;
  font-weight: 600;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  backdrop-filter: blur(8px);
  box-shadow: var(--shadow-sm);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.status-badge.badge-success {
  background: var(--color-success);
  color: white;
}

.status-badge.badge-warning {
  background: var(--color-warning);
  color: white;
}

.status-badge.badge-info {
  background: var(--color-info);
  color: white;
}

.status-badge.badge-error {
  background: var(--color-error);
  color: white;
}

/* Content */
.project-content {
  padding: var(--space-5);
}

.project-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h4);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: -0.01em;
}

.project-genre {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-primary);
  font-weight: 600;
  margin-bottom: var(--space-2);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.project-premise {
  font-family: var(--font-serif);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  margin-bottom: var(--space-4);
  min-height: 2.5rem;
  font-style: italic;
}

/* Stats */
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
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  font-weight: 700;
  color: var(--color-text-primary);
}

.stat-label {
  font-family: var(--font-sans);
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

/* Progress Bar - Literary Style */
.progress-bar {
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  position: relative;
}

.progress-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.2) 50%,
    transparent 100%
  );
  animation: shimmer 2s infinite;
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
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(200%); }
}

/* Loading Skeleton */
.loading-container {
  margin-bottom: var(--space-8);
}

.skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 100%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

.skeleton-card {
  pointer-events: none;
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.skeleton-cover {
  height: 160px;
  border-radius: 0;
  margin: 0;
  width: 100%;
  background: var(--color-bg-tertiary);
}

.skeleton-title {
  height: 24px;
  width: 70%;
  margin: var(--space-5) var(--space-5) var(--space-3);
}

.skeleton-text {
  height: 16px;
  width: 90%;
  margin: 0 var(--space-5) var(--space-2);
}

.skeleton-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: var(--space-4) var(--space-5) var(--space-5);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}

.skeleton-badge {
  height: 20px;
  width: 80px;
}

.skeleton-progress {
  height: 6px;
  width: 100px;
}

/* Skeleton Table */
.skeleton-table {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  overflow: hidden;
  border: 1px solid var(--color-border);
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
  animation: fadeIn var(--transition-slow);
}

.empty-state-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
  opacity: 0.6;
}

.empty-state-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h3);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-state-description {
  font-family: var(--font-serif);
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  max-width: 320px;
  margin-bottom: var(--space-6);
  font-style: italic;
}

.empty-state-action {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
}

.empty-state-action:hover {
  background: var(--color-primary-hover);
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

/* Table View - Literary Style */
.projects-table-wrapper {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  animation: fadeIn var(--transition-slow);
}

.projects-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.projects-table th {
  font-family: var(--font-sans);
  text-align: left;
  padding: var(--space-4) var(--space-6);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  background: var(--color-bg-secondary);
  border-bottom: 2px solid var(--color-border);
}

.projects-table td {
  padding: var(--space-4) var(--space-6);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-primary);
  border-bottom: 1px solid var(--color-border-light);
}

.projects-table tr:last-child td {
  border-bottom: none;
}

.table-row {
  cursor: pointer;
  transition: all var(--transition-fast);
}

.table-row:hover {
  background: var(--color-bg-secondary);
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
  width: 36px;
  height: 48px;
  border-radius: var(--radius-sm);
  background: linear-gradient(
    145deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 100%
  );
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.title-text {
  font-family: var(--font-serif);
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge.badge-success {
  background: var(--color-success);
  color: white;
}

.badge.badge-warning {
  background: var(--color-warning);
  color: white;
}

.badge.badge-info {
  background: var(--color-info);
  color: white;
}

.badge.badge-error {
  background: var(--color-error);
  color: white;
}

.progress-cell {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.progress-bar-mini {
  flex: 1;
  height: 6px;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  overflow: hidden;
  max-width: 80px;
}

.progress-bar-mini .progress-fill {
  background: var(--color-primary);
}

.progress-text {
  color: var(--color-text-secondary);
  font-size: 0.75rem;
  min-width: 36px;
  font-weight: 600;
}

/* Responsive */
@media (max-width: 768px) {
  .projects-page {
    padding: var(--space-4);
  }

  .header-content {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-4);
  }

  .page-title {
    font-size: var(--font-size-h3);
  }

  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
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

/* Dark Mode Adjustments */
[data-theme="dark"] .search-input {
  background: var(--color-bg-elevated);
  box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.2);
}

[data-theme="dark"] .cover-placeholder {
  background: linear-gradient(
    145deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-secondary) 100%
  );
}

[data-theme="dark"] .project-cover::after {
  opacity: 0.05;
}

[data-theme="dark"] .skeleton {
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 0%,
    var(--color-bg-elevated) 50%,
    var(--color-bg-tertiary) 100%
  );
  background-size: 200% 100%;
}
</style>

/* Create Project Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-container {
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: var(--shadow-xl);
  animation: modalIn 0.2s ease-out;
}

@keyframes modalIn {
  from {
    opacity: 0;
    transform: scale(0.95) translateY(-10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.modal-close {
  background: none;
  border: none;
  padding: var(--space-2);
  cursor: pointer;
  color: var(--color-text-tertiary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.modal-body {
  padding: var(--space-5);
  overflow-y: auto;
  max-height: calc(90vh - 140px);
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-5);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

/* Form Styles */
.create-project-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.required {
  color: var(--color-error);
}

.form-input,
.form-select,
.form-textarea {
  padding: var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-bg-input);
  transition: all var(--transition-fast);
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(139, 90, 43, 0.15);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--color-text-placeholder);
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.form-error {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: rgba(155, 44, 44, 0.1);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

/* Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--color-primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-bg-tertiary);
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}
