<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { search, type SearchResultItem, type SearchResponse } from '@/api/search'

interface Props {
  modelValue: boolean
}

const props = defineProps<Props>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()

// State
const searchQuery = ref('')
const searchResults = ref<SearchResponse | null>(null)
const isLoading = ref(false)
const error = ref<string | null>(null)
const selectedType = ref<'all' | 'project' | 'chapter' | 'character'>('all')

// Computed
const isOpen = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
})

const hasResults = computed(() => {
  if (!searchResults.value) return false
  return searchResults.value.total_results > 0
})

const projectCount = computed(() => searchResults.value?.projects.length || 0)
const chapterCount = computed(() => searchResults.value?.chapters.length || 0)
const characterCount = computed(() => searchResults.value?.characters.length || 0)

// Methods
const close = () => {
  isOpen.value = false
  searchQuery.value = ''
  searchResults.value = null
  error.value = null
}

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    close()
  }
}

const performSearch = async () => {
  if (!searchQuery.value.trim()) {
    searchResults.value = null
    return
  }

  isLoading.value = true
  error.value = null

  try {
    const results = await search({
      q: searchQuery.value,
      type: selectedType.value === 'all' ? undefined : selectedType.value,
    })
    searchResults.value = results
  } catch (err) {
    console.error('Search failed:', err)
    error.value = 'Search failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}

const handleResultClick = (result: SearchResultItem) => {
  close()
  if (result.url) {
    router.push(result.url)
  }
}

// Watch for query changes with debounce
let debounceTimer: NodeJS.Timeout | null = null
watch(searchQuery, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    performSearch()
  }, 300)
}, { immediate: true })

// Watch for type changes
watch(selectedType, () => {
  performSearch()
})

// Keyboard shortcuts
onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeyDown)
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="isOpen" class="modal-overlay" @click.self="close">
        <div class="modal-container">
          <!-- Modal Header -->
          <div class="modal-header">
            <div class="search-icon">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <input
              v-model="searchQuery"
              type="text"
              class="search-input"
              placeholder="Search projects, chapters, characters..."
              autofocus
            />
            <button class="close-btn" @click="close">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <!-- Type Filters -->
          <div class="type-filters">
            <button
              :class="['filter-btn', { active: selectedType === 'all' }]"
              @click="selectedType = 'all'"
            >
              All
              <span v-if="searchResults" class="count">{{ searchResults.total_results }}</span>
            </button>
            <button
              :class="['filter-btn', { active: selectedType === 'project' }]"
              @click="selectedType = 'project'"
            >
              Projects
              <span v-if="searchResults" class="count">{{ projectCount }}</span>
            </button>
            <button
              :class="['filter-btn', { active: selectedType === 'chapter' }]"
              @click="selectedType = 'chapter'"
            >
              Chapters
              <span v-if="searchResults" class="count">{{ chapterCount }}</span>
            </button>
            <button
              :class="['filter-btn', { active: selectedType === 'character' }]"
              @click="selectedType = 'character'"
            >
              Characters
              <span v-if="searchResults" class="count">{{ characterCount }}</span>
            </button>
          </div>

          <!-- Modal Body -->
          <div class="modal-body">
            <!-- Loading State -->
            <div v-if="isLoading" class="loading-state">
              <div class="spinner"></div>
              <span>Searching...</span>
            </div>

            <!-- Error State -->
            <div v-else-if="error" class="error-state">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{{ error }}</span>
            </div>

            <!-- Empty State -->
            <div v-else-if="!searchQuery.trim()" class="empty-state">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <p>Start typing to search</p>
              <p class="hint">Search across projects, chapters, and characters</p>
            </div>

            <!-- No Results -->
            <div v-else-if="!hasResults" class="no-results">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="11" cy="11" r="8" />
                <line x1="21" y1="21" x2="16.65" y2="16.65" />
                <line x1="8" y1="11" x2="14" y2="11" />
              </svg>
              <p>No results found for "{{ searchQuery }}"</p>
              <p class="hint">Try different keywords or filters</p>
            </div>

            <!-- Results -->
            <div v-else class="results-list">
              <!-- Projects Section -->
              <div v-if="selectedType === 'all' && projectCount > 0" class="result-section">
                <div class="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  <span>Projects</span>
                </div>
                <div class="result-items">
                  <button
                    v-for="result in searchResults.projects"
                    :key="result.id"
                    class="result-item"
                    @click="handleResultClick(result)"
                  >
                    <div class="result-icon project">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                      </svg>
                    </div>
                    <div class="result-content">
                      <div class="result-title">{{ result.title }}</div>
                      <div class="result-meta">
                        <span v-if="result.genre" class="badge">{{ result.genre }}</span>
                        <span v-if="result.progress">{{ result.progress }}</span>
                      </div>
                    </div>
                    <div class="result-reason">
                      <span v-for="reason in result.match_reason" :key="reason" class="match-tag">
                        {{ reason }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>

              <!-- Chapters Section -->
              <div v-if="selectedType === 'all' && chapterCount > 0" class="result-section">
                <div class="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                    <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                  </svg>
                  <span>Chapters</span>
                </div>
                <div class="result-items">
                  <button
                    v-for="result in searchResults.chapters"
                    :key="result.id"
                    class="result-item"
                    @click="handleResultClick(result)"
                  >
                    <div class="result-icon chapter">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
                        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
                      </svg>
                    </div>
                    <div class="result-content">
                      <div class="result-title">{{ result.title }}</div>
                      <div class="result-meta">
                        <span class="novel-title">{{ result.novel_title }}</span>
                        <span v-if="result.chapter_number">Chapter {{ result.chapter_number }}</span>
                      </div>
                      <div v-if="result.preview" class="result-preview">{{ result.preview }}</div>
                    </div>
                    <div class="result-reason">
                      <span v-for="reason in result.match_reason" :key="reason" class="match-tag">
                        {{ reason }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>

              <!-- Characters Section -->
              <div v-if="selectedType === 'all' && characterCount > 0" class="result-section">
                <div class="section-header">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <span>Characters</span>
                </div>
                <div class="result-items">
                  <button
                    v-for="result in searchResults.characters"
                    :key="result.id"
                    class="result-item"
                    @click="handleResultClick(result)"
                  >
                    <div class="result-icon character">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                        <circle cx="12" cy="7" r="4" />
                      </svg>
                    </div>
                    <div class="result-content">
                      <div class="result-title">{{ result.name || result.title }}</div>
                      <div class="result-meta">
                        <span class="novel-title">{{ result.novel_title }}</span>
                        <span v-if="result.tier" :class="['badge', result.tier === 1 ? 'main' : 'supporting']">
                          {{ result.tier === 1 ? 'Main' : 'Supporting' }}
                        </span>
                        <span v-if="result.profession">{{ result.profession }}</span>
                      </div>
                      <div v-if="result.bio_preview" class="result-preview">{{ result.bio_preview }}</div>
                    </div>
                    <div class="result-reason">
                      <span v-for="reason in result.match_reason" :key="reason" class="match-tag">
                        {{ reason }}
                      </span>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Modal Footer -->
          <div v-if="hasResults" class="modal-footer">
            <span class="results-count">{{ searchResults?.total_results }} results</span>
            <span class="hint">Press ESC to close</span>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ========== MODAL OVERLAY ========== */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 80px;
  z-index: 1000;
}

/* ========== MODAL CONTAINER ========== */
.modal-container {
  width: 100%;
  max-width: 700px;
  max-height: calc(100vh - 160px);
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ========== MODAL HEADER ========== */
.modal-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-elevated);
}

.search-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  font-family: var(--font-sans);
  font-size: var(--font-size-body-lg);
  color: var(--color-text-primary);
  background: transparent;
}

.search-input::placeholder {
  color: var(--color-text-tertiary);
}

.close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

/* ========== TYPE FILTERS ========== */
.type-filters {
  display: flex;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-6);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
}

.filter-btn {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border: 1px solid transparent;
  background: transparent;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.filter-btn:hover {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.filter-btn.active {
  background: var(--color-primary-muted);
  color: var(--color-primary);
  border-color: var(--color-primary);
}

.filter-btn .count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-1);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  font-size: 11px;
  font-weight: 600;
}

.filter-btn.active .count {
  background: var(--color-primary);
  color: white;
}

/* ========== MODAL BODY ========== */
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-4) var(--space-6);
  max-height: 500px;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-12) 0;
  color: var(--color-text-secondary);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-12) 0;
  color: var(--color-error);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-12) 0;
  color: var(--color-text-tertiary);
  text-align: center;
}

.empty-state svg {
  opacity: 0.5;
}

.empty-state .hint {
  font-size: var(--font-size-body-sm);
  opacity: 0.7;
}

/* No Results */
.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  padding: var(--space-12) 0;
  color: var(--color-text-tertiary);
  text-align: center;
}

.no-results svg {
  opacity: 0.5;
}

.no-results .hint {
  font-size: var(--font-size-body-sm);
  opacity: 0.7;
}

/* Results List */
.results-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.result-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.section-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-tertiary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.result-items {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.result-item {
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-3);
  border: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}

.result-item:hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-border);
  transform: translateX(2px);
}

.result-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.result-icon.project {
  background: rgba(114, 137, 218, 0.1);
  color: var(--color-info);
}

.result-icon.chapter {
  background: rgba(139, 90, 43, 0.1);
  color: var(--color-primary);
}

.result-icon.character {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
}

.result-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.result-title {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
}

.result-preview {
  font-size: var(--font-size-body-sm);
  color: var(--color-text-tertiary);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-reason {
  display: flex;
  gap: var(--space-1);
  flex-shrink: 0;
}

.match-tag {
  padding: 2px var(--space-2);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-secondary);
  text-transform: capitalize;
}

.badge {
  padding: 2px var(--space-2);
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-sm);
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
}

.badge.main {
  background: rgba(139, 90, 43, 0.1);
  color: var(--color-primary);
}

.badge.supporting {
  background: rgba(168, 85, 247, 0.1);
  color: #a855f7;
}

.novel-title {
  font-style: italic;
  opacity: 0.8;
}

/* ========== MODAL FOOTER ========== */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-6);
  border-top: 1px solid var(--color-border);
  background: var(--color-bg-secondary);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-tertiary);
}

.results-count {
  font-weight: 500;
  color: var(--color-text-secondary);
}

/* ========== TRANSITIONS ========== */
.modal-enter-active,
.modal-leave-active {
  transition: opacity var(--transition-base);
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform var(--transition-base), opacity var(--transition-base);
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: translateY(-20px) scale(0.98);
  opacity: 0;
}
</style>
