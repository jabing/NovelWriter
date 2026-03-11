<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useProjectStore } from '@/stores/projectStore'
import { Reading, Notebook } from '@element-plus/icons-vue'

const { t } = useI18n()
const router = useRouter()
const projectStore = useProjectStore()

// Computed properties
const projects = computed(() => projectStore.projectList)
const isLoading = computed(() => projectStore.isLoading)

// Sort projects by reading progress (in-progress first)
const sortedProjects = computed(() => {
  return [...projects.value].sort((a, b) => {
    // In-progress projects first
    const aInProgress = a.progress_percent > 0 && a.progress_percent < 100
    const bInProgress = b.progress_percent > 0 && b.progress_percent < 100
    
    if (aInProgress && !bInProgress) return -1
    if (!aInProgress && bInProgress) return 1
    
    // Then sort by progress (higher first for in-progress)
    if (aInProgress && bInProgress) {
      return b.progress_percent - a.progress_percent
    }
    
    // Completed projects last, sorted by completion date (most recent first)
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  })
})

// Continue reading project (most recent in-progress)
const continueReadingProject = computed(() => {
  return sortedProjects.value.find(p => p.progress_percent > 0 && p.progress_percent < 100)
})

// Format word count
function formatWordCount(count: number): string {
  if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}k`
  }
  return count.toString()
}

// Get gradient colors based on genre
function getCoverGradient(genre: string): string {
  const gradients: Record<string, string> = {
    'Fantasy': 'linear-gradient(145deg, #667eea 0%, #764ba2 100%)',
    'Science Fiction': 'linear-gradient(145deg, #0f0c29 0%, #302b63 50%, #24243e 100%)',
    'Romance': 'linear-gradient(145deg, #ff6b6b 0%, #ee5a24 100%)',
    'Mystery': 'linear-gradient(145deg, #2c3e50 0%, #4ca1af 100%)',
    'Thriller': 'linear-gradient(145deg, #232526 0%, #414345 100%)',
    'Horror': 'linear-gradient(145deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)',
    'Literary Fiction': 'linear-gradient(145deg, #355c7d 0%, #6c5b7b 50%, #c06c84 100%)',
    'Historical Fiction': 'linear-gradient(145deg, #8b4513 0%, #d2691e 100%)',
    'Adventure': 'linear-gradient(145deg, #11998e 0%, #38ef7d 100%)',
    'Young Adult': 'linear-gradient(145deg, #fc5c7d 0%, #6a82fb 100%)'
  }
  return gradients[genre] || 'linear-gradient(145deg, #667eea 0%, #764ba2 100%)'
}

// Navigate to read chapter
function continueReading(projectId: string) {
  router.push(`/projects/${projectId}`)
}

// Open project details
function openProject(projectId: string) {
  router.push(`/projects/${projectId}`)
}

// Initialize data
onMounted(() => {
  projectStore.fetchProjects()
})
</script>

<template>
  <div class="bookshelf-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="page-title">{{ t('bookshelf.title') }}</h1>
          <p class="page-subtitle">{{ t('bookshelf.subtitle') }}</p>
        </div>
      </div>
    </header>

    <!-- Continue Reading Section -->
    <section v-if="continueReadingProject && !isLoading" class="continue-section">
      <div class="section-header">
        <h2 class="section-title">{{ t('bookshelf.continueReading') }}</h2>
      </div>
      <div class="continue-card" @click="continueReading(continueReadingProject.id)">
        <div class="continue-cover" :style="{ background: getCoverGradient(continueReadingProject.genre) }">
          <div class="cover-spine"></div>
          <div class="cover-content">
            <span class="cover-title">{{ continueReadingProject.title }}</span>
          </div>
          <div class="cover-progress">
            <div class="progress-track">
              <div 
                class="progress-fill" 
                :style="{ width: `${continueReadingProject.progress_percent}%` }"
              ></div>
            </div>
            <span class="progress-text">{{ continueReadingProject.progress_percent }}% {{ t('bookshelf.completed') }}</span>
          </div>
        </div>
        <div class="continue-info">
          <h3 class="continue-title">{{ continueReadingProject.title }}</h3>
          <p class="continue-genre">{{ continueReadingProject.genre }}</p>
          <div class="continue-stats">
            <span class="stat-item">
              <span class="stat-value">{{ continueReadingProject.completed_chapters }}</span>
              <span class="stat-label">/{{ continueReadingProject.target_chapters }} {{ t('bookshelf.chapters') }}</span>
            </span>
            <span class="stat-divider">·</span>
            <span class="stat-item">
              <span class="stat-value">{{ formatWordCount(continueReadingProject.total_words) }}</span>
              <span class="stat-label"> {{ t('bookshelf.words') }}</span>
            </span>
          </div>
          <button class="btn-continue" @click.stop="continueReading(continueReadingProject.id)">
            <el-icon><Reading /></el-icon>
            {{ t('bookshelf.continue') }}
          </button>
        </div>
      </div>
    </section>

    <!-- Loading State -->
    <div v-if="isLoading" class="loading-container">
      <div class="books-grid">
        <div v-for="i in 6" :key="`skeleton-${i}`" class="book-skeleton">
          <div class="skeleton skeleton-cover"></div>
          <div class="skeleton skeleton-title"></div>
          <div class="skeleton skeleton-author"></div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="projects.length === 0" class="empty-state">
      <div class="empty-state-icon">
        <el-icon :size="64"><Notebook /></el-icon>
      </div>
      <h3 class="empty-state-title">{{ t('bookshelf.noBooks') }}</h3>
      <p class="empty-state-description">
        {{ t('bookshelf.noBooksDesc') }}
      </p>
      <button class="btn btn-primary" @click="router.push('/projects/new')">
        {{ t('project.create') }}
      </button>
    </div>

    <!-- All Books Section -->
    <section v-else class="all-books-section">
      <div class="section-header">
        <h2 class="section-title">{{ t('bookshelf.allBooks') }}</h2>
        <span class="book-count">{{ projects.length }} {{ projects.length === 1 ? t('bookshelf.book') : t('bookshelf.books') }}</span>
      </div>
      
      <div class="books-grid">
        <article
          v-for="project in sortedProjects"
          :key="project.id"
          class="book-card"
          @click="openProject(project.id)"
          tabindex="0"
          @keypress.enter="openProject(project.id)"
        >
          <!-- Book Cover -->
          <div class="book-cover" :style="{ background: getCoverGradient(project.genre) }">
            <div class="cover-spine"></div>
            <div class="cover-content">
              <span class="cover-title">{{ project.title }}</span>
              <span class="cover-genre">{{ project.genre }}</span>
            </div>
            
            <!-- Progress Bar -->
            <div class="cover-progress-bar">
              <div 
                class="progress-fill" 
                :style="{ width: `${project.progress_percent}%` }"
              ></div>
            </div>
            
            <!-- Completed Badge -->
            <div v-if="project.progress_percent === 100" class="completed-badge">
              <el-icon><Reading /></el-icon>
            </div>
          </div>

          <!-- Book Info -->
          <div class="book-info">
            <h3 class="book-title">{{ project.title }}</h3>
            <p class="book-author">{{ project.genre }}</p>
            <div class="book-progress">
              <span class="progress-percent">{{ project.progress_percent }}%</span>
              <span class="progress-detail">
                {{ project.completed_chapters }}/{{ project.target_chapters }} {{ t('bookshelf.chapters') }}
              </span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<style scoped>
.bookshelf-page {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.page-header {
  margin-bottom: var(--space-8);
}

.header-text {
  max-width: 600px;
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  letter-spacing: -0.02em;
}

.page-subtitle {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
}

/* Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.book-count {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

/* Continue Reading Section */
.continue-section {
  margin-bottom: var(--space-10);
}

.continue-card {
  display: flex;
  gap: var(--space-6);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  padding: var(--space-6);
  box-shadow: var(--shadow-card);
  cursor: pointer;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
}

.continue-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.continue-cover {
  position: relative;
  width: 140px;
  min-width: 140px;
  height: 210px;
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  overflow: hidden;
}

.continue-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: var(--space-2) 0;
}

.continue-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
}

.continue-genre {
  font-size: var(--font-size-sm);
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--space-4);
}

.continue-stats {
  display: flex;
  align-items: baseline;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
  flex-wrap: wrap;
}

.stat-item {
  display: flex;
  align-items: baseline;
  gap: var(--space-1);
}

.stat-value {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.stat-divider {
  color: var(--color-text-tertiary);
}

.btn-continue {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-top: auto;
  padding: var(--space-3) var(--space-6);
  background: var(--gradient-primary);
  color: white;
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: opacity var(--transition-fast), transform var(--transition-fast);
  min-height: 44px;
  align-self: flex-start;
}

.btn-continue:hover {
  opacity: 0.9;
  transform: scale(1.02);
}

.btn-continue:active {
  transform: scale(0.98);
}

/* Books Grid */
.books-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--space-6);
}

/* Book Card */
.book-card {
  cursor: pointer;
  transition: transform var(--transition-base);
}

.book-card:hover,
.book-card:focus {
  transform: translateY(-8px);
  outline: none;
}

.book-card:hover .book-cover,
.book-card:focus .book-cover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
}

/* Book Cover - 2:3 Aspect Ratio */
.book-cover {
  position: relative;
  width: 100%;
  padding-bottom: 150%; /* 2:3 aspect ratio */
  border-radius: var(--radius-lg);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  transition: box-shadow var(--transition-base);
  overflow: hidden;
}

/* Book Spine Effect */
.cover-spine {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 8px;
  background: linear-gradient(90deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 100%);
}

/* Cover Content */
.cover-content {
  position: absolute;
  top: var(--space-5);
  left: var(--space-4);
  right: var(--space-3);
  bottom: var(--space-8);
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.cover-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: white;
  line-height: var(--line-height-tight);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.cover-genre {
  font-size: var(--font-size-xs);
  color: rgba(255, 255, 255, 0.7);
  margin-top: var(--space-2);
}

/* Cover Progress Bar */
.cover-progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(0, 0, 0, 0.2);
}

.cover-progress-bar .progress-fill {
  height: 100%;
  background: white;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.5);
}

/* Continue Cover Progress */
.cover-progress {
  position: absolute;
  bottom: var(--space-4);
  left: var(--space-4);
  right: var(--space-3);
}

.progress-track {
  height: 4px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: var(--radius-full);
  overflow: hidden;
  margin-bottom: var(--space-2);
}

.progress-track .progress-fill {
  height: 100%;
  background: white;
  border-radius: var(--radius-full);
}

.progress-text {
  font-size: var(--font-size-xs);
  color: rgba(255, 255, 255, 0.9);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
}

/* Completed Badge */
.completed-badge {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  width: 28px;
  height: 28px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-success);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

/* Book Info */
.book-info {
  padding: var(--space-3) 0;
}

.book-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-author {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.book-progress {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.progress-percent {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-primary);
}

.progress-detail {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Loading Skeleton */
.loading-container {
  margin-top: var(--space-8);
}

.book-skeleton {
  display: flex;
  flex-direction: column;
}

.skeleton-cover {
  padding-bottom: 150%;
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-3);
}

.skeleton-title {
  height: 16px;
  width: 80%;
  margin-bottom: var(--space-2);
}

.skeleton-author {
  height: 12px;
  width: 60%;
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

/* Responsive */
@media (max-width: 768px) {
  .bookshelf-page {
    padding: var(--space-4);
  }

  .page-title {
    font-size: var(--font-size-2xl);
  }

  .continue-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }

  .continue-cover {
    width: 120px;
    min-width: 120px;
    height: 180px;
  }

  .continue-info {
    align-items: center;
  }

  .continue-stats {
    justify-content: center;
  }

  .btn-continue {
    width: 100%;
  }

  .books-grid {
    grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
    gap: var(--space-4);
  }
}

@media (max-width: 480px) {
  .books-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-3);
  }

  .book-title {
    font-size: var(--font-size-xs);
  }

  .book-author {
    font-size: 10px;
  }
}
</style>
