<template>
  <div class="platform-connect">
    <div class="platform-grid grid-3">
      <div 
        v-for="platform in platforms" 
        :key="platform.id" 
        class="platform-card card"
      >
        <div class="platform-header">
          <div class="platform-icon">
            <i :class="getPlatformIcon(platform.type)"></i>
          </div>
          <div class="platform-info">
            <h3 class="platform-name">{{ platform.name }}</h3>
            <div class="platform-status">
              <span 
                class="status-badge badge" 
                :class="platform.connected ? 'badge-success' : 'badge-warning'"
              >
                <i class="status-icon" :class="platform.connected ? 'fas fa-check-circle' : 'fas fa-exclamation-circle'"></i>
                {{ platform.connected ? 'Connected' : 'Not Connected' }}
              </span>
            </div>
          </div>
        </div>

        <div class="platform-content">
          <div class="platform-details">
            <div class="detail-item">
              <span class="detail-label">Type:</span>
              <span class="detail-value">{{ platform.type }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Last Sync:</span>
              <span class="detail-value">{{ platform.last_sync || 'Never' }}</span>
            </div>
          </div>

          <div class="platform-actions">
            <button 
              class="btn btn-primary"
              @click="toggleConnection(platform)"
            >
              <i class="fas fa-plug"></i>
              {{ platform.connected ? 'Disconnect' : 'Connect' }}
            </button>
            <button 
              class="btn btn-secondary"
              @click="showCredentials(platform)"
            >
              <i class="fas fa-key"></i>
              Configure
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Credential Configuration Modal -->
    <div v-if="showCredentialModal" class="modal-overlay">
      <div class="modal card">
        <div class="modal-header">
          <h2 class="modal-title">Configure {{ selectedPlatform?.name }} Credentials</h2>
          <button 
            class="close-btn btn btn-secondary"
            @click="closeCredentialModal"
          >
            <i class="fas fa-times"></i>
          </button>
        </div>
        
        <div class="modal-body">
          <form @submit.prevent="testConnection">
            <div class="form-group">
              <label class="form-label">API Key</label>
              <input 
                type="password" 
                v-model="credentials.apiKey"
                class="form-input"
                placeholder="Enter your API key"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Secret Key</label>
              <input 
                type="password" 
                v-model="credentials.secretKey"
                class="form-input"
                placeholder="Enter your secret key"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Username</label>
              <input 
                type="text" 
                v-model="credentials.username"
                class="form-input"
                placeholder="Enter your username"
              />
            </div>
            
            <div class="form-group">
              <label class="form-label">Password</label>
              <input 
                type="password" 
                v-model="credentials.password"
                class="form-input"
                placeholder="Enter your password"
              />
            </div>
          </form>
        </div>
        
        <div class="modal-footer">
          <button 
            class="btn btn-primary"
            @click="testConnection"
          >
            <i class="fas fa-test-tube"></i>
            Test Connection
          </button>
          <button 
            class="btn btn-secondary"
            @click="saveCredentials"
          >
            <i class="fas fa-save"></i>
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import type { Platform } from '../types';

const props = defineProps<{
  platforms: Platform[];
}>();

const emit = defineEmits<{
  (e: 'toggle-connection', platform: Platform): void;
  (e: 'show-credentials', platform: Platform): void;
  (e: 'test-connection', platform: Platform, credentials: any): void;
  (e: 'save-credentials', platform: Platform, credentials: any): void;
}>();

const showCredentialModal = ref(false);
const selectedPlatform = ref<Platform | null>(null);
const credentials = ref({
  apiKey: '',
  secretKey: '',
  username: '',
  password: ''
});

const platformIcons = {
  amazon: 'fab fa-amazon',
  apple: 'fab fa-apple',
  google: 'fab fa-google',
  microsoft: 'fab fa-microsoft',
  facebook: 'fab fa-facebook',
  twitter: 'fab fa-twitter',
  instagram: 'fab fa-instagram',
  youtube: 'fab fa-youtube',
  github: 'fab fa-github',
  reddit: 'fab fa-reddit',
  linkedin: 'fab fa-linkedin',
  default: 'fas fa-globe'
};

const getPlatformIcon = (type: string) => {
  return platformIcons[type.toLowerCase()] || platformIcons.default;
};

const toggleConnection = (platform: Platform) => {
  emit('toggle-connection', platform);
};

const showCredentials = (platform: Platform) => {
  selectedPlatform.value = platform;
  credentials.value = {
    apiKey: '',
    secretKey: '',
    username: '',
    password: ''
  };
  showCredentialModal.value = true;
};

const closeCredentialModal = () => {
  showCredentialModal.value = false;
  selectedPlatform.value = null;
};

const testConnection = () => {
  if (selectedPlatform.value) {
    emit('test-connection', selectedPlatform.value, { ...credentials.value });
  }
};

const saveCredentials = () => {
  if (selectedPlatform.value) {
    emit('save-credentials', selectedPlatform.value, { ...credentials.value });
    closeCredentialModal();
  }
};
</script>

<style scoped>
.platform-connect {
  padding: var(--space-8);
}

.platform-grid {
  gap: var(--space-6);
}

.platform-card {
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
}

.platform-header {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-4);
}

.platform-icon {
  width: var(--space-10);
  height: var(--space-10);
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-surface-elevated);
  border-radius: var(--radius-full);
  color: var(--color-primary);
}

.platform-info {
  flex: 1;
}

.platform-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  margin-bottom: var(--space-1);
}

.platform-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.status-badge {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
}

.status-icon {
  margin-right: var(--space-1);
}

.platform-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.platform-details {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label {
  font-size: var(--font-size-sm);
  color: var(--color-text-tertiary);
  font-weight: var(--font-weight-medium);
}

.detail-value {
  font-size: var(--font-size-base);
  color: var(--color-text-primary);
}

.platform-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-4);
}

.platform-actions .btn {
  flex: 1;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
}

.modal {
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-6);
  padding-bottom: var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.modal-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
}

.close-btn {
  padding: var(--space-2) var(--space-3);
  min-height: 36px;
}

.modal-body {
  margin-bottom: var(--space-6);
}

.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  display: block;
  margin-bottom: var(--space-2);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-primary);
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  background: var(--color-surface);
  transition: border-color var(--transition-base);
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px rgba(0, 122, 255, 0.2);
}

.modal-footer {
  display: flex;
  gap: var(--space-2);
  justify-content: flex-end;
  padding-top: var(--space-4);
  border-top: 1px solid var(--color-border);
}

.modal-footer .btn {
  flex: 1;
  max-width: 150px;
}
</style>