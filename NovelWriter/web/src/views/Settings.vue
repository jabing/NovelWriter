<script setup lang="ts">
import { ref, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { useSettingsStore } from '@/stores/settingsStore';

const { t } = useI18n();
const settingsStore = useSettingsStore();

const qualityModes = computed(() => [
  { value: 'high', label: t('settings.qualityModes.high.label'), description: t('settings.qualityModes.high.description') },
  { value: 'medium', label: t('settings.qualityModes.medium.label'), description: t('settings.qualityModes.medium.description') },
  { value: 'low', label: t('settings.qualityModes.low.label'), description: t('settings.qualityModes.low.description') }
]);

const themes = computed(() => [
  { value: 'light', label: t('settings.themes.light'), preview: 'bg-white' },
  { value: 'dark', label: t('settings.themes.dark'), preview: 'bg-gray-900' }
]);

const apiKey = ref('');
const showApiKey = ref(false);

const currentQualityMode = ref('medium'); // Default value
const currentTheme = ref('light'); // Default value

// Sync with store
const language = computed({
  get: () => settingsStore.language,
  set: (val) => settingsStore.setLanguage(val)
});

const theme = computed({
  get: () => settingsStore.theme,
  set: (val) => settingsStore.setTheme(val)
});

const saveApiKey = () => {
  // In a real app, this would save to a secure backend
  console.log('API Key saved:', apiKey.value);
  showApiKey.value = false;
};

const clearApiKey = () => {
  apiKey.value = '';
};
</script>

<template>
  <div class="settings-page" data-testid="settings-page">
    <header class="page-header">
      <h1 data-testid="settings-page-title">{{ t('settings.title') }}</h1>
      <p>{{ t('settings.subtitle') }}</p>
    </header>

    <div class="settings-grid">
      <!-- Quality Mode Section -->
      <section class="settings-section card" data-testid="settings-quality-mode-section">
        <h2>{{ t('settings.qualityMode.title') }}</h2>
        <div class="quality-modes">
          <div
            v-for="mode in qualityModes"
            :key="mode.value"
            class="quality-mode-item"
            :data-testid="`quality-mode-${mode.value}`"
            :class="{ active: currentQualityMode === mode.value }"
            @click="currentQualityMode = mode.value"
          >
            <div class="quality-mode-content">
              <h3>{{ mode.label }}</h3>
              <p class="text-sm text-gray-500" data-testid="quality-mode-description">{{ mode.description }}</p>
            </div>
            <div class="quality-mode-indicator">
              <div class="quality-indicator" :class="mode.value"></div>
            </div>
          </div>
        </div>
      </section>

      <!-- Language Section -->
      <section class="settings-section card" data-testid="settings-language-section">
        <h2>{{ t('settings.language.title') }}</h2>
        <div class="language-toggle">
          <div class="language-info">
            <label>{{ t('settings.language.interfaceLabel') }}</label>
            <p>{{ t('settings.language.interfaceDescription') }}</p>
          </div>
          <div class="toggle-container">
            <span class="toggle-label">EN</span>
            <label class="toggle">
              <input type="checkbox" v-model="language" :true-value="'en'" :false-value="'zh'" data-testid="language-toggle" />
              <span class="toggle-slider"></span>
            </label>
            <span class="toggle-label">ZH</span>
          </div>
        </div>
      </section>

      <!-- API Key Section -->
      <section class="settings-section card" data-testid="settings-api-key-section">
        <h2>{{ t('settings.apiConfig.title') }}</h2>
        <div class="api-key-section">
          <div class="api-key-info">
            <label>{{ t('settings.apiConfig.apiKeyLabel') }}</label>
            <p>{{ t('settings.apiConfig.apiKeyDescription') }}</p>
          </div>
          <div class="api-key-input-container">
            <input
              v-if="showApiKey"
              v-model="apiKey"
              type="password"
              :placeholder="t('settings.apiConfig.placeholder')"
              class="api-key-input"
              data-testid="api-key-input"
            />
            <div v-else class="api-key-mask" data-testid="api-key-masked">
              <span>••••••••</span>
              <button @click="showApiKey = true" class="reveal-btn" data-testid="api-key-reveal-btn">{{ t('settings.apiConfig.show') }}</button>
            </div>
            <div class="api-key-actions">
              <button
                v-if="showApiKey"
                @click="saveApiKey"
                class="btn btn-primary btn-sm"
                data-testid="api-key-save-btn"
              >
                {{ t('common.save') }}
              </button>
              <button
                v-if="showApiKey"
                @click="clearApiKey"
                class="btn btn-secondary btn-sm"
                data-testid="api-key-clear-btn"
              >
                {{ t('common.clear') }}
              </button>
              <button
                v-else
                @click="showApiKey = true"
                class="btn btn-secondary btn-sm"
                data-testid="api-key-edit-btn"
              >
                {{ t('common.edit') }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Theme Section -->
      <section class="settings-section card" data-testid="settings-theme-section">
        <h2>{{ t('settings.theme.title') }}</h2>
        <div class="theme-options">
          <div
            v-for="themeOption in themes"
            :key="themeOption.value"
            class="theme-option"
            :data-testid="`theme-${themeOption.value}`"
            :class="{ active: currentTheme === themeOption.value }"
            @click="currentTheme = themeOption.value"
          >
            <div class="theme-preview" :class="themeOption.preview" data-testid="theme-preview"></div>
            <div class="theme-label">{{ themeOption.label }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.settings-page {
  padding: var(--space-6);
  max-width: 900px;
  animation: fadeIn var(--transition-slow);
}

.page-header {
  margin-bottom: var(--space-8);
  animation: fadeInUp var(--transition-slow) backwards;
  animation-delay: 0.05s;
}

.page-header h1 {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
}

.page-header p {
  color: var(--color-text-secondary);
  font-size: var(--font-size-lg);
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--space-6);
}

.settings-section {
  padding: var(--space-6);
  animation: fadeInUp var(--transition-slow) backwards;
}

.settings-section:nth-child(1) { animation-delay: 0.1s; }
.settings-section:nth-child(2) { animation-delay: 0.15s; }
.settings-section:nth-child(3) { animation-delay: 0.2s; }
.settings-section:nth-child(4) { animation-delay: 0.25s; }

.settings-section h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

/* Quality Mode Styles */
.quality-modes {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.quality-mode-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--color-border-light);
  will-change: transform, box-shadow, background-color;
}

.quality-mode-item:hover {
  background: var(--color-surface-elevated);
  border-color: var(--color-primary);
  transform: translateY(-1px);
}

.quality-mode-item.active {
  background: var(--gradient-primary);
  color: white;
  border-color: transparent;
}

.quality-mode-content h3 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  margin-bottom: var(--space-1);
}

.quality-mode-content p {
  font-size: var(--font-size-xs);
  opacity: 0.9;
}

.quality-mode-indicator {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface);
  border: 2px solid var(--color-border);
  transition: all var(--transition-fast);
}

.quality-indicator {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  transition: transform var(--transition-fast);
}

.quality-mode-item:hover .quality-indicator {
  transform: scale(1.1);
}

.quality-indicator.high {
  background: #34C759;
}

.quality-indicator.medium {
  background: #FF9500;
}

.quality-indicator.low {
  background: #FF3B30;
}

/* Language Toggle Styles */
.language-toggle {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.language-info label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.language-info p {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.toggle-container {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toggle-label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  min-width: 24px;
  text-align: center;
  transition: color var(--transition-fast);
}

/* API Key Styles */
.api-key-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.api-key-info label {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.api-key-info p {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.api-key-input-container {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.api-key-input {
  flex: 1;
  padding: var(--space-2) var(--space-3);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
  background: var(--color-surface);
  transition: all var(--transition-fast);
}

.api-key-input:focus {
  border-color: var(--color-border-focus);
  box-shadow: 0 0 0 3px var(--color-primary-muted);
  outline: none;
}

.api-key-mask {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  min-width: 200px;
}

.api-key-mask span {
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
}

.reveal-btn {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
  background: transparent;
  border: none;
  cursor: pointer;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  transition: all var(--transition-fast);
}

.reveal-btn:hover {
  background: var(--color-primary);
  color: white;
}

.api-key-actions {
  display: flex;
  gap: var(--space-2);
}

/* Theme Options Styles */
.theme-options {
  display: flex;
  gap: var(--space-3);
}

.theme-option {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--space-3);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
  border: 1px solid var(--color-border-light);
  will-change: transform, box-shadow, border-color;
}

.theme-option:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.theme-option.active {
  border-color: var(--color-primary);
  background: var(--color-surface-elevated);
}

.theme-preview {
  width: 60px;
  height: 40px;
  border-radius: var(--radius-md);
  margin-bottom: var(--space-2);
  border: 1px solid var(--color-border);
  transition: transform var(--transition-fast);
}

.theme-option:hover .theme-preview {
  transform: scale(1.05);
}

.theme-label {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

/* Toggle Switch */
.toggle {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 28px;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: var(--color-border);
  transition: var(--transition-base);
  border-radius: var(--radius-full);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 22px;
  width: 22px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: var(--transition-base);
  border-radius: 50%;
  box-shadow: var(--shadow-sm);
}

.toggle input:checked + .toggle-slider {
  background-color: var(--color-primary);
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(20px);
}

/* Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
  min-height: 36px;
  will-change: transform, box-shadow;
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-border-light);
  transform: translateY(-1px);
}

.btn-secondary:active {
  transform: scale(0.98);
}

.btn-sm {
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-xs);
  min-height: 32px;
}

/* Keyframe animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeInUp {
  from { 
    opacity: 0; 
    transform: translateY(12px); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0); 
  }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .settings-page,
  .page-header,
  .settings-section {
    animation: none;
  }
  
  .quality-mode-item:hover,
  .theme-option:hover,
  .btn:hover {
    transform: none;
  }
  
  .toggle-slider,
  .toggle-slider:before {
    transition: none;
  }
}
</style>