<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useProjectStore } from '@/stores/projectStore';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { createCharacter, getCharacters, type Character, type CreateCharacterPayload } from '@/api/characters';
import {
  Document,
  User,
  Setting,
  Edit,
  Plus,
  Download,
  Delete,
  ArrowLeft,
  Close,
  Warning,
  Loading
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

// Character state
const characters = ref<Character[]>([]);
const isCharactersLoading = ref(false);

// Character creation modal state
const isCreateCharacterModalOpen = ref(false);
const isSubmittingCharacter = ref(false);
const characterFormError = ref('');

// Character form
const characterForm = reactive<CreateCharacterPayload>({
  name: '',
  tier: 1,
  bio: '',
  mbti: '',
  profession: ''
});

// Character tier options
const characterTierOptions = [
  { value: 1, label: '主角', description: 'tier 1' },
  { value: 1, label: '反派', description: 'tier 1' },
  { value: 2, label: '配角', description: 'tier 2' },
  { value: 3, label: '次要角色', description: 'tier 3' }
];

// MBTI options
const mbtiOptions = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
];

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

// Computed for character grouping
const mainCharacters = computed(() => {
  return characters.value.filter(c => c.tier === 1);
});

const supportingCharacters = computed(() => {
  return characters.value.filter(c => c.tier >= 2);
});

const hasCharacters = computed(() => characters.value.length > 0);

// View character details
function viewCharacter(character: import('@/api/characters').Character) {
  router.push(`/projects/${projectId.value}/characters/${encodeURIComponent(character.name)}`);
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

// Fetch characters for the project
async function fetchCharacters() {
  if (!projectId.value) return;
  isCharactersLoading.value = true;
  try {
    const response = await getCharacters(projectId.value);
    characters.value = response.characters;
  } catch (err) {
    console.error('Failed to fetch characters:', err);
    ElMessage.error('获取角色列表失败');
  } finally {
    isCharactersLoading.value = false;
  }
}

// Open create character modal
function openCreateCharacterModal() {
  isCreateCharacterModalOpen.value = true;
  characterFormError.value = '';
  // Reset form
  characterForm.name = '';
  characterForm.tier = 1;
  characterForm.bio = '';
  characterForm.mbti = '';
  characterForm.profession = '';
}

// Close create character modal
function closeCreateCharacterModal() {
  isCreateCharacterModalOpen.value = false;
  characterFormError.value = '';
}

// Validate character form
function validateCharacterForm(): boolean {
  if (!characterForm.name || characterForm.name.trim().length < 1) {
    characterFormError.value = '角色名称不能为空';
    return false;
  }
  if (characterForm.name.trim().length > 50) {
    characterFormError.value = '角色名称不能超过50个字符';
    return false;
  }
  characterFormError.value = '';
  return true;
}

// Submit create character
async function submitCreateCharacter() {
  if (!validateCharacterForm()) return;
  if (!projectId.value) return;

  isSubmittingCharacter.value = true;
  characterFormError.value = '';

  try {
    await createCharacter(projectId.value, {
      name: characterForm.name.trim(),
      tier: characterForm.tier,
      bio: characterForm.bio || undefined,
      mbti: characterForm.mbti || undefined,
      profession: characterForm.profession || undefined
    });

    ElMessage.success('角色创建成功');
    closeCreateCharacterModal();
    // Refresh characters list
    await fetchCharacters();
  } catch (err) {
    characterFormError.value = err instanceof Error ? err.message : '创建角色失败';
  } finally {
    isSubmittingCharacter.value = false;
  }
}

// Fetch project data on mount
onMounted(async () => {
  if (projectStore.projects.length === 0) {
    await projectStore.fetchProjects();
  }
  isLoading.value = false;
  // Pre-fetch characters for when user switches to characters tab
  await fetchCharacters();
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
            <!-- Characters Header -->
            <div class="characters-header">
              <h3 class="characters-title">{{ t('projectDetail.tabs.characters') }}</h3>
              <button class="btn btn-primary btn-sm" @click="openCreateCharacterModal">
                <el-icon><Plus /></el-icon>
                创建角色
              </button>
            </div>

            <!-- Loading State -->
            <div v-if="isCharactersLoading" class="characters-loading">
              <div v-for="i in 3" :key="`char-skeleton-${i}`" class="character-card skeleton">
                <div class="skeleton-avatar"></div>
                <div class="skeleton-info">
                  <div class="skeleton-name"></div>
                  <div class="skeleton-role"></div>
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div v-else-if="characters.length === 0" class="empty-content">
              <el-icon :size="48"><User /></el-icon>
              <h3>{{ t('projectDetail.tabs.characters') }}</h3>
              <p>{{ t('projectDetail.empty.characters') }}</p>
              <button class="btn btn-primary empty-action" @click="openCreateCharacterModal">
                <el-icon><Plus /></el-icon>
                创建第一个角色
              </button>
            </div>

            <!-- Character List -->
            <div v-else class="characters-list">
              <div
                v-for="character in characters"
                :key="character.name"
                class="character-card"
                @click="viewCharacter(character)"
              >
                <div class="character-avatar">
                  <el-icon :size="24"><User /></el-icon>
                </div>
                <div class="character-info">
                  <div class="character-name">{{ character.name }}</div>
                  <div class="character-meta">
                    <span class="character-tier" :class="`tier-${character.tier}`">
                      {{ character.tier === 1 ? '主角/反派' : character.tier === 2 ? '配角' : '次要角色' }}
                    </span>
                    <span v-if="character.mbti" class="character-mbti">{{ character.mbti }}</span>
                    <span v-if="character.profession" class="character-profession">{{ character.profession }}</span>
                  </div>
                  <p v-if="character.bio" class="character-bio">{{ character.bio }}</p>
                </div>
              </div>
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

      <!-- Create Character Modal -->
      <Teleport to="body">
        <Transition name="modal">
          <div v-if="isCreateCharacterModalOpen" class="modal-overlay" @click.self="closeCreateCharacterModal">
            <div class="modal-container">
              <!-- Modal Header -->
              <div class="modal-header">
                <h2 class="modal-title">创建新角色</h2>
                <button class="modal-close" @click="closeCreateCharacterModal" :disabled="isSubmittingCharacter">
                  <el-icon><Close /></el-icon>
                </button>
              </div>

              <!-- Modal Body -->
              <div class="modal-body">
                <form class="create-character-form" @submit.prevent="submitCreateCharacter">
                  <!-- Name Field -->
                  <div class="form-group">
                    <label class="form-label" for="character-name">
                      角色名称 <span class="required">*</span>
                    </label>
                    <input
                      id="character-name"
                      v-model="characterForm.name"
                      type="text"
                      class="form-input"
                      placeholder="请输入角色名称"
                      :disabled="isSubmittingCharacter"
                      @blur="validateCharacterForm"
                    />
                  </div>

                  <!-- Tier/Type Field -->
                  <div class="form-group">
                    <label class="form-label" for="character-tier">角色类型</label>
                    <select
                      id="character-tier"
                      v-model="characterForm.tier"
                      class="form-select"
                      :disabled="isSubmittingCharacter"
                    >
                      <option :value="1">主角</option>
                      <option :value="1">反派</option>
                      <option :value="2">配角</option>
                      <option :value="3">次要角色</option>
                    </select>
                  </div>

                  <!-- Bio Field -->
                  <div class="form-group">
                    <label class="form-label" for="character-bio">角色简介</label>
                    <textarea
                      id="character-bio"
                      v-model="characterForm.bio"
                      class="form-textarea"
                      rows="3"
                      placeholder="简要描述这个角色..."
                      :disabled="isSubmittingCharacter"
                    ></textarea>
                  </div>

                  <!-- MBTI Field -->
                  <div class="form-group">
                    <label class="form-label" for="character-mbti">MBTI类型</label>
                    <select
                      id="character-mbti"
                      v-model="characterForm.mbti"
                      class="form-select"
                      :disabled="isSubmittingCharacter"
                    >
                      <option value="">请选择MBTI类型</option>
                      <option v-for="mbti in mbtiOptions" :key="mbti" :value="mbti">
                        {{ mbti }}
                      </option>
                    </select>
                  </div>

                  <!-- Profession Field -->
                  <div class="form-group">
                    <label class="form-label" for="character-profession">职业</label>
                    <input
                      id="character-profession"
                      v-model="characterForm.profession"
                      type="text"
                      class="form-input"
                      placeholder="请输入角色职业"
                      :disabled="isSubmittingCharacter"
                    />
                  </div>

                  <!-- Error Message -->
                  <div v-if="characterFormError" class="form-error">
                    <el-icon><Warning /></el-icon>
                    <span>{{ characterFormError }}</span>
                  </div>
                </form>
              </div>

              <!-- Modal Footer -->
              <div class="modal-footer">
                <button
                  class="btn btn-secondary"
                  @click="closeCreateCharacterModal"
                  :disabled="isSubmittingCharacter"
                >
                  取消
                </button>
                <button
                  class="btn btn-primary"
                  @click="submitCreateCharacter"
                  :disabled="isSubmittingCharacter || !characterForm.name.trim()"
                >
                  <el-icon v-if="isSubmittingCharacter" class="spinning"><Loading /></el-icon>
                  <span v-else>创建角色</span>
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </Teleport>
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

/* Characters Tab Styles */
.characters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}

.characters-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0;
}

.btn-sm {
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-sm);
}

/* Characters Loading Skeleton */
.characters-loading {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.characters-loading .character-card.skeleton {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  background: linear-gradient(
    90deg,
    var(--color-border-light) 25%,
    var(--color-border) 50%,
    var(--color-border-light) 75%
  );
  background-size: 200% 100%;
  animation: skeleton-loading 1.5s infinite;
}

.skeleton-avatar {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-full);
  background: var(--color-border);
}

.skeleton-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.skeleton-name {
  width: 120px;
  height: 16px;
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

.skeleton-role {
  width: 80px;
  height: 12px;
  background: var(--color-border);
  border-radius: var(--radius-sm);
}

/* Characters List */
.characters-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* Character Card - Book-like Design */
.character-card {
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  cursor: pointer;
  position: relative;
  overflow: hidden;
}

.character-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: var(--color-primary);
  opacity: 0;
  transition: opacity var(--transition-base);
}

.character-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
}

.character-card:hover::before {
  opacity: 1;
}

/* Character Avatar */
.character-avatar {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: var(--radius-full);
  color: white;
  font-weight: var(--font-weight-bold);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
}

/* Character Info */
.character-info {
  flex: 1;
  min-width: 0;
}

.character-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1) 0;
}

.character-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
  flex-wrap: wrap;
}

/* Tier Badges */
.character-tier {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.tier-1 {
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%);
  color: white;
}

.tier-2 {
  background: linear-gradient(135deg, #4ecdc4 0%, #44a08d 100%);
  color: white;
}

.tier-3,
.tier-4,
.tier-5 {
  background: linear-gradient(135deg, #a8a8a8 0%, #7a7a7a 100%);
  color: white;
}

/* MBTI Badge */
.character-mbti {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

/* Profession Badge */
.character-profession {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  background: var(--color-border-light);
  color: var(--color-text-secondary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
}

/* Character Bio */
.character-bio {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Empty Action Button */
.empty-action {
  margin-top: var(--space-4);
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

/* Modal Styles - Matching Projects.vue */
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
.create-character-form {
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
  font-family: var(--font-family);
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
  min-height: 80px;
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

/* Spinning Animation for Loading Icon */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
