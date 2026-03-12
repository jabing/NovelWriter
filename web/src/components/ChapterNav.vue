<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Chapter } from '../types';

const { t } = useI18n();

const props = defineProps<{
  chapters: Chapter[];
  currentChapterId: string;
  projectId: string;
}>();

const emit = defineEmits<{
  (e: 'navigate', chapterId: string): void;
  (e: 'previous'): void;
  (e: 'next'): void;
}>();

// Auto-hide state
const isVisible = ref(true);
const lastScrollY = ref(0);
const hideTimeout = ref<ReturnType<typeof setTimeout> | null>(null);

// Current chapter index
const currentIndex = computed(() => {
  return props.chapters.findIndex(c => c.id === props.currentChapterId);
});

// Navigation state
const hasPrevious = computed(() => currentIndex.value > 0);
const hasNext = computed(() => currentIndex.value < props.chapters.length - 1);

// Current chapter
const currentChapter = computed(() => {
  return props.chapters[currentIndex.value];
});

// Progress text
const progressText = computed(() => {
  if (currentIndex.value === -1 || props.chapters.length === 0) return '';
  return `${currentIndex.value + 1} / ${props.chapters.length}`;
});

// Chapter options for dropdown
const chapterOptions = computed(() => {
  return props.chapters.map(chapter => ({
    value: chapter.id,
    label: `${chapter.number}. ${chapter.title}`
  }));
});

// Navigation handlers
const handlePrevious = (): void => {
  if (hasPrevious.value) {
    emit('previous');
    emit('navigate', props.chapters[currentIndex.value - 1].id);
  }
};

const handleNext = (): void => {
  if (hasNext.value) {
    emit('next');
    emit('navigate', props.chapters[currentIndex.value + 1].id);
  }
};

const handleSelect = (chapterId: string): void => {
  emit('navigate', chapterId);
};

// Auto-hide logic
const showNav = (): void => {
  isVisible.value = true;
  if (hideTimeout.value) {
    clearTimeout(hideTimeout.value);
  }
};

const scheduleHide = (): void => {
  hideTimeout.value = setTimeout(() => {
    isVisible.value = false;
  }, 3000);
};

const handleScroll = (): void => {
  showNav();
  scheduleHide();
};

const handleMouseMove = (): void => {
  showNav();
  scheduleHide();
};

// Lifecycle
onMounted(() => {
  window.addEventListener('scroll', handleScroll);
  window.addEventListener('mousemove', handleMouseMove);
  scheduleHide();
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  window.removeEventListener('mousemove', handleMouseMove);
  if (hideTimeout.value) {
    clearTimeout(hideTimeout.value);
  }
});
</script>

<template>
  <Transition name="nav-fade">
    <div 
      v-if="isVisible && chapters.length > 0"
      class="chapter-nav"
      @mouseenter="showNav"
      @mouseleave="scheduleHide"
    >
      <!-- Previous Button -->
      <button
        class="nav-btn nav-prev"
        :disabled="!hasPrevious"
        :title="t('chapter.previous')"
        @click="handlePrevious"
      >
        <span class="nav-icon">‹</span>
      </button>

      <!-- Chapter Selector -->
      <div class="chapter-selector">
        <select
          class="chapter-select"
          :value="currentChapterId"
          @change="handleSelect(($event.target as HTMLSelectElement).value)"
        >
          <option
            v-for="option in chapterOptions"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>

        <!-- Current chapter info on hover -->
        <div v-if="currentChapter" class="chapter-info">
          <span class="chapter-number">Ch. {{ currentChapter.number }}</span>
          <span class="chapter-title">{{ currentChapter.title }}</span>
        </div>
      </div>

      <!-- Progress Indicator -->
      <div class="progress-indicator">
        <span class="progress-text">{{ progressText }}</span>
        <div class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: `${((currentIndex + 1) / chapters.length) * 100}%` }"
          />
        </div>
      </div>

      <!-- Next Button -->
      <button
        class="nav-btn nav-next"
        :disabled="!hasNext"
        :title="t('chapter.next')"
        @click="handleNext"
      >
        <span class="nav-icon">›</span>
      </button>
    </div>
  </Transition>
</template>

<style scoped>
.chapter-nav {
  position: fixed;
  bottom: var(--space-6);
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-4);
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: var(--radius-xl);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 
    0 4px 24px rgba(0, 0, 0, 0.12),
    0 1px 2px rgba(0, 0, 0, 0.04);
  z-index: var(--z-sticky);
  transition: all var(--transition-base);
}

.chapter-nav:hover {
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.16),
    0 2px 4px rgba(0, 0, 0, 0.06);
}

/* Navigation Buttons */
.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-primary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-btn:hover:not(:disabled) {
  background: var(--color-border-light);
}

.nav-btn:active:not(:disabled) {
  transform: scale(0.95);
}

.nav-btn:disabled {
  color: var(--color-text-tertiary);
  cursor: not-allowed;
  opacity: 0.5;
}

.nav-icon {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
}

/* Chapter Selector */
.chapter-selector {
  position: relative;
  min-width: 160px;
}

.chapter-select {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  padding-right: var(--space-6);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%2386868B' d='M2.5 4.5L6 8L9.5 4.5'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 8px center;
  transition: all var(--transition-fast);
}

.chapter-select:hover {
  border-color: var(--color-primary);
}

.chapter-select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.chapter-info {
  display: none;
  position: absolute;
  bottom: 100%;
  left: 50%;
  transform: translateX(-50%);
  margin-bottom: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-lg);
  white-space: nowrap;
  z-index: 10;
}

.chapter-selector:hover .chapter-info {
  display: block;
}

.chapter-number {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
  margin-right: var(--space-2);
}

.chapter-title {
  font-size: var(--font-size-xs);
  color: var(--color-text-secondary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: inline-block;
  vertical-align: bottom;
}

/* Progress Indicator */
.progress-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-1);
  min-width: 60px;
}

.progress-text {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
}

.progress-bar {
  width: 100%;
  height: 3px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-base);
}

/* Transitions */
.nav-fade-enter-active,
.nav-fade-leave-active {
  transition: all var(--transition-base);
}

.nav-fade-enter-from,
.nav-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(20px);
}

/* Responsive */
@media (max-width: 640px) {
  .chapter-nav {
    bottom: var(--space-4);
    left: var(--space-4);
    right: var(--space-4);
    transform: none;
    width: auto;
  }

  .chapter-selector {
    flex: 1;
    min-width: auto;
  }

  .progress-indicator {
    min-width: 50px;
  }

  .chapter-info {
    display: none !important;
  }
}
</style>
