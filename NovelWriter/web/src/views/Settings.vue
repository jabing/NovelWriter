<script setup lang="ts">
import { ref, computed } from 'vue';
import { useSettingsStore } from '@/stores/settingsStore';

const settingsStore = useSettingsStore();

const qualityModes = [
  { value: 'high', label: 'High Quality', description: 'Best quality output with detailed analysis' },
  { value: 'medium', label: 'Medium Quality', description: 'Balanced quality and performance' },
  { value: 'low', label: 'Low Quality', description: 'Fastest generation with basic analysis' }
];

const themes = [
  { value: 'light', label: 'Light', preview: 'bg-white' },
  { value: 'dark', label: 'Dark', preview: 'bg-gray-900' }
];

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
      <h1 data-testid="settings-page-title">Settings</h1>
      <p>Configure your preferences and application settings</p>
    </header>

    <div class="settings-grid">
      <!-- Quality Mode Section -->
      <section class="settings-section card" data-testid="settings-quality-mode-section">
        <h2>Quality Mode</h2>
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
        <h2>Language</h2>
        <div class="language-toggle">
          <div class="language-info">
            <label>Interface Language</label>
            <p>Select your preferred language for the application</p>
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
        <h2>API Configuration</h2>
        <div class="api-key-section">
          <div class="api-key-info">
            <label>API Key</label>
            <p>Enter your API key for AI services</p>
          </div>
          <div class="api-key-input-container">
            <input
              v-if="showApiKey"
              v-model="apiKey"
              type="password"
              placeholder="Enter API key"
              class="api-key-input"
              data-testid="api-key-input"
            />
            <div v-else class="api-key-mask" data-testid="api-key-masked">
              <span>••••••••</span>
              <button @click="showApiKey = true" class="reveal-btn" data-testid="api-key-reveal-btn">Show</button>
            </div>
            <div class="api-key-actions">
              <button
                v-if="showApiKey"
                @click="saveApiKey"
                class="btn btn-primary btn-sm"
                data-testid="api-key-save-btn"
              >
                Save
              </button>
              <button
                v-if="showApiKey"
                @click="clearApiKey"
                class="btn btn-secondary btn-sm"
                data-testid="api-key-clear-btn"
              >
                Clear
              </button>
              <button
                v-else
                @click="showApiKey = true"
                class="btn btn-secondary btn-sm"
                data-testid="api-key-edit-btn"
              >
                Edit
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- Theme Section -->
      <section class="settings-section card" data-testid="settings-theme-section">
        <h2>Theme</h2>
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
}

.page-header {
  margin-bottom: var(--space-8);
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
}

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
  transition: all var(--transition-base);
  border: 1px solid var(--color-border-light);
}

.quality-mode-item:hover {
  background: var(--color-surface-elevated);
  border-color: var(--color-primary);
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
}

.quality-indicator {
  width: 20px;
  height: 20px;
  border-radius: 50%;
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
  transition: all var(--transition-base);
  border: 1px solid var(--color-border-light);
}

.theme-option:hover {
  border-color: var(--color-primary);
  transform: translateY(-2px);
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
  transition: all var(--transition-base);
  min-height: 36px;
}

.btn-primary {
  background: var(--gradient-primary);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--color-surface);
  color: var(--color-text-primary);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  background: var(--color-border-light);
}

.btn-sm {
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-xs);
  min-height: 32px;
}
</style>