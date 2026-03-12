<script setup lang="ts">
import { ref, computed, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useProjectStore } from '@/stores/projectStore';
import type { CreateProjectPayload } from '@/types';

const { t } = useI18n();
const projectStore = useProjectStore();

// Emits
const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'complete', projectId: string): void;
}>();

// Form state
const currentStep = ref(0);
const isSubmitting = ref(false);
const stepErrors = ref<Record<string, string>>({});

interface FormData {
  title: string;
  genre: string;
  description: string;
  premise: string;
  themes: string[];
  structure: 'three-act' | 'five-act' | 'heros-journey';
  targetWords: number;
  targetChapters: number;
}

const formData = reactive<FormData>({
  title: '',
  genre: '',
  description: '',
  premise: '',
  themes: [],
  structure: 'three-act',
  targetWords: 80000,
  targetChapters: 20
});

// New theme input
const newTheme = ref('');

// Step configuration
const steps = computed(() => [
  { key: 'basicInfo', icon: '📝' },
  { key: 'premise', icon: '💡' },
  { key: 'structure', icon: '🏗️' },
  { key: 'targets', icon: '🎯' }
]);

const totalSteps = computed(() => steps.value.length);

// Genre options
const genres = computed(() => [
  { value: 'fantasy', label: t('wizard.genre.fantasy') },
  { value: 'scifi', label: t('wizard.genre.scifi') },
  { value: 'romance', label: t('wizard.genre.romance') },
  { value: 'mystery', label: t('wizard.genre.mystery') },
  { value: 'thriller', label: t('wizard.genre.thriller') },
  { value: 'horror', label: t('wizard.genre.horror') },
  { value: 'literary', label: t('wizard.genre.literary') },
  { value: 'historical', label: t('wizard.genre.historical') },
  { value: 'adventure', label: t('wizard.genre.adventure') },
  { value: 'youngAdult', label: t('wizard.genre.youngAdult') }
]);

// Structure options
const structures = computed(() => [
  { 
    value: 'three-act', 
    title: t('wizard.field.threeAct'),
    description: t('wizard.field.threeActDesc')
  },
  { 
    value: 'five-act', 
    title: t('wizard.field.fiveAct'),
    description: t('wizard.field.fiveActDesc')
  },
  { 
    value: 'heros-journey', 
    title: t('wizard.field.herosJourney'),
    description: t('wizard.field.herosJourneyDesc')
  }
]);

// Word count presets
const wordPresets = [
  { value: 40000, label: '40K - Novella' },
  { value: 60000, label: '60K - Short Novel' },
  { value: 80000, label: '80K - Standard Novel' },
  { value: 100000, label: '100K - Long Novel' },
  { value: 120000, label: '120K - Epic' }
];

// Chapter presets
const chapterPresets = [
  { value: 10, label: '10 Chapters' },
  { value: 20, label: '20 Chapters' },
  { value: 30, label: '30 Chapters' },
  { value: 40, label: '40 Chapters' },
  { value: 50, label: '50 Chapters' }
];

// Validation
const validateStep = (step: number): boolean => {
  stepErrors.value = {};
  
  if (step === 0) {
    if (!formData.title.trim()) {
      stepErrors.value.title = t('wizard.error.titleRequired');
      return false;
    }
    if (formData.title.trim().length < 2) {
      stepErrors.value.title = t('wizard.error.titleMinLength');
      return false;
    }
    if (!formData.genre) {
      stepErrors.value.genre = t('wizard.error.genreRequired');
      return false;
    }
  }
  
  return true;
};

// Navigation
const canGoNext = computed(() => {
  if (currentStep.value === 0) {
    return formData.title.trim().length >= 2 && formData.genre !== '';
  }
  return true;
});

const isLastStep = computed(() => currentStep.value === totalSteps.value - 1);

const goToNext = () => {
  if (!validateStep(currentStep.value)) return;
  
  if (currentStep.value < totalSteps.value - 1) {
    currentStep.value++;
  }
};

const goToPrevious = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
};

const goToStep = (step: number) => {
  // Only allow going back or to completed steps
  if (step <= currentStep.value || validateStep(currentStep.value)) {
    currentStep.value = step;
  }
};

// Theme management
const addTheme = () => {
  const theme = newTheme.value.trim();
  if (theme && !formData.themes.includes(theme)) {
    formData.themes.push(theme);
  }
  newTheme.value = '';
};

const removeTheme = (index: number) => {
  formData.themes.splice(index, 1);
};

// Submit
const handleSubmit = async () => {
  if (!validateStep(currentStep.value)) return;
  
  isSubmitting.value = true;
  
  const payload: CreateProjectPayload = {
    title: formData.title,
    genre: formData.genre,
    premise: formData.premise,
    themes: formData.themes,
    story_structure: formData.structure,
    target_words: formData.targetWords,
    target_chapters: formData.targetChapters
  };
  
  try {
    const project = await projectStore.createProject(payload);
    if (project) {
      emit('complete', project.id);
    }
  } catch (error) {
    console.error('Failed to create project:', error);
  } finally {
    isSubmitting.value = false;
  }
};

const handleClose = () => {
  emit('close');
};
</script>

<template>
  <div class="wizard-overlay" @click.self="handleClose">
    <div class="wizard-container">
      <!-- Header -->
      <header class="wizard-header">
        <h2 class="wizard-title">{{ t('wizard.title') }}</h2>
        <button class="close-button" @click="handleClose" :aria-label="t('common.close')">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path d="M1 1L13 13M1 13L13 1" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </header>

      <!-- Stepper -->
      <nav class="stepper" aria-label="Progress">
        <div class="stepper-track">
          <div 
            class="stepper-progress" 
            :style="{ width: `${(currentStep / (totalSteps - 1)) * 100}%` }"
          />
        </div>
        <ol class="stepper-steps">
          <li 
            v-for="(step, index) in steps" 
            :key="step.key"
            class="stepper-step"
            :class="{ 
              'active': index === currentStep,
              'completed': index < currentStep 
            }"
          >
            <button 
              class="stepper-button"
              @click="goToStep(index)"
              :disabled="index > currentStep"
              :aria-current="index === currentStep ? 'step' : undefined"
            >
              <span class="stepper-icon">{{ step.icon }}</span>
              <span class="stepper-label">{{ t(`wizard.${step.key}.title`) }}</span>
            </button>
          </li>
        </ol>
      </nav>

      <!-- Step Content -->
      <div class="wizard-content">
        <Transition name="slide-fade" mode="out-in">
          <!-- Step 1: Basic Info -->
          <div v-if="currentStep === 0" key="basicInfo" class="step-panel">
            <div class="step-header">
              <h3 class="step-title">{{ t('wizard.basicInfo.title') }}</h3>
              <p class="step-description">{{ t('wizard.basicInfo.description') }}</p>
            </div>
            
            <div class="form-group">
              <label class="form-label" for="title">
                {{ t('wizard.field.title') }}
                <span class="required">*</span>
              </label>
              <input 
                id="title"
                v-model="formData.title"
                type="text"
                class="form-input"
                :class="{ 'error': stepErrors.title }"
                :placeholder="t('wizard.field.titlePlaceholder')"
                autofocus
              />
              <span v-if="stepErrors.title" class="error-message">
                {{ stepErrors.title }}
              </span>
            </div>

            <div class="form-group">
              <label class="form-label" for="genre">
                {{ t('wizard.field.genre') }}
                <span class="required">*</span>
              </label>
              <select 
                id="genre"
                v-model="formData.genre"
                class="form-select"
                :class="{ 'error': stepErrors.genre }"
              >
                <option value="" disabled>{{ t('wizard.field.genrePlaceholder') }}</option>
                <option v-for="g in genres" :key="g.value" :value="g.value">
                  {{ g.label }}
                </option>
              </select>
              <span v-if="stepErrors.genre" class="error-message">
                {{ stepErrors.genre }}
              </span>
            </div>

            <div class="form-group">
              <label class="form-label" for="description">
                {{ t('wizard.field.description') }}
              </label>
              <textarea 
                id="description"
                v-model="formData.description"
                class="form-textarea"
                :placeholder="t('wizard.field.descriptionPlaceholder')"
                rows="3"
              />
            </div>
          </div>

          <!-- Step 2: Premise & Themes -->
          <div v-else-if="currentStep === 1" key="premise" class="step-panel">
            <div class="step-header">
              <h3 class="step-title">{{ t('wizard.premise.title') }}</h3>
              <p class="step-description">{{ t('wizard.premise.description') }}</p>
            </div>
            
            <div class="form-group">
              <label class="form-label" for="premise">
                {{ t('wizard.field.premise') }}
              </label>
              <textarea 
                id="premise"
                v-model="formData.premise"
                class="form-textarea"
                :placeholder="t('wizard.field.premisePlaceholder')"
                rows="4"
              />
            </div>

            <div class="form-group">
              <label class="form-label" for="themes">
                {{ t('wizard.field.themes') }}
              </label>
              <div class="theme-input-wrapper">
                <input 
                  id="themes"
                  v-model="newTheme"
                  type="text"
                  class="form-input"
                  :placeholder="t('wizard.field.themesPlaceholder')"
                  @keydown.enter.prevent="addTheme"
                />
              </div>
              <div v-if="formData.themes.length > 0" class="theme-tags">
                <span 
                  v-for="(theme, index) in formData.themes" 
                  :key="index"
                  class="theme-tag"
                >
                  {{ theme }}
                  <button 
                    class="theme-tag-remove"
                    @click="removeTheme(index)"
                    :aria-label="t('common.delete')"
                  >
                    <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
                      <path d="M1 1L9 9M1 9L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                  </button>
                </span>
              </div>
            </div>
          </div>

          <!-- Step 3: Story Structure -->
          <div v-else-if="currentStep === 2" key="structure" class="step-panel">
            <div class="step-header">
              <h3 class="step-title">{{ t('wizard.structure.title') }}</h3>
              <p class="step-description">{{ t('wizard.structure.description') }}</p>
            </div>
            
            <div class="structure-options">
              <label 
                v-for="s in structures" 
                :key="s.value"
                class="structure-option"
                :class="{ 'selected': formData.structure === s.value }"
              >
                <input 
                  type="radio"
                  :value="s.value"
                  v-model="formData.structure"
                  class="structure-radio"
                />
                <div class="structure-content">
                  <span class="structure-title">{{ s.title }}</span>
                  <span class="structure-desc">{{ s.description }}</span>
                </div>
                <span class="structure-check">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8L6.5 11.5L13 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
              </label>
            </div>
          </div>

          <!-- Step 4: Targets -->
          <div v-else-if="currentStep === 3" key="targets" class="step-panel">
            <div class="step-header">
              <h3 class="step-title">{{ t('wizard.targets.title') }}</h3>
              <p class="step-description">{{ t('wizard.targets.description') }}</p>
            </div>
            
            <div class="form-group">
              <label class="form-label">{{ t('wizard.field.targetWords') }}</label>
              <div class="target-presets">
                <button 
                  v-for="preset in wordPresets"
                  :key="preset.value"
                  class="preset-button"
                  :class="{ 'selected': formData.targetWords === preset.value }"
                  @click="formData.targetWords = preset.value"
                >
                  {{ preset.label }}
                </button>
              </div>
              <div class="custom-input">
                <input 
                  type="number"
                  v-model.number="formData.targetWords"
                  class="form-input"
                  min="10000"
                  max="500000"
                  step="10000"
                />
                <span class="input-suffix">words</span>
              </div>
            </div>

            <div class="form-group">
              <label class="form-label">{{ t('wizard.field.targetChapters') }}</label>
              <div class="target-presets">
                <button 
                  v-for="preset in chapterPresets"
                  :key="preset.value"
                  class="preset-button"
                  :class="{ 'selected': formData.targetChapters === preset.value }"
                  @click="formData.targetChapters = preset.value"
                >
                  {{ preset.label }}
                </button>
              </div>
              <div class="custom-input">
                <input 
                  type="number"
                  v-model.number="formData.targetChapters"
                  class="form-input"
                  min="1"
                  max="100"
                  step="1"
                />
                <span class="input-suffix">chapters</span>
              </div>
            </div>

            <!-- Summary -->
            <div class="summary-card">
              <h4 class="summary-title">Project Summary</h4>
              <dl class="summary-list">
                <div class="summary-item">
                  <dt>Title</dt>
                  <dd>{{ formData.title }}</dd>
                </div>
                <div class="summary-item">
                  <dt>Genre</dt>
                  <dd>{{ genres.find(g => g.value === formData.genre)?.label }}</dd>
                </div>
                <div class="summary-item">
                  <dt>Structure</dt>
                  <dd>{{ structures.find(s => s.value === formData.structure)?.title }}</dd>
                </div>
                <div class="summary-item">
                  <dt>Target</dt>
                  <dd>{{ formData.targetWords.toLocaleString() }} words / {{ formData.targetChapters }} chapters</dd>
                </div>
                <div v-if="formData.themes.length > 0" class="summary-item">
                  <dt>Themes</dt>
                  <dd>{{ formData.themes.join(', ') }}</dd>
                </div>
              </dl>
            </div>
          </div>
        </Transition>
      </div>

      <!-- Footer -->
      <footer class="wizard-footer">
        <div class="step-indicator">
          {{ t('wizard.step', { current: currentStep + 1, total: totalSteps }) }}
        </div>
        <div class="wizard-actions">
          <button 
            v-if="currentStep > 0"
            class="btn btn-secondary"
            @click="goToPrevious"
          >
            {{ t('wizard.previous') }}
          </button>
          <button 
            v-if="!isLastStep"
            class="btn btn-primary"
            :disabled="!canGoNext"
            @click="goToNext"
          >
            {{ t('wizard.next') }}
          </button>
          <button 
            v-else
            class="btn btn-primary"
            :disabled="isSubmitting"
            @click="handleSubmit"
          >
            <span v-if="isSubmitting" class="loading-spinner" />
            {{ isSubmitting ? t('common.loading') : t('wizard.finish') }}
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* Overlay */
.wizard-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  animation: fadeIn var(--transition-base) ease-out;
}

/* Container */
.wizard-container {
  background: var(--color-surface);
  border-radius: var(--radius-2xl);
  box-shadow: var(--shadow-xl);
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  animation: slideUp var(--transition-slow) cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Header */
.wizard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-6);
  border-bottom: 1px solid var(--color-border-light);
}

.wizard-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  border-radius: var(--radius-full);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.close-button:hover {
  background: var(--color-border-light);
  color: var(--color-text-secondary);
}

/* Stepper */
.stepper {
  padding: var(--space-6) var(--space-6) var(--space-4);
  position: relative;
}

.stepper-track {
  position: absolute;
  top: calc(var(--space-6) + 16px);
  left: var(--space-6);
  right: var(--space-6);
  height: 2px;
  background: var(--color-border);
  border-radius: var(--radius-full);
}

.stepper-progress {
  height: 100%;
  background: var(--gradient-primary);
  border-radius: var(--radius-full);
  transition: width var(--transition-slow) cubic-bezier(0.16, 1, 0.3, 1);
}

.stepper-steps {
  list-style: none;
  display: flex;
  justify-content: space-between;
  position: relative;
  margin: 0;
  padding: 0;
}

.stepper-step {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stepper-button {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.stepper-button:disabled {
  cursor: default;
}

.stepper-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-full);
  font-size: var(--font-size-base);
  transition: all var(--transition-base);
  position: relative;
  z-index: 1;
}

.stepper-step.active .stepper-icon {
  border-color: var(--color-primary);
  background: var(--color-surface);
  box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.15);
}

.stepper-step.completed .stepper-icon {
  border-color: var(--color-primary);
  background: var(--color-primary);
}

.stepper-label {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-medium);
  transition: color var(--transition-base);
  max-width: 80px;
  text-align: center;
}

.stepper-step.active .stepper-label {
  color: var(--color-primary);
}

.stepper-step.completed .stepper-label {
  color: var(--color-text-secondary);
}

/* Content */
.wizard-content {
  flex: 1;
  overflow-y: auto;
  padding: 0 var(--space-6);
  min-height: 320px;
}

.step-panel {
  padding: var(--space-4) 0;
}

.step-header {
  margin-bottom: var(--space-6);
}

.step-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-1);
}

.step-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
}

/* Form Elements */
.form-group {
  margin-bottom: var(--space-5);
}

.form-label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.required {
  color: var(--color-error);
  margin-left: var(--space-1);
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  transition: all var(--transition-fast);
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.15);
}

.form-input.error,
.form-select.error {
  border-color: var(--color-error);
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: var(--color-text-tertiary);
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg width='12' height='12' viewBox='0 0 12 12' fill='none' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M3 4.5L6 7.5L9 4.5' stroke='%2386868B' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right var(--space-4) center;
  padding-right: var(--space-10);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.error-message {
  display: block;
  font-size: var(--font-size-sm);
  color: var(--color-error);
  margin-top: var(--space-1);
}

/* Theme Tags */
.theme-input-wrapper {
  margin-bottom: var(--space-2);
}

.theme-tags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.theme-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-3);
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  border-radius: var(--radius-full);
}

.theme-tag-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  border-radius: var(--radius-full);
  transition: background var(--transition-fast);
}

.theme-tag-remove:hover {
  background: rgba(0, 122, 255, 0.2);
}

/* Structure Options */
.structure-options {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.structure-option {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-4);
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.structure-option:hover {
  border-color: var(--color-border);
  background: var(--color-border-light);
}

.structure-option.selected {
  border-color: var(--color-primary);
  background: rgba(0, 122, 255, 0.05);
}

.structure-radio {
  position: absolute;
  opacity: 0;
  pointer-events: none;
}

.structure-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.structure-title {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.structure-desc {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.structure-check {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-full);
  background: transparent;
  color: transparent;
  transition: all var(--transition-fast);
}

.structure-option.selected .structure-check {
  background: var(--color-primary);
  color: white;
}

/* Target Presets */
.target-presets {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.preset-button {
  padding: var(--space-2) var(--space-3);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.preset-button:hover {
  border-color: var(--color-border);
  background: var(--color-border-light);
}

.preset-button.selected {
  border-color: var(--color-primary);
  background: rgba(0, 122, 255, 0.1);
  color: var(--color-primary);
}

.custom-input {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.custom-input .form-input {
  width: auto;
  min-width: 120px;
}

.input-suffix {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

/* Summary Card */
.summary-card {
  margin-top: var(--space-6);
  padding: var(--space-4);
  background: var(--color-border-light);
  border-radius: var(--radius-lg);
}

.summary-title {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-secondary);
  margin: 0 0 var(--space-3);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.summary-list {
  margin: 0;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  padding: var(--space-2) 0;
  border-bottom: 1px solid var(--color-border);
}

.summary-item:last-child {
  border-bottom: none;
}

.summary-item dt {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.summary-item dd {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
  margin: 0;
}

/* Footer */
.wizard-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-5) var(--space-6);
  border-top: 1px solid var(--color-border-light);
}

.step-indicator {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.wizard-actions {
  display: flex;
  gap: var(--space-3);
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-5);
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  border: none;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-base);
  min-height: 44px;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-primary:active:not(:disabled) {
  transform: translateY(0);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-border-light);
}

/* Loading Spinner */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: var(--radius-full);
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Transitions */
.slide-fade-enter-active {
  transition: all var(--transition-slow) cubic-bezier(0.16, 1, 0.3, 1);
}

.slide-fade-leave-active {
  transition: all var(--transition-fast) ease-in;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* Responsive */
@media (max-width: 640px) {
  .wizard-container {
    max-height: 100vh;
    border-radius: 0;
  }
  
  .stepper-label {
    display: none;
  }
  
  .wizard-footer {
    flex-direction: column;
    gap: var(--space-4);
  }
  
  .wizard-actions {
    width: 100%;
  }
  
  .wizard-actions .btn {
    flex: 1;
  }
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .wizard-overlay,
  .wizard-container,
  .stepper-progress,
  .slide-fade-enter-active,
  .slide-fade-leave-active {
    animation: none;
    transition: none;
  }
}
</style>
