<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useProjectStore } from '@/stores/projectStore';
import {
  Document,
  Edit,
  Plus,
  MagicStick,
  Collection,
  Check,
  Loading,
  ArrowDown,
  Setting,
  Close
} from '@element-plus/icons-vue';
import type { Project, Chapter } from '@/types';
import { getChapters, createChapter, updateChapter } from '@/api/chapters';
import { generateChapterContent } from '@/api/writer';

const projectStore = useProjectStore();

// State
const projects = computed(() => projectStore.projectList);
const selectedProjectId = ref<string>('');
const chapters = ref<Chapter[]>([]);
const selectedChapterId = ref<string>('');
const isLoadingChapters = ref(false);
const isGenerating = ref(false);
const generatedContent = ref('');
const editedContent = ref('');
const isSaving = ref(false);

// Writing configuration
const writingConfig = ref({
  type: 'fantasy',
  style: 'balanced',
  wordCount: 3000,
  plotPoints: [] as string[]
});

const newPlotPoint = ref('');

// Genre options
const genreOptions = [
  { value: 'fantasy', label: '奇幻 (Fantasy)', icon: '🐉' },
  { value: 'scifi', label: '科幻 (Sci-Fi)', icon: '🚀' },
  { value: 'romance', label: '浪漫 (Romance)', icon: '💕' },
  { value: 'mystery', label: '悬疑 (Mystery)', icon: '🔍' },
  { value: 'thriller', label: '惊悚 (Thriller)', icon: '⚡' },
  { value: 'horror', label: '恐怖 (Horror)', icon: '👻' },
  { value: 'historical', label: '历史 (Historical)', icon: '🏛️' },
  { value: 'wuxia', label: '武侠 (Wuxia)', icon: '⚔️' },
  { value: 'xianxia', label: '仙侠 (Xianxia)', icon: '☁️' },
  { value: 'urban', label: '都市 (Urban)', icon: '🏙️' }
];

const styleOptions = [
  { value: 'light', label: '轻松愉快', description: '轻松幽默的叙事风格' },
  { value: 'balanced', label: '平衡自然', description: '自然流畅的叙述方式' },
  { value: 'serious', label: '严肃深沉', description: '深沉内敛的文学风格' },
  { value: 'suspenseful', label: '悬疑紧张', description: '紧张刺激的悬疑氛围' },
  { value: 'poetic', label: '诗意优美', description: '优美抒情的文学表达' }
];

const wordCountOptions = [
  { value: 1500, label: '短篇 (1500字)', description: '适合短篇章节' },
  { value: 3000, label: '标准 (3000字)', description: '常规章节长度' },
  { value: 5000, label: '长章 (5000字)', description: '较长的章节内容' },
  { value: 8000, label: '长篇 (8000字)', description: '详细的章节描写' }
];

// Computed
const selectedProject = computed<Project | undefined>(() => {
  return projects.value.find(p => p.id === selectedProjectId.value);
});

const selectedChapter = computed<Chapter | undefined>(() => {
  return chapters.value.find(c => c.id === selectedChapterId.value);
});

const canGenerate = computed(() => {
  return selectedProjectId.value && 
         selectedChapterId.value && 
         writingConfig.value.type &&
         !isGenerating.value;
});

const hasContent = computed(() => {
  return editedContent.value.trim().length > 0;
});

const wordCount = computed(() => {
  return editedContent.value.trim().split(/\s+/).filter(w => w.length > 0).length;
});

// Methods
async function loadChapters() {
  if (!selectedProjectId.value) {
    chapters.value = [];
    return;
  }
  
  isLoadingChapters.value = true;
  try {
    chapters.value = await getChapters(selectedProjectId.value);
    // Auto-select first chapter if exists
    if (chapters.value.length > 0 && !selectedChapterId.value) {
      const firstChapter = chapters.value[0];
      if (firstChapter) {
        selectedChapterId.value = firstChapter.id;
        editedContent.value = firstChapter.content || '';
      }
    }
  } catch (error) {
    console.error('Failed to load chapters:', error);
  } finally {
    isLoadingChapters.value = false;
  }
}

async function createNewChapter() {
  if (!selectedProjectId.value) return;
  
  const chapterNumber = chapters.value.length + 1;
  const title = `第${chapterNumber}章`;
  
  try {
    const newChapter = await createChapter(selectedProjectId.value, {
      number: chapterNumber,
      title,
      status: 'draft'
    });
    chapters.value.push(newChapter);
    selectedChapterId.value = newChapter.id;
    editedContent.value = '';
    generatedContent.value = '';
  } catch (error) {
    console.error('Failed to create chapter:', error);
  }
}

function selectChapter(chapter: Chapter) {
  selectedChapterId.value = chapter.id;
  editedContent.value = chapter.content || '';
  generatedContent.value = '';
}

function addPlotPoint() {
  const point = newPlotPoint.value.trim();
  if (point && !writingConfig.value.plotPoints.includes(point)) {
    writingConfig.value.plotPoints.push(point);
    newPlotPoint.value = '';
  }
}

function removePlotPoint(index: number) {
  writingConfig.value.plotPoints.splice(index, 1);
}

async function generateContent() {
  if (!canGenerate.value) return;
  
  isGenerating.value = true;
  generatedContent.value = '';
  
  try {
    const result = await generateChapterContent({
      project_id: selectedProjectId.value,
      chapter_id: selectedChapterId.value,
      genre: writingConfig.value.type,
      style: writingConfig.value.style,
      word_count: writingConfig.value.wordCount,
      plot_points: writingConfig.value.plotPoints
    });
    
    generatedContent.value = result.content;
    editedContent.value = result.content;
  } catch (error) {
    console.error('Failed to generate content:', error);
  } finally {
    isGenerating.value = false;
  }
}

async function saveChapter() {
  if (!selectedChapterId.value || !hasContent.value) return;
  
  isSaving.value = true;
  try {
    await updateChapter(selectedChapterId.value, {
      content: editedContent.value,
      word_count: wordCount.value,
      status: 'completed'
    });
    
    // Update local chapter data
    const chapter = chapters.value.find(c => c.id === selectedChapterId.value);
    if (chapter) {
      chapter.content = editedContent.value;
      chapter.word_count = wordCount.value;
      chapter.status = 'completed';
    }
  } catch (error) {
    console.error('Failed to save chapter:', error);
  } finally {
    isSaving.value = false;
  }
}

function insertGeneratedContent() {
  if (generatedContent.value) {
    editedContent.value = generatedContent.value;
  }
}

// Watch for project changes
watch(selectedProjectId, () => {
  selectedChapterId.value = '';
  editedContent.value = '';
  generatedContent.value = '';
  loadChapters();
});

// Initialize
onMounted(() => {
  projectStore.fetchProjects();
});
</script>

<template>
  <div class="writing-page">
    <!-- Page Header -->
    <header class="page-header">
      <div class="header-content">
        <div class="header-text">
          <h1 class="page-title">写作工作台</h1>
          <p class="page-subtitle">AI辅助创作，让灵感自由流淌</p>
        </div>
      </div>
    </header>

    <div class="writing-layout">
      <!-- Left Sidebar: Project & Chapters -->
      <aside class="sidebar-panel">
        <!-- Project Selector -->
        <div class="panel-section">
          <h3 class="panel-title">
            <el-icon><Collection /></el-icon>
            选择项目
          </h3>
          <select v-model="selectedProjectId" class="project-select">
            <option value="">请选择项目...</option>
            <option 
              v-for="project in projects" 
              :key="project.id" 
              :value="project.id"
            >
              {{ project.title }}
            </option>
          </select>
          <div v-if="selectedProject" class="project-info">
            <span class="genre-badge">{{ selectedProject?.genre }}</span>
            <span class="progress-text">{{ selectedProject?.completed_chapters }}/{{ selectedProject?.target_chapters }} 章</span>
          </div>
        </div>

        <!-- Chapter List -->
        <div class="panel-section">
          <div class="section-header">
            <h3 class="panel-title">
              <el-icon><Document /></el-icon>
              章节列表
            </h3>
            <button 
              v-if="selectedProjectId"
              class="btn-icon" 
              @click="createNewChapter"
              title="创建新章节"
            >
              <el-icon><Plus /></el-icon>
            </button>
          </div>
          
          <div v-if="isLoadingChapters" class="loading-chapters">
            <div v-for="i in 3" :key="i" class="skeleton-chapter"></div>
          </div>
          
          <div v-else-if="chapters.length === 0" class="empty-chapters">
            <p v-if="selectedProjectId">暂无章节，点击 + 创建</p>
            <p v-else>请先选择项目</p>
          </div>
          
          <ul v-else class="chapter-list">
            <li 
              v-for="chapter in chapters" 
              :key="chapter.id"
              :class="['chapter-item', { active: chapter.id === selectedChapterId }]"
              @click="selectChapter(chapter)"
            >
              <span class="chapter-number">{{ chapter.number }}</span>
              <div class="chapter-info">
                <span class="chapter-title">{{ chapter.title }}</span>
                <span :class="['chapter-status', chapter.status]">
                  {{ chapter.status === 'completed' ? '已完成' : 
                     chapter.status === 'in_progress' ? '进行中' : '草稿' }}
                </span>
              </div>
              <span class="chapter-words">{{ chapter.word_count || 0 }}字</span>
            </li>
          </ul>
        </div>
      </aside>

      <!-- Center: Configuration -->
      <div class="config-panel">
        <h3 class="panel-title">
          <el-icon><Setting /></el-icon>
          写作配置
        </h3>

        <!-- Genre Selection -->
        <div class="config-group">
          <label class="config-label">作品类型</label>
          <div class="genre-grid">
            <button
              v-for="genre in genreOptions"
              :key="genre.value"
              :class="['genre-btn', { active: writingConfig.type === genre.value }]"
              @click="writingConfig.type = genre.value"
            >
              <span class="genre-icon">{{ genre.icon }}</span>
              <span class="genre-label">{{ genre.label }}</span>
            </button>
          </div>
        </div>

        <!-- Style Selection -->
        <div class="config-group">
          <label class="config-label">写作风格</label>
          <div class="style-list">
            <button
              v-for="style in styleOptions"
              :key="style.value"
              :class="['style-btn', { active: writingConfig.style === style.value }]"
              @click="writingConfig.style = style.value"
            >
              <span class="style-name">{{ style.label }}</span>
              <span class="style-desc">{{ style.description }}</span>
            </button>
          </div>
        </div>

        <!-- Word Count -->
        <div class="config-group">
          <label class="config-label">目标字数</label>
          <div class="wordcount-list">
            <button
              v-for="option in wordCountOptions"
              :key="option.value"
              :class="['wordcount-btn', { active: writingConfig.wordCount === option.value }]"
              @click="writingConfig.wordCount = option.value"
            >
              <span class="wordcount-label">{{ option.label }}</span>
              <span class="wordcount-desc">{{ option.description }}</span>
            </button>
          </div>
        </div>

        <!-- Plot Points -->
        <div class="config-group">
          <label class="config-label">关键情节点</label>
          <div class="plotpoints-input">
            <input
              v-model="newPlotPoint"
              type="text"
              class="plot-input"
              placeholder="输入情节点，按回车添加..."
              @keypress.enter="addPlotPoint"
            />
            <button class="btn btn-secondary" @click="addPlotPoint">
              <el-icon><Plus /></el-icon>
              添加
            </button>
          </div>
          <div v-if="writingConfig.plotPoints.length > 0" class="plotpoints-list">
            <span 
              v-for="(point, index) in writingConfig.plotPoints" 
              :key="index"
              class="plot-tag"
            >
              {{ point }}
              <button class="plot-remove" @click="removePlotPoint(index)">
                <el-icon><Close /></el-icon>
              </button>
            </span>
          </div>
        </div>

        <!-- Generate Button -->
        <button 
          :class="['btn btn-generate', { 'btn-loading': isGenerating }]"
          :disabled="!canGenerate"
          @click="generateContent"
        >
          <el-icon v-if="isGenerating" class="spin-icon"><Loading /></el-icon>
          <el-icon v-else><MagicStick /></el-icon>
          {{ isGenerating ? 'AI正在创作中...' : '开始AI生成' }}
        </button>
      </div>

      <!-- Right: Editor -->
      <div class="editor-panel">
        <div class="editor-header">
          <div class="editor-title">
            <el-icon><Edit /></el-icon>
            <span v-if="selectedChapter">{{ selectedChapter.title }}</span>
            <span v-else>编辑器</span>
          </div>
          <div class="editor-stats">
            <span class="word-stat">{{ wordCount }} 字</span>
            <button 
              class="btn btn-primary"
              :disabled="!hasContent || isSaving"
              @click="saveChapter"
            >
              <el-icon v-if="isSaving" class="spin-icon"><Loading /></el-icon>
              <el-icon v-else><Check /></el-icon>
              {{ isSaving ? '保存中...' : '保存章节' }}
            </button>
          </div>
        </div>

        <!-- Generated Content Preview -->
        <div v-if="generatedContent && generatedContent !== editedContent" class="generated-preview">
          <div class="preview-header">
            <span class="preview-title">AI生成的内容</span>
            <button class="btn btn-secondary btn-sm" @click="insertGeneratedContent">
              <el-icon><ArrowDown /></el-icon>
              使用此内容
            </button>
          </div>
          <div class="preview-content">{{ generatedContent.substring(0, 200) }}...</div>
        </div>

        <!-- Text Editor -->
        <textarea
          v-model="editedContent"
          class="editor-textarea"
          :placeholder="selectedChapterId ? '开始写作...' : '请先选择一个章节'"
          :disabled="!selectedChapterId"
        ></textarea>
      </div>
    </div>
  </div>
</template>

<style scoped>
.writing-page {
  min-height: 100%;
  padding: var(--space-6);
  max-width: 1600px;
  margin: 0 auto;
  animation: fadeIn var(--transition-slow);
}

/* Header */
.page-header {
  margin-bottom: var(--space-6);
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

/* Layout */
.writing-layout {
  display: grid;
  grid-template-columns: 280px 320px 1fr;
  gap: var(--space-6);
  min-height: calc(100vh - 200px);
}

/* Panels */
.sidebar-panel,
.config-panel,
.editor-panel {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

.panel-section {
  padding: var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}

.panel-section:last-child {
  border-bottom: none;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.section-header .panel-title {
  margin-bottom: 0;
}

/* Project Selector */
.project-select {
  width: 100%;
  height: 40px;
  padding: 0 var(--space-3);
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.project-select:focus {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
}

.project-info {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
  flex-wrap: wrap;
}

.genre-badge {
  padding: var(--space-1) var(--space-2);
  background: var(--color-primary-muted);
  color: var(--color-primary);
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: var(--radius-sm);
}

.progress-text {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Chapter List */
.loading-chapters {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.skeleton-chapter {
  height: 48px;
  background: linear-gradient(
    90deg,
    var(--color-bg-tertiary) 25%,
    var(--color-bg-secondary) 50%,
    var(--color-bg-tertiary) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: var(--radius-md);
}

.empty-chapters {
  padding: var(--space-4);
  text-align: center;
  color: var(--color-text-tertiary);
  font-size: var(--font-size-body-sm);
}

.chapter-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.chapter-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid transparent;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chapter-item:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border);
}

.chapter-item.active {
  background: var(--color-primary-muted);
  border-color: var(--color-primary-light);
}

.chapter-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.chapter-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chapter-title {
  font-size: var(--font-size-body-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chapter-status {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chapter-status.draft {
  color: var(--color-text-tertiary);
}

.chapter-status.in_progress {
  color: var(--color-warning);
}

.chapter-status.completed {
  color: var(--color-success);
}

.chapter-words {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  flex-shrink: 0;
}

/* Config Panel */
.config-panel {
  padding: var(--space-4);
  overflow-y: auto;
}

.config-group {
  margin-bottom: var(--space-5);
}

.config-label {
  display: block;
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-secondary);
  margin-bottom: var(--space-3);
}

/* Genre Grid */
.genre-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-2);
}

.genre-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-2);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.genre-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-focus);
}

.genre-btn.active {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
}

.genre-icon {
  font-size: 1.5rem;
}

.genre-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--color-text-primary);
}

/* Style List */
.style-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.style-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
}

.style-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-focus);
}

.style-btn.active {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
}

.style-name {
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.style-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Word Count */
.wordcount-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.wordcount-btn {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-2) var(--space-3);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.wordcount-btn:hover {
  background: var(--color-bg-tertiary);
  border-color: var(--color-border-focus);
}

.wordcount-btn.active {
  background: var(--color-primary-muted);
  border-color: var(--color-primary);
}

.wordcount-label {
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-primary);
}

.wordcount-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

/* Plot Points */
.plotpoints-input {
  display: flex;
  gap: var(--space-2);
  margin-bottom: var(--space-2);
}

.plot-input {
  flex: 1;
  height: 36px;
  padding: 0 var(--space-3);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-primary);
  background: var(--color-bg-input);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  outline: none;
  transition: all var(--transition-fast);
}

.plot-input:focus {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 2px var(--color-primary-muted);
}

.plotpoints-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.plot-tag {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: var(--color-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
  border-radius: var(--radius-md);
}

.plot-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  transition: color var(--transition-fast);
}

.plot-remove:hover {
  color: white;
}

/* Generate Button */
.btn-generate {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-hover) 100%);
  color: white;
  font-size: var(--font-size-body);
  font-weight: 600;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-base);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  box-shadow: var(--shadow-md);
}

.btn-generate:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.btn-generate:disabled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-disabled);
  cursor: not-allowed;
  box-shadow: none;
}

/* Editor Panel */
.editor-panel {
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-secondary);
  border-bottom: 1px solid var(--color-border);
}

.editor-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-serif);
  font-size: var(--font-size-body);
  font-weight: 600;
  color: var(--color-text-primary);
}

.editor-stats {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.word-stat {
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Generated Preview */
.generated-preview {
  padding: var(--space-3) var(--space-4);
  background: linear-gradient(135deg, rgba(201, 162, 39, 0.1) 0%, rgba(201, 162, 39, 0.05) 100%);
  border-bottom: 1px solid var(--color-border);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
}

.preview-title {
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-accent-gold);
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.preview-content {
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
  line-height: 1.6;
  font-style: italic;
}

/* Text Editor */
.editor-textarea {
  flex: 1;
  width: 100%;
  padding: var(--space-4);
  font-family: var(--font-serif);
  font-size: var(--font-size-body);
  line-height: 1.8;
  color: var(--color-text-primary);
  background: var(--color-bg-primary);
  border: none;
  outline: none;
  resize: none;
  min-height: 400px;
}

.editor-textarea::placeholder {
  color: var(--color-text-placeholder);
}

.editor-textarea:disabled {
  background: var(--color-bg-secondary);
  cursor: not-allowed;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: none;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

.btn-primary:disabled {
  background: var(--color-bg-tertiary);
  color: var(--color-text-disabled);
  cursor: not-allowed;
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-border-focus);
}

.btn-sm {
  padding: var(--space-1) var(--space-2);
  font-size: 0.75rem;
}

.btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  padding: 0;
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn-icon:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

/* Loading Animation */
.spin-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 1200px) {
  .writing-layout {
    grid-template-columns: 260px 280px 1fr;
  }
}

@media (max-width: 992px) {
  .writing-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto 1fr;
  }
  
  .sidebar-panel,
  .config-panel {
    max-height: 400px;
    overflow-y: auto;
  }
}

@media (max-width: 768px) {
  .writing-page {
    padding: var(--space-4);
  }
  
  .page-title {
    font-size: var(--font-size-h3);
  }
  
  .genre-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
