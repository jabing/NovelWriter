<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Chapter, ChapterStatus } from '../types';

const { t } = useI18n();

const props = defineProps<{
  chapters: Chapter[];
  projectId: string;
}>();

const emit = defineEmits<{
  (e: 'edit', chapter: Chapter): void;
  (e: 'read', chapter: Chapter): void;
  (e: 'delete', chapter: Chapter): void;
  (e: 'publish', chapter: Chapter): void;
  (e: 'reorder', chapters: Chapter[]): void;
}>();

const statusConfig: Record<ChapterStatus, { class: string; icon: string }> = {
  draft: { class: 'badge-draft', icon: '○' },
  in_progress: { class: 'badge-progress', icon: '◐' },
  completed: { class: 'badge-success', icon: '●' },
  published: { class: 'badge-published', icon: '✓' }
};

const getStatusLabel = (status: ChapterStatus): string => {
  const labels: Record<ChapterStatus, string> = {
    draft: t('chapter.draft'),
    in_progress: t('chapter.inProgress'),
    completed: t('chapter.completed'),
    published: t('chapter.published')
  };
  return labels[status];
};

const formatWordCount = (count: number): string => {
  return count.toLocaleString();
};

const handleEdit = (chapter: Chapter): void => {
  emit('edit', chapter);
};

const handleRead = (chapter: Chapter): void => {
  emit('read', chapter);
};

const handleDelete = (chapter: Chapter): void => {
  emit('delete', chapter);
};

const handlePublish = (chapter: Chapter): void => {
  emit('publish', chapter);
};
</script>

<template>
  <div class="chapter-list">
    <!-- Empty State -->
    <div v-if="chapters.length === 0" class="empty-state">
      <div class="empty-state-icon">📖</div>
      <div class="empty-state-title">{{ t('common.noData') }}</div>
      <div class="empty-state-description">
        {{ t('chapter.create') }} - Start writing your story
      </div>
    </div>

    <!-- Chapter List -->
    <TransitionGroup v-else name="chapter-list" tag="div" class="chapters-container">
      <div
        v-for="chapter in chapters"
        :key="chapter.id"
        class="chapter-item"
        tabindex="0"
        @keydown.enter="handleRead(chapter)"
      >
        <!-- Chapter Number -->
        <div class="chapter-number">{{ chapter.number }}</div>

        <!-- Chapter Content -->
        <div class="chapter-content">
          <div class="chapter-header">
            <h3 class="chapter-title">{{ chapter.title }}</h3>
            <span
              class="chapter-status"
              :class="statusConfig[chapter.status].class"
            >
              <span class="status-icon">{{ statusConfig[chapter.status].icon }}</span>
              {{ getStatusLabel(chapter.status) }}
            </span>
          </div>

          <div class="chapter-meta">
            <span class="meta-item">
              <span class="meta-icon">📝</span>
              {{ formatWordCount(chapter.word_count) }} {{ t('chapter.wordCount') }}
            </span>
            <span class="meta-divider">•</span>
            <span class="meta-item">
              <span class="meta-icon">📅</span>
              {{ new Date(chapter.updated_at).toLocaleDateString() }}
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div class="chapter-actions">
          <button
            class="action-btn action-read"
            :title="t('common.edit')"
            @click.stop="handleRead(chapter)"
          >
            <span class="action-icon">▶</span>
          </button>
          <button
            class="action-btn action-edit"
            :title="t('common.edit')"
            @click.stop="handleEdit(chapter)"
          >
            <span class="action-icon">✎</span>
          </button>
          <button
            class="action-btn action-publish"
            :title="t('publish.publishNow')"
            @click.stop="handlePublish(chapter)"
          >
            <span class="action-icon">↑</span>
          </button>
          <button
            class="action-btn action-delete"
            :title="t('common.delete')"
            @click.stop="handleDelete(chapter)"
          >
            <span class="action-icon">×</span>
          </button>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.chapter-list {
  width: 100%;
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
  font-size: 3.5rem;
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
  opacity: 0.6;
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
  max-width: 280px;
}

/* Chapters Container */
.chapters-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

/* Chapter Item */
.chapter-item {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border-light);
  cursor: pointer;
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.chapter-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--gradient-primary);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.chapter-item:hover {
  background: var(--color-border-light);
  border-color: var(--color-border);
  transform: translateX(2px);
}

.chapter-item:hover::before {
  opacity: 1;
}

.chapter-item:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Chapter Number */
.chapter-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: var(--gradient-primary);
  color: white;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

/* Chapter Content */
.chapter-content {
  flex: 1;
  min-width: 0;
}

.chapter-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-1);
}

.chapter-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chapter-meta {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.meta-icon {
  font-size: var(--font-size-xs);
}

.meta-divider {
  color: var(--color-text-tertiary);
}

/* Status Badges */
.chapter-status {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: 2px var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-icon {
  font-size: 0.65rem;
}

.badge-draft {
  background: rgba(142, 142, 147, 0.12);
  color: #8E8E93;
}

.badge-progress {
  background: rgba(255, 149, 0, 0.12);
  color: var(--color-warning);
}

.badge-success {
  background: rgba(52, 199, 89, 0.12);
  color: var(--color-success);
}

.badge-published {
  background: rgba(0, 122, 255, 0.12);
  color: var(--color-primary);
}

/* Actions */
.chapter-actions {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.chapter-item:hover .chapter-actions,
.chapter-item:focus-within .chapter-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--color-border);
  color: var(--color-text-primary);
}

.action-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.action-icon {
  font-size: var(--font-size-sm);
  line-height: 1;
}

.action-read:hover {
  background: rgba(0, 122, 255, 0.12);
  color: var(--color-primary);
}

.action-edit:hover {
  background: rgba(52, 199, 89, 0.12);
  color: var(--color-success);
}

.action-publish:hover {
  background: rgba(88, 86, 214, 0.12);
  color: var(--color-secondary);
}

.action-delete:hover {
  background: rgba(255, 59, 48, 0.12);
  color: var(--color-error);
}

/* Transitions */
.chapter-list-enter-active,
.chapter-list-leave-active {
  transition: all var(--transition-base);
}

.chapter-list-enter-from,
.chapter-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.chapter-list-move {
  transition: transform var(--transition-base);
}

/* Responsive */
@media (max-width: 640px) {
  .chapter-actions {
    opacity: 1;
  }

  .chapter-meta {
    flex-wrap: wrap;
    gap: var(--space-1);
  }

  .meta-divider {
    display: none;
  }
}
</style>
