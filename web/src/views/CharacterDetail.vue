<script setup lang="ts">
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import {
  User,
  Edit,
  Save as SaveIcon,
  Close,
  ArrowLeft,
  Loading,
  Warning,
  Document
} from '@element-plus/icons-vue'
import { getCharacter, updateCharacter, type Character } from '@/api/characters'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// Route params
const projectId = computed(() => route.params.projectId as string)
const characterName = computed(() => route.params.characterId as string)

// State
const isLoading = ref(true)
const isEditing = ref(false)
const isSubmitting = ref(false)
const submitError = ref('')

// Character data
const character = ref<Character | null>(null)

// Edit form
const editForm = reactive<Partial<Character>>({
  name: '',
  aliases: [],
  tier: 1,
  bio: '',
  persona: '',
  mbti: '',
  profession: '',
  relationships: {},
  interested_topics: []
})

// MBTI options
const mbtiOptions = [
  'INTJ', 'INTP', 'ENTJ', 'ENTP',
  'INFJ', 'INFP', 'ENFJ', 'ENFP',
  'ISTJ', 'ISFJ', 'ESTJ', 'ESFJ',
  'ISTP', 'ISFP', 'ESTP', 'ESFP'
]

// Tier options
const tierOptions = [
  { value: 1, label: '主角/反派', description: 'Main character or antagonist' },
  { value: 2, label: '配角', description: 'Supporting character' },
  { value: 3, label: '次要角色', description: 'Minor character' }
]

// Fetch character data
async function fetchCharacter() {
  if (!projectId.value || !characterName.value) {
    ElMessage.error('Missing project or character ID')
    router.push('/projects')
    return
  }

  isLoading.value = true
  try {
    const data = await getCharacter(projectId.value, characterName.value)
    character.value = data
    
    // Populate edit form
    Object.assign(editForm, {
      name: data.name,
      aliases: data.aliases || [],
      tier: data.tier || 1,
      bio: data.bio || '',
      persona: data.persona || '',
      mbti: data.mbti || '',
      profession: data.profession || '',
      relationships: data.relationships || {},
      interested_topics: data.interested_topics || []
    })
  } catch (err) {
    console.error('Failed to fetch character:', err)
    ElMessage.error('Failed to load character details')
  } finally {
    isLoading.value = false
  }
}

// Toggle edit mode
function toggleEdit() {
  if (isEditing.value) {
    // Cancel edit - reset form
    if (character.value) {
      Object.assign(editForm, {
        name: character.value.name,
        aliases: character.value.aliases || [],
        tier: character.value.tier || 1,
        bio: character.value.bio || '',
        persona: character.value.persona || '',
        mbti: character.value.mbti || '',
        profession: character.value.profession || '',
        relationships: character.value.relationships || {},
        interested_topics: character.value.interested_topics || []
      })
    }
    submitError.value = ''
  }
  isEditing.value = !isEditing.value
}

// Validate form
function validateForm(): boolean {
  if (!editForm.name || editForm.name.trim().length < 1) {
    submitError.value = 'Character name is required'
    return false
  }
  if (editForm.name.trim().length > 100) {
    submitError.value = 'Character name must be less than 100 characters'
    return false
  }
  if (editForm.tier && (editForm.tier < 1 || editForm.tier > 5)) {
    submitError.value = 'Tier must be between 1 and 5'
    return false
  }
  submitError.value = ''
  return true
}

// Submit update
async function submitUpdate() {
  if (!validateForm()) return
  if (!projectId.value || !characterName.value) return

  isSubmitting.value = true
  submitError.value = ''

  try {
    await updateCharacter(projectId.value, characterName.value, editForm)
    ElMessage.success('Character updated successfully')
    isEditing.value = false
    // Refresh data
    await fetchCharacter()
  } catch (err) {
    console.error('Failed to update character:', err)
    submitError.value = err instanceof Error ? err.message : 'Failed to update character'
  } finally {
    isSubmitting.value = false
  }
}

// Go back to project detail
function goBack() {
  router.push(`/projects/${projectId.value}`)
}

// Format relationships for display
const relationshipEntries = computed(() => {
  if (!character.value?.relationships) return []
  return Object.entries(character.value.relationships)
})

// Get tier label
function getTierLabel(tier: number): string {
  const option = tierOptions.find(t => t.value === tier)
  return option ? option.label : 'Unknown'
}

// Get tier color class
function getTierColor(tier: number): string {
  if (tier === 1) return 'tier-1'
  if (tier === 2) return 'tier-2'
  return 'tier-3'
}

// Fetch on mount
onMounted(() => {
  fetchCharacter()
})

// Watch for route changes
watch([() => route.params.projectId, () => route.params.characterId], () => {
  fetchCharacter()
})
</script>

<template>
  <div class="character-detail">
    <!-- Loading State -->
    <div v-if="isLoading" class="loading-state">
      <div class="skeleton skeleton-header"></div>
      <div class="skeleton skeleton-content"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="!character" class="not-found">
      <div class="not-found-icon">
        <el-icon :size="64"><User /></el-icon>
      </div>
      <h2 class="not-found-title">Character Not Found</h2>
      <p class="not-found-description">
        The character you're looking for doesn't exist or has been removed.
      </p>
      <button class="btn btn-primary" @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        Back to Project
      </button>
    </div>

    <!-- Main Content -->
    <template v-else>
      <!-- Header -->
      <header class="detail-header">
        <button class="back-button" @click="goBack" :aria-label="'Go back'">
          <el-icon><ArrowLeft /></el-icon>
        </button>
        <div class="header-content">
          <div class="character-avatar">
            <div class="avatar-placeholder">
              {{ character.name.charAt(0).toUpperCase() }}
            </div>
          </div>
          <div class="header-info">
            <h1 class="character-name">{{ character.name }}</h1>
            <div class="character-meta">
              <span class="tier-badge" :class="getTierColor(character.tier)">
                {{ getTierLabel(character.tier) }}
              </span>
              <span v-if="character.mbti" class="mbti-badge">{{ character.mbti }}</span>
              <span v-if="character.profession" class="profession-badge">{{ character.profession }}</span>
            </div>
          </div>
          <div class="header-actions">
            <button
              v-if="!isEditing"
              class="btn btn-primary"
              @click="toggleEdit"
            >
              <el-icon><Edit /></el-icon>
              Edit Character
            </button>
            <template v-else>
              <button
                class="btn btn-secondary"
                @click="toggleEdit"
                :disabled="isSubmitting"
              >
                <el-icon><Close /></el-icon>
                Cancel
              </button>
              <button
                class="btn btn-primary"
                @click="submitUpdate"
                :disabled="isSubmitting"
              >
                <el-icon v-if="isSubmitting" class="spinning"><Loading /></el-icon>
                <el-icon v-else><SaveIcon /></el-icon>
                Save Changes
              </button>
            </template>
          </div>
        </div>
      </header>

      <!-- Content Grid -->
      <main class="content-grid">
        <!-- Left Column - Main Info -->
        <div class="main-column">
          <!-- Bio Section -->
          <section class="card info-section">
            <h3 class="section-title">
              <el-icon><Document /></el-icon>
              Biography
            </h3>
            <div v-if="!isEditing" class="section-content">
              <p class="bio-text">{{ character.bio || 'No biography provided' }}</p>
            </div>
            <div v-else class="section-content">
              <div class="form-group">
                <label class="form-label" for="bio">Biography</label>
                <textarea
                  id="bio"
                  v-model="editForm.bio"
                  class="form-textarea"
                  rows="6"
                  placeholder="Enter character biography..."
                  :disabled="isSubmitting"
                ></textarea>
              </div>
            </div>
          </section>

          <!-- Persona Section -->
          <section class="card info-section">
            <h3 class="section-title">
              <el-icon><User /></el-icon>
              Persona
            </h3>
            <div v-if="!isEditing" class="section-content">
              <p class="bio-text">{{ character.persona || 'No persona description provided' }}</p>
            </div>
            <div v-else class="section-content">
              <div class="form-group">
                <label class="form-label" for="persona">Persona</label>
                <textarea
                  id="persona"
                  v-model="editForm.persona"
                  class="form-textarea"
                  rows="4"
                  placeholder="Describe character's personality..."
                  :disabled="isSubmitting"
                ></textarea>
              </div>
            </div>
          </section>

          <!-- Topics Section -->
          <section v-if="character.interested_topics?.length" class="card info-section">
            <h3 class="section-title">
              <el-icon><Document /></el-icon>
              Interested Topics
            </h3>
            <div v-if="!isEditing" class="section-content">
              <div class="tags-container">
                <span
                  v-for="topic in character.interested_topics"
                  :key="topic"
                  class="topic-tag"
                >
                  {{ topic }}
                </span>
              </div>
            </div>
            <div v-else class="section-content">
              <div class="form-group">
                <label class="form-label" for="topics">Topics (comma-separated)</label>
                <input
                  id="topics"
                  v-model="editForm.interested_topics"
                  type="text"
                  class="form-input"
                  placeholder="topic1, topic2, topic3"
                  :disabled="isSubmitting"
                />
                <p class="form-hint">Separate topics with commas</p>
              </div>
            </div>
          </section>
        </div>

        <!-- Right Column - Details -->
        <div class="side-column">
          <!-- Details Card -->
          <section class="card details-section">
            <h3 class="section-title">Details</h3>
            <dl v-if="!isEditing" class="details-list">
              <div class="detail-row">
                <dt>Name</dt>
                <dd>{{ character.name }}</dd>
              </div>
              <div class="detail-row">
                <dt>Tier</dt>
                <dd>{{ getTierLabel(character.tier) }}</dd>
              </div>
              <div v-if="character.mbti" class="detail-row">
                <dt>MBTI</dt>
                <dd>{{ character.mbti }}</dd>
              </div>
              <div v-if="character.profession" class="detail-row">
                <dt>Profession</dt>
                <dd>{{ character.profession }}</dd>
              </div>
              <div v-if="character.aliases?.length" class="detail-row">
                <dt>Aliases</dt>
                <dd>{{ character.aliases.join(', ') }}</dd>
              </div>
            </dl>

            <!-- Edit Form -->
            <div v-else class="edit-form">
              <div class="form-group">
                <label class="form-label" for="name">Name</label>
                <input
                  id="name"
                  v-model="editForm.name"
                  type="text"
                  class="form-input"
                  :disabled="isSubmitting"
                />
              </div>

              <div class="form-group">
                <label class="form-label" for="tier">Tier</label>
                <select
                  id="tier"
                  v-model.number="editForm.tier"
                  class="form-select"
                  :disabled="isSubmitting"
                >
                  <option v-for="option in tierOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label" for="mbti">MBTI</label>
                <select
                  id="mbti"
                  v-model="editForm.mbti"
                  class="form-select"
                  :disabled="isSubmitting"
                >
                  <option value="">Select MBTI type</option>
                  <option v-for="mbti in mbtiOptions" :key="mbti" :value="mbti">
                    {{ mbti }}
                  </option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label" for="profession">Profession</label>
                <input
                  id="profession"
                  v-model="editForm.profession"
                  type="text"
                  class="form-input"
                  placeholder="e.g., Teacher, Detective, Student"
                  :disabled="isSubmitting"
                />
              </div>

              <div class="form-group">
                <label class="form-label" for="aliases">Aliases (comma-separated)</label>
                <input
                  id="aliases"
                  v-model="editForm.aliases"
                  type="text"
                  class="form-input"
                  placeholder="alias1, alias2"
                  :disabled="isSubmitting"
                />
              </div>
            </div>
          </section>

          <!-- Relationships Section -->
          <section v-if="relationshipEntries.length" class="card relationships-section">
            <h3 class="section-title">Relationships</h3>
            <div v-if="!isEditing" class="relationships-list">
              <div
                v-for="[targetChar, type] in relationshipEntries"
                :key="targetChar"
                class="relationship-item"
              >
                <span class="relationship-target">{{ targetChar }}</span>
                <span class="relationship-type">{{ type }}</span>
              </div>
            </div>
            <div v-else class="section-content">
              <p class="form-hint">Relationships can be edited in the project view</p>
            </div>
          </section>

          <!-- Error Message -->
          <div v-if="submitError" class="error-message">
            <el-icon><Warning /></el-icon>
            <span>{{ submitError }}</span>
          </div>
        </div>
      </main>
    </template>
  </div>
</template>

<style scoped>
.character-detail {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1400px;
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
  height: 120px;
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
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-6);
  padding: var(--space-6);
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--color-border-light);
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.back-button:hover {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.header-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--space-5);
}

.character-avatar {
  flex-shrink: 0;
}

.avatar-placeholder {
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: var(--radius-xl);
  font-size: 2.5rem;
  font-weight: var(--font-weight-bold);
  color: white;
  box-shadow: var(--shadow-md);
}

.header-info {
  flex: 1;
  min-width: 0;
}

.character-name {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
  line-height: var(--line-height-tight);
}

.character-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-wrap: wrap;
}

.tier-badge,
.mbti-badge,
.profession-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
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

.tier-3 {
  background: linear-gradient(135deg, #a8a8a8 0%, #7a7a7a 100%);
  color: white;
}

.mbti-badge {
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
}

.profession-badge {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}

.header-actions {
  display: flex;
  gap: var(--space-3);
  flex-shrink: 0;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: var(--space-6);
}

/* Cards */
.card {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  margin-bottom: var(--space-6);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-4) 0;
}

.section-content {
  color: var(--color-text-secondary);
}

/* Bio Text */
.bio-text {
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  margin: 0;
  white-space: pre-wrap;
}

/* Tags */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.topic-tag {
  display: inline-flex;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.topic-tag:hover {
  background: rgba(0, 122, 255, 0.15);
  transform: translateY(-1px);
}

/* Details List */
.details-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.detail-row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  padding-bottom: var(--space-3);
  border-bottom: 1px solid var(--color-border-light);
}

.detail-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.detail-row dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-medium);
  text-transform: capitalize;
}

.detail-row dd {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
  text-align: right;
}

/* Edit Form */
.edit-form,
.form-group {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  margin-bottom: var(--space-4);
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
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

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.form-hint {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin: var(--space-1) 0 0 0;
}

/* Relationships */
.relationships-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.relationship-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-md);
  border: 1px solid var(--color-border-light);
}

.relationship-target {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.relationship-type {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-style: italic;
}

/* Error Message */
.error-message {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4);
  background: rgba(155, 44, 44, 0.1);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-size: var(--font-size-sm);
}

/* Buttons */
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

/* Spinning Animation */
.spinning {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .character-detail {
    padding: var(--space-4);
  }

  .detail-header {
    padding: var(--space-4);
    flex-direction: column;
    align-items: flex-start;
  }

  .character-avatar {
    align-self: center;
  }

  .character-name {
    font-size: var(--font-size-2xl);
  }

  .header-actions {
    flex-direction: column;
  }

  .btn {
    width: 100%;
  }
}
</style>
