<template>
  <div v-if="isVisible" class="onboarding-overlay" @click="handleOverlayClick">
    <div class="onboarding-modal" @click.stop>
      <!-- Header -->
      <div class="onboarding-header">
        <h2 class="onboarding-title">{{ t('onboarding.title') }}</h2>
        <p class="onboarding-subtitle">{{ t('onboarding.subtitle') }}</p>
        <button class="close-btn" @click="closeOnboarding" :aria-label="t('common.close')">
          <span>&times;</span>
        </button>
      </div>

      <!-- Progress Bar -->
      <div class="progress-container">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
        </div>
        <span class="progress-text">{{ currentStep + 1 }} / {{ totalSteps }}</span>
      </div>

      <!-- Steps Content -->
      <div class="onboarding-content">
        <!-- Step 1: Create Project -->
        <transition name="slide" mode="out-in">
          <div v-if="currentStep === 0" key="step1" class="step-content">
            <div class="step-icon">📝</div>
            <h3 class="step-title">{{ t('onboarding.steps.project.title') }}</h3>
            <p class="step-description">{{ t('onboarding.steps.project.description') }}</p>
            <div class="step-tips">
              <div class="tip-item">
                <span class="tip-icon">✨</span>
                <span>{{ t('onboarding.steps.project.tips.chooseGenre') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">🎯</span>
                <span>{{ t('onboarding.steps.project.tips.setGoals') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">📚</span>
                <span>{{ t('onboarding.steps.project.tips.outline') }}</span>
              </div>
            </div>
          </div>

          <!-- Step 2: Add Characters -->
          <div v-else-if="currentStep === 1" key="step2" class="step-content">
            <div class="step-icon">👥</div>
            <h3 class="step-title">{{ t('onboarding.steps.characters.title') }}</h3>
            <p class="step-description">{{ t('onboarding.steps.characters.description') }}</p>
            <div class="step-tips">
              <div class="tip-item">
                <span class="tip-icon">🎭</span>
                <span>{{ t('onboarding.steps.characters.tips.profiles') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">🔗</span>
                <span>{{ t('onboarding.steps.characters.tips.relationships') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">📖</span>
                <span>{{ t('onboarding.steps.characters.tips.arcs') }}</span>
              </div>
            </div>
          </div>

          <!-- Step 3: Write Chapter -->
          <div v-else-if="currentStep === 2" key="step3" class="step-content">
            <div class="step-icon">✍️</div>
            <h3 class="step-title">{{ t('onboarding.steps.write.title') }}</h3>
            <p class="step-description">{{ t('onboarding.steps.write.description') }}</p>
            <div class="step-tips">
              <div class="tip-item">
                <span class="tip-icon">🤖</span>
                <span>{{ t('onboarding.steps.write.tips.aiAssist') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">📝</span>
                <span>{{ t('onboarding.steps.write.tips.draft') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">🔄</span>
                <span>{{ t('onboarding.steps.write.tips.revise') }}</span>
              </div>
            </div>
          </div>

          <!-- Step 4: Publish -->
          <div v-else-if="currentStep === 3" key="step4" class="step-content">
            <div class="step-icon">🚀</div>
            <h3 class="step-title">{{ t('onboarding.steps.publish.title') }}</h3>
            <p class="step-description">{{ t('onboarding.steps.publish.description') }}</p>
            <div class="step-tips">
              <div class="tip-item">
                <span class="tip-icon">🌐</span>
                <span>{{ t('onboarding.steps.publish.tips.platforms') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">📊</span>
                <span>{{ t('onboarding.steps.publish.tips.analytics') }}</span>
              </div>
              <div class="tip-item">
                <span class="tip-icon">💬</span>
                <span>{{ t('onboarding.steps.publish.tips.feedback') }}</span>
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Navigation Buttons -->
      <div class="onboarding-footer">
        <button
          v-if="currentStep > 0"
          @click="previousStep"
          class="btn btn-secondary"
        >
          {{ t('onboarding.previous') }}
        </button>
        <button
          v-else
          @click="closeOnboarding"
          class="btn btn-secondary"
        >
          {{ t('onboarding.skip') }}
        </button>
        
        <button
          @click="nextStep"
          class="btn btn-primary"
        >
          {{ currentStep === totalSteps - 1 ? t('onboarding.finish') : t('onboarding.next') }}
        </button>
      </div>

      <!-- Don't show again checkbox -->
      <div class="dont-show-again">
        <label class="checkbox-label">
          <input
            type="checkbox"
            v-model="dontShowAgain"
            @change="savePreference"
          />
          <span class="checkbox-text">{{ t('onboarding.dontShowAgain') }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// State
const isVisible = ref(false);
const currentStep = ref(0);
const dontShowAgain = ref(false);

// Constants
const STORAGE_KEY = 'novelwriter_onboarding_dismissed';
const totalSteps = 4;

// Computed
const progressPercentage = computed(() => {
  return ((currentStep.value + 1) / totalSteps) * 100;
});

// Methods
const checkOnboardingStatus = () => {
  const dismissed = localStorage.getItem(STORAGE_KEY);
  if (!dismissed || dismissed === 'false') {
    isVisible.value = true;
    currentStep.value = 0;
  }
};

const savePreference = () => {
  if (dontShowAgain.value) {
    localStorage.setItem(STORAGE_KEY, 'true');
  } else {
    localStorage.removeItem(STORAGE_KEY);
  }
};

const closeOnboarding = () => {
  isVisible.value = false;
  if (dontShowAgain.value) {
    savePreference();
  }
};

const nextStep = () => {
  if (currentStep.value < totalSteps - 1) {
    currentStep.value++;
  } else {
    closeOnboarding();
  }
};

const previousStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--;
  }
};

const handleOverlayClick = (event: MouseEvent) => {
  if (event.target === event.currentTarget) {
    closeOnboarding();
  }
};

// Lifecycle
onMounted(() => {
  checkOnboardingStatus();
});

// Expose method to manually show onboarding (for testing/settings)
defineExpose({
  show: () => {
    isVisible.value = true;
    currentStep.value = 0;
  }
});
</script>

<style scoped>
/* Overlay */
.onboarding-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: var(--space-6);
  animation: fadeIn var(--transition-base);
}

/* Modal */
.onboarding-modal {
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  max-width: 520px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-2xl);
  animation: slideUp var(--transition-base);
  position: relative;
}

/* Header */
.onboarding-header {
  padding: var(--space-6);
  text-align: center;
  border-bottom: 1px solid var(--color-border-light);
  position: relative;
}

.onboarding-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.onboarding-subtitle {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
}

.close-btn {
  position: absolute;
  top: var(--space-4);
  right: var(--space-4);
  background: transparent;
  border: none;
  font-size: var(--font-size-2xl);
  color: var(--color-text-tertiary);
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.close-btn:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

/* Progress Bar */
.progress-container {
  padding: var(--space-4) var(--space-6);
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: var(--color-border-light);
  border-radius: var(--radius-full);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary), var(--color-primary-light));
  transition: width var(--transition-base);
  border-radius: var(--radius-full);
}

.progress-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
  min-width: 48px;
  text-align: right;
}

/* Content */
.onboarding-content {
  padding: var(--space-6);
  min-height: 320px;
}

.step-content {
  text-align: center;
  animation: slideIn var(--transition-base);
}

.step-icon {
  font-size: 64px;
  margin-bottom: var(--space-4);
  display: block;
}

.step-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-3);
}

.step-description {
  font-size: var(--font-size-base);
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: var(--space-6);
}

/* Tips */
.step-tips {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  text-align: left;
  background: var(--color-bg-secondary);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
}

.tip-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.tip-icon {
  font-size: var(--font-size-lg);
  flex-shrink: 0;
}

/* Footer */
.onboarding-footer {
  padding: var(--space-4) var(--space-6);
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

/* Don't show again */
.dont-show-again {
  padding: 0 var(--space-6) var(--space-6);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  user-select: none;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: var(--color-primary);
}

.checkbox-text {
  transition: color var(--transition-fast);
}

.checkbox-label:hover .checkbox-text {
  color: var(--color-text-primary);
}

/* Buttons */
.btn {
  padding: var(--space-2) var(--space-6);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-md);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  min-width: 100px;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-bg-secondary);
  transform: translateY(-1px);
}

/* Transitions */
.slide-enter-active,
.slide-leave-active {
  transition: all var(--transition-base);
}

.slide-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.slide-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Scrollbar */
.onboarding-modal::-webkit-scrollbar {
  width: 8px;
}

.onboarding-modal::-webkit-scrollbar-track {
  background: var(--color-bg-secondary);
  border-radius: var(--radius-full);
}

.onboarding-modal::-webkit-scrollbar-thumb {
  background: var(--color-border);
  border-radius: var(--radius-full);
}

.onboarding-modal::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-dark);
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .onboarding-overlay,
  .onboarding-modal,
  .progress-fill,
  .step-content {
    animation: none;
  }
  
  .slide-enter-active,
  .slide-leave-active {
    transition: none;
  }
}
</style>
