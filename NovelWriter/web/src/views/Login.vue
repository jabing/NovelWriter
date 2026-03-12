<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { User, Lock, Message, Loading, Warning } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';

const router = useRouter();
const { t } = useI18n();
const authStore = useAuthStore();

// Form state
const isLoginMode = ref(true);
const loading = ref(false);
const error = ref<string | null>(null);

// Form data
const formData = ref({
  email: '',
  password: '',
  name: '',
});

// Toggle between login and register
function toggleMode() {
  isLoginMode.value = !isLoginMode.value;
  error.value = null;
  formData.value = { email: '', password: '', name: '' };
}

// Handle form submission
async function handleSubmit() {
  loading.value = true;
  error.value = null;

  try {
    if (isLoginMode.value) {
      await authStore.login(formData.value.email, formData.value.password);
    } else {
      await authStore.register(formData.value.email, formData.value.password, formData.value.name);
    }
    
    // Redirect to dashboard on success
    router.push('/');
  } catch (err) {
    const errorData = err as { response?: { data?: { detail?: string } } }
    error.value = errorData.response?.data?.detail || t('auth.error');
    console.error('Auth error:', err);
  } finally {
    loading.value = false;
  }
}

// Computed properties
const formTitle = computed(() => 
  isLoginMode.value ? t('auth.loginTitle') : t('auth.registerTitle')
);
const submitText = computed(() => 
  isLoginMode.value ? t('auth.login') : t('auth.register')
);
const toggleText = computed(() => 
  isLoginMode.value ? t('auth.needAccount') : t('auth.haveAccount')
);
const toggleAction = computed(() => 
  isLoginMode.value ? t('auth.register') : t('auth.login')
);
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo/Brand -->
      <div class="brand-section">
        <div class="brand-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 19l7-7 3 3-7 7-3-3z" />
            <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
            <path d="M2 2l7.586 7.586" />
            <circle cx="11" cy="11" r="2" />
          </svg>
        </div>
        <h1 class="brand-title">NovelWriter</h1>
        <p class="brand-subtitle">{{ t('auth.tagline') }}</p>
      </div>

      <!-- Login/Register Card -->
      <div class="login-card">
        <h2 class="card-title">{{ formTitle }}</h2>

        <!-- Error Message -->
        <div v-if="error" class="error-message">
          <el-icon><Warning /></el-icon>
          <span>{{ error }}</span>
        </div>

        <!-- Form -->
        <form @submit.prevent="handleSubmit" class="login-form">
          <!-- Name field (register only) -->
          <el-form-item v-if="!isLoginMode">
            <div class="input-group">
              <el-icon class="input-icon"><User /></el-icon>
              <input
                v-model="formData.name"
                type="text"
                :placeholder="t('auth.namePlaceholder')"
                class="login-input"
                required
              />
            </div>
          </el-form-item>

          <!-- Email field -->
          <el-form-item>
            <div class="input-group">
              <el-icon class="input-icon"><Message /></el-icon>
              <input
                v-model="formData.email"
                type="email"
                :placeholder="t('auth.emailPlaceholder')"
                class="login-input"
                required
              />
            </div>
          </el-form-item>

          <!-- Password field -->
          <el-form-item>
            <div class="input-group">
              <el-icon class="input-icon"><Lock /></el-icon>
              <input
                v-model="formData.password"
                type="password"
                :placeholder="t('auth.passwordPlaceholder')"
                class="login-input"
                required
              />
            </div>
          </el-form-item>

          <!-- Submit Button -->
          <button type="submit" class="btn-submit" :disabled="loading">
            <el-icon v-if="loading" class="is-spinning"><Loading /></el-icon>
            <span>{{ submitText }}</span>
          </button>
        </form>

        <!-- Toggle Link -->
        <div class="toggle-section">
          <span class="toggle-text">{{ toggleText }}</span>
          <button @click="toggleMode" class="toggle-link">
            {{ toggleAction }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ========== PAGE LAYOUT ========== */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(
    135deg,
    var(--color-bg-secondary) 0%,
    var(--color-bg-primary) 100%
  );
  padding: var(--space-6);
}

.login-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-8);
  max-width: 420px;
  width: 100%;
}

/* ========== BRAND SECTION ========== */
.brand-section {
  text-align: center;
  animation: fadeInDown 0.6s ease-out;
}

.brand-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 80px;
  height: 80px;
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-primary-hover) 100%
  );
  border-radius: var(--radius-xl);
  color: #fff;
  margin-bottom: var(--space-4);
  box-shadow: 0 8px 24px rgba(139, 90, 43, 0.3);
}

.brand-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h2);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  letter-spacing: -0.02em;
}

.brand-subtitle {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  margin: 0;
}

/* ========== LOGIN CARD ========== */
.login-card {
  width: 100%;
  background: var(--color-bg-elevated);
  border-radius: var(--radius-xl);
  padding: var(--space-8);
  box-shadow: var(--shadow-card);
  border: 1px solid var(--color-border);
  animation: fadeInUp 0.6s ease-out;
}

.card-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--color-text-primary);
  text-align: center;
  margin-bottom: var(--space-6);
  letter-spacing: -0.02em;
}

/* ========== ERROR MESSAGE ========== */
.error-message {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: rgba(155, 44, 44, 0.1);
  border: 1px solid rgba(155, 44, 44, 0.3);
  border-radius: var(--radius-md);
  color: var(--color-error);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  margin-bottom: var(--space-4);
}

/* ========== FORM STYLES ========== */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.input-group {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  transition: all var(--transition-fast);
}

.input-group:focus-within {
  border-color: var(--color-primary);
  background: var(--color-bg-primary);
  box-shadow: 0 0 0 3px rgba(139, 90, 43, 0.1);
}

.input-icon {
  color: var(--color-text-tertiary);
  font-size: 18px;
  flex-shrink: 0;
}

.login-input {
  flex: 1;
  border: none;
  background: transparent;
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-primary);
  outline: none;
}

.login-input::placeholder {
  color: var(--color-text-placeholder);
}

/* ========== SUBMIT BUTTON ========== */
.btn-submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  width: 100%;
  padding: var(--space-4);
  margin-top: var(--space-2);
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-primary-hover) 100%
  );
  border: none;
  border-radius: var(--radius-md);
  color: #fff;
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-base);
  box-shadow: 0 4px 12px rgba(139, 90, 43, 0.2);
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(139, 90, 43, 0.3);
}

.btn-submit:active:not(:disabled) {
  transform: translateY(0);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ========== TOGGLE SECTION ========== */
.toggle-section {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  margin-top: var(--space-6);
  padding-top: var(--space-6);
  border-top: 1px solid var(--color-border-light);
}

.toggle-text {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  color: var(--color-text-secondary);
}

.toggle-link {
  background: none;
  border: none;
  color: var(--color-primary);
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  cursor: pointer;
  transition: color var(--transition-fast);
}

.toggle-link:hover {
  color: var(--color-primary-hover);
}

/* ========== ANIMATIONS ========== */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.is-spinning {
  animation: spin 1s linear infinite;
}

/* ========== RESPONSIVE ========== */
@media (max-width: 480px) {
  .login-page {
    padding: var(--space-4);
  }

  .login-card {
    padding: var(--space-6);
  }

  .brand-title {
    font-size: var(--font-size-h3);
  }
}

/* ========== DARK MODE ========== */
[data-theme="dark"] .login-page {
  background: linear-gradient(
    135deg,
    var(--color-bg-primary) 0%,
    var(--color-bg-secondary) 100%
  );
}

[data-theme="dark"] .brand-icon {
  box-shadow: 0 8px 24px rgba(166, 123, 91, 0.3);
}

[data-theme="dark"] .btn-submit {
  box-shadow: 0 4px 12px rgba(166, 123, 91, 0.3);
}

[data-theme="dark"] .btn-submit:hover:not(:disabled) {
  box-shadow: 0 6px 20px rgba(166, 123, 91, 0.4);
}
</style>
