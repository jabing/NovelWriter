<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import {
  ArrowLeft,
  User,
  Loading,
  Warning,
  Document
} from '@element-plus/icons-vue';
import GraphVisualization from '@/components/GraphVisualization.vue';
import type { GraphNode, GraphEdge } from '@/api/graph';
import { getCharacterGraph } from '@/api/graph';
import { getCharacter } from '@/api/characters';
import type { Character } from '@/api/characters';

const route = useRoute();
const router = useRouter();
const { t } = useI18n();

// State
const isLoading = ref(true);
const error = ref<string | null>(null);
const nodes = ref<GraphNode[]>([]);
const edges = ref<GraphEdge[]>([]);
const selectedCharacter = ref<Character | null>(null);
const isCharacterDetailOpen = ref(false);
const isCharacterLoading = ref(false);

// Get project ID from route
const projectId = computed(() => route.params.id as string);

// Check if we have graph data
const hasGraphData = computed(() => nodes.value.length > 0);

// Fetch graph data
async function fetchGraphData() {
  if (!projectId.value) {
    error.value = 'Project ID is required';
    isLoading.value = false;
    return;
  }

  isLoading.value = true;
  error.value = null;

  try {
    const response = await getCharacterGraph(projectId.value);
    nodes.value = response.nodes;
    edges.value = response.edges;
  } catch (err) {
    console.error('Failed to fetch character graph:', err);
    error.value = err instanceof Error ? err.message : 'Failed to load character graph';
    ElMessage.error(t('characterGraph.errors.loadFailed'));
  } finally {
    isLoading.value = false;
  }
}

// Handle node click
async function handleNodeClick(nodeData: GraphNode['data']) {
  if (!projectId.value) return;

  isCharacterDetailOpen.value = true;
  isCharacterLoading.value = true;
  selectedCharacter.value = null;

  try {
    const character = await getCharacter(projectId.value, nodeData.label);
    selectedCharacter.value = character;
  } catch (err) {
    console.error('Failed to fetch character details:', err);
    ElMessage.error(t('characterGraph.errors.characterLoadFailed'));
    isCharacterDetailOpen.value = false;
  } finally {
    isCharacterLoading.value = false;
  }
}

// Handle edge click
function handleEdgeClick(edgeData: GraphEdge['data']) {
  console.log('Edge clicked:', edgeData);
}

// Close character detail panel
function closeCharacterDetail() {
  isCharacterDetailOpen.value = false;
  selectedCharacter.value = null;
}

// Navigate back to project detail
function goBack() {
  router.push(`/projects/${projectId.value}`);
}

// Navigate to character detail page
function viewCharacterDetail() {
  if (selectedCharacter.value) {
    router.push(`/projects/${projectId.value}/characters/${encodeURIComponent(selectedCharacter.value.name)}`);
  }
}

// Format relationship type for display
function formatRelationshipType(type: string): string {
  return type.toLowerCase().replace(/_/g, ' ');
}

// Fetch data on mount
onMounted(fetchGraphData);

// Watch for route changes
watch(() => route.params.id, (newId, oldId) => {
  if (newId !== oldId) {
    fetchGraphData();
  }
});
</script>

<template>
  <div class="character-graph">
    <!-- Header -->
    <header class="graph-header">
      <button class="back-button" @click="goBack" :aria-label="t('characterGraph.aria.goBack')">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <div class="header-content">
        <h1 class="page-title">{{ t('characterGraph.title') }}</h1>
        <p class="page-description">{{ t('characterGraph.description') }}</p>
      </div>
    </header>

    <!-- Main Content -->
    <main class="graph-main">
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state" role="status" aria-live="polite">
        <el-icon :size="48" class="loading-icon"><Loading /></el-icon>
        <p class="loading-text">{{ t('characterGraph.loading') }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-state" role="alert">
        <div class="error-icon">
          <el-icon :size="48"><Warning /></el-icon>
        </div>
        <h2 class="error-title">{{ t('characterGraph.error.title') }}</h2>
        <p class="error-message">{{ error }}</p>
        <button class="btn btn-primary" @click="fetchGraphData">
          {{ t('characterGraph.actions.retry') }}
        </button>
      </div>

      <!-- Empty State (No Characters) -->
      <div v-else-if="!hasGraphData" class="empty-state" role="status" aria-live="polite">
        <div class="empty-icon">
          <el-icon :size="64"><Document /></el-icon>
        </div>
        <h2 class="empty-title">{{ t('characterGraph.empty.title') }}</h2>
        <p class="empty-description">{{ t('characterGraph.empty.description') }}</p>
        <button class="btn btn-primary" @click="goBack">
          {{ t('characterGraph.actions.backToProject') }}
        </button>
      </div>

      <!-- Graph Visualization -->
      <div v-else class="graph-content">
        <GraphVisualization
          :nodes="nodes"
          :edges="edges"
          :loading="isLoading"
          @node-click="handleNodeClick"
          @edge-click="handleEdgeClick"
          class="graph-visualization"
        />
      </div>
    </main>

    <!-- Character Detail Panel (Slide-over) -->
    <Teleport to="body">
      <Transition name="slide">
        <div v-if="isCharacterDetailOpen" class="character-panel-overlay" @click.self="closeCharacterDetail">
          <aside class="character-panel" role="dialog" aria-modal="true" :aria-label="t('characterGraph.characterPanel.title')">
            <!-- Panel Header -->
            <div class="panel-header">
              <h2 class="panel-title">{{ t('characterGraph.characterPanel.title') }}</h2>
              <button class="panel-close" @click="closeCharacterDetail" :aria-label="t('common.close')">
                <el-icon><Close /></el-icon>
              </button>
            </div>

            <!-- Panel Content -->
            <div class="panel-content">
              <!-- Loading -->
              <div v-if="isCharacterLoading" class="panel-loading">
                <el-icon :size="32" class="spinning"><Loading /></el-icon>
                <span>{{ t('characterGraph.characterPanel.loading') }}</span>
              </div>

              <!-- Character Details -->
              <div v-else-if="selectedCharacter" class="character-details">
                <!-- Avatar and Name -->
                <div class="character-header">
                  <div class="character-avatar">
                    <el-icon :size="32"><User /></el-icon>
                  </div>
                  <div class="character-name-section">
                    <h3 class="character-name">{{ selectedCharacter.name }}</h3>
                    <span v-if="selectedCharacter.mbti" class="character-mbti">{{ selectedCharacter.mbti }}</span>
                  </div>
                </div>

                <!-- Basic Info -->
                <div class="info-section">
                  <h4 class="section-title">{{ t('characterGraph.characterPanel.basicInfo') }}</h4>
                  <dl class="info-list">
                    <div class="info-row" v-if="selectedCharacter.tier">
                      <dt>{{ t('characterGraph.characterPanel.tier') }}</dt>
                      <dd class="tier-badge" :class="`tier-${selectedCharacter.tier}`">
                        {{ selectedCharacter.tier === 1 ? '主角/反派' : selectedCharacter.tier === 2 ? '配角' : '次要角色' }}
                      </dd>
                    </div>
                    <div class="info-row" v-if="selectedCharacter.profession">
                      <dt>{{ t('characterGraph.characterPanel.profession') }}</dt>
                      <dd>{{ selectedCharacter.profession }}</dd>
                    </div>
                    <div class="info-row" v-if="selectedCharacter.current_status">
                      <dt>{{ t('characterGraph.characterPanel.status') }}</dt>
                      <dd>{{ selectedCharacter.current_status }}</dd>
                    </div>
                  </dl>
                </div>

                <!-- Bio -->
                <div class="info-section" v-if="selectedCharacter.bio">
                  <h4 class="section-title">{{ t('characterGraph.characterPanel.bio') }}</h4>
                  <p class="character-bio">{{ selectedCharacter.bio }}</p>
                </div>

                <!-- Relationships -->
                <div class="info-section" v-if="Object.keys(selectedCharacter.relationships || {}).length > 0">
                  <h4 class="section-title">{{ t('characterGraph.characterPanel.relationships') }}</h4>
                  <ul class="relationships-list">
                    <li
                      v-for="(type, name) in selectedCharacter.relationships"
                      :key="name"
                      class="relationship-item"
                    >
                      <span class="relationship-name">{{ name }}</span>
                      <span class="relationship-type">{{ formatRelationshipType(type) }}</span>
                    </li>
                  </ul>
                </div>

                <!-- Aliases -->
                <div class="info-section" v-if="selectedCharacter.aliases?.length">
                  <h4 class="section-title">{{ t('characterGraph.characterPanel.aliases') }}</h4>
                  <div class="aliases-list">
                    <span v-for="alias in selectedCharacter.aliases" :key="alias" class="alias-tag">{{ alias }}</span>
                  </div>
                </div>

                <!-- Actions -->
                <div class="panel-actions">
                  <button class="btn btn-primary" @click="viewCharacterDetail">
                    {{ t('characterGraph.actions.viewFullProfile') }}
                  </button>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<style scoped>
.character-graph {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1400px;
  margin: 0 auto;
}

/* Header */
.graph-header {
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
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  line-height: var(--line-height-tight);
  margin-bottom: var(--space-1);
}

.page-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

/* Main Content */
.graph-main {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  min-height: 600px;
  overflow: hidden;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  gap: var(--space-4);
}

.loading-icon {
  color: var(--color-primary);
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: var(--font-size-lg);
  color: var(--color-text-secondary);
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  padding: var(--space-8);
  text-align: center;
}

.error-icon {
  color: var(--color-error);
  margin-bottom: var(--space-4);
}

.error-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.error-message {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 400px;
  margin-bottom: var(--space-6);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 600px;
  padding: var(--space-8);
  text-align: center;
}

.empty-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.empty-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  max-width: 400px;
  margin-bottom: var(--space-6);
}

/* Graph Content */
.graph-content {
  width: 100%;
  height: 100%;
  min-height: 600px;
}

.graph-visualization {
  width: 100%;
  height: 600px;
}

/* Character Panel Overlay */
.character-panel-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}

/* Character Panel */
.character-panel {
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  height: 100%;
  box-shadow: var(--shadow-xl);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

/* Panel Header */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-5);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-border-light);
}

.panel-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.panel-close {
  background: none;
  border: none;
  padding: var(--space-2);
  cursor: pointer;
  color: var(--color-text-tertiary);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-close:hover {
  background: var(--color-border);
  color: var(--color-text-primary);
}

/* Panel Content */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
}

.panel-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--color-text-secondary);
}

.spinning {
  animation: spin 1s linear infinite;
}

/* Character Details */
.character-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.character-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.character-avatar {
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-secondary) 100%);
  border-radius: var(--radius-full);
  color: white;
}

.character-name-section {
  flex: 1;
}

.character-name {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1) 0;
}

.character-mbti {
  display: inline-flex;
  padding: var(--space-1) var(--space-2);
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

/* Info Section */
.info-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.section-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.info-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) 0;
}

.info-row dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.info-row dd {
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  font-weight: var(--font-weight-medium);
}

/* Tier Badge */
.tier-badge {
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

/* Bio */
.character-bio {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  margin: 0;
}

/* Relationships List */
.relationships-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.relationship-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3);
  background: var(--color-border-light);
  border-radius: var(--radius-md);
}

.relationship-name {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.relationship-type {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  text-transform: capitalize;
}

/* Aliases */
.aliases-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.alias-tag {
  display: inline-flex;
  padding: var(--space-1) var(--space-3);
  background: var(--color-border-light);
  color: var(--color-text-secondary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
}

/* Panel Actions */
.panel-actions {
  display: flex;
  gap: var(--space-3);
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
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

.btn-primary {
  background: var(--color-primary);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
  transform: translateY(-1px);
}

/* Slide Transition */
.slide-enter-active,
.slide-leave-active {
  transition: opacity 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  opacity: 0;
}

.slide-enter-from .character-panel,
.slide-leave-to .character-panel {
  transform: translateX(100%);
}

/* Responsive */
@media (max-width: 768px) {
  .character-graph {
    padding: var(--space-4);
  }

  .page-title {
    font-size: var(--font-size-2xl);
  }

  .graph-visualization {
    height: 500px;
  }

  .character-panel {
    max-width: 100%;
  }
}

/* High contrast mode */
@media (prefers-contrast: high) {
  .character-panel {
    border-left: 2px solid var(--color-border);
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .loading-icon,
  .spinning {
    animation: none;
  }

  .character-panel {
    animation: none;
  }
}
</style>
