<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useProjectStore } from '@/stores/projectStore'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'
import GlobalSearch from '@/components/GlobalSearch.vue'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()
const authStore = useAuthStore()
const { t } = useI18n()

// Search modal state
const showSearch = ref(false)

// Mobile sidebar state
const isSidebarOpen = ref(false)

// Toggle sidebar for mobile
const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

// Close sidebar
const closeSidebar = () => {
  isSidebarOpen.value = false
}

// Load auth state from storage on mount
onMounted(() => {
  authStore.loadFromStorage()
})

// Auth state
const isLoggedIn = computed(() => authStore.isLoggedIn)
const currentUser = computed(() => authStore.user)

// Logout handler
const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// Navigation items with SF Symbols-style icons
const navItems = [
  { name: 'Dashboard', path: '/', icon: 'house' },
  { name: 'Projects', path: '/projects', icon: 'folder' },
  { name: 'Writing', path: '/writing', icon: 'pencil' },
  { name: 'Reading', path: '/reading', icon: 'book' },
  { name: 'Agents', path: '/agents', icon: 'cpu' },
  { name: 'Publish', path: '/publish', icon: 'paperplane' },
  { name: 'Comments', path: '/comments', icon: 'bubble' },
  { name: 'Analytics', path: '/analytics', icon: 'chart' },
  { name: 'Settings', path: '/settings', icon: 'gear' }
]

// Current project info
const currentProject = computed(() => projectStore.currentProjectData)

// Check if nav item is active
const isActive = (path: string) => {
  if (path === '/') {
    return route.path === '/'
  }
  return route.path.startsWith(path)
}

// Navigate to route
const navigate = (path: string) => {
  router.push(path)
  closeSidebar()
}

// Open search modal
const openSearch = () => {
  showSearch.value = true
}

// Keyboard shortcut for search (Ctrl/Cmd + K)
const handleKeyDown = (e: KeyboardEvent) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
    e.preventDefault()
    openSearch()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeyDown)
})
</script>

<template>
  <div class="main-layout">
    <!-- Sidebar -->
    <aside class="sidebar" :class="{ 'sidebar-open': isSidebarOpen }">
      <!-- Mobile Overlay -->
      <div class="sidebar-overlay" @click="closeSidebar"></div>
      
      <!-- Logo/Brand -->
      <div class="sidebar-header">
        <div class="brand">
          <div class="brand-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 19l7-7 3 3-7 7-3-3z" />
              <path d="M18 13l-1.5-7.5L2 2l3.5 14.5L13 18l5-5z" />
              <path d="M2 2l7.586 7.586" />
              <circle cx="11" cy="11" r="2" />
            </svg>
          </div>
          <span class="brand-name">NovelWriter</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="sidebar-nav">
        <ul class="nav-list">
          <li v-for="item in navItems" :key="item.path">
            <button
              class="nav-item"
              :data-testid="`nav-${item.name.toLowerCase()}`"
              :class="{ active: isActive(item.path) }"
              @click="navigate(item.path)"
            >
              <!-- SF Symbols-style Icon -->
              <span class="nav-icon">
                <!-- House Icon -->
                <svg v-if="item.icon === 'house'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  <polyline points="9 22 9 12 15 12 15 22" />
                </svg>
                <!-- Folder Icon -->
                <svg v-else-if="item.icon === 'folder'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                </svg>
                <!-- Pencil Icon -->
                <svg v-else-if="item.icon === 'pencil'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
                </svg>
                <!-- Book Icon -->
                <svg v-else-if="item.icon === 'book'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                  <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                </svg>
                <!-- CPU Icon -->
                <svg v-else-if="item.icon === 'cpu'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="4" y="4" width="16" height="16" rx="2" ry="2" />
                  <rect x="9" y="9" width="6" height="6" />
                  <line x1="9" y1="1" x2="9" y2="4" />
                  <line x1="15" y1="1" x2="15" y2="4" />
                  <line x1="9" y1="20" x2="9" y2="23" />
                  <line x1="15" y1="20" x2="15" y2="23" />
                  <line x1="20" y1="9" x2="23" y2="9" />
                  <line x1="20" y1="14" x2="23" y2="14" />
                  <line x1="1" y1="9" x2="4" y2="9" />
                  <line x1="1" y1="14" x2="4" y2="14" />
                </svg>
                <!-- Paper Plane Icon -->
                <svg v-else-if="item.icon === 'paperplane'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="22" y1="2" x2="11" y2="13" />
                  <polygon points="22 2 15 22 11 13 2 9 22 2" />
                </svg>
                <!-- Bubble/Comment Icon -->
                <svg v-else-if="item.icon === 'bubble'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
                <!-- Chart/Analytics Icon -->
                <svg v-else-if="item.icon === 'chart'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
                <!-- Gear Icon -->
                <svg v-else-if="item.icon === 'gear'" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
                </svg>
              </span>
              <span class="nav-label">{{ item.name }}</span>
            </button>
          </li>
        </ul>
      </nav>

      <!-- Sidebar Footer -->
      <div class="sidebar-footer">
        <div v-if="isLoggedIn" class="user-info">
          <div class="user-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <div class="user-details">
            <span class="user-name">{{ currentUser?.name || 'User' }}</span>
            <span class="user-email">{{ currentUser?.email || '' }}</span>
          </div>
          <button class="logout-btn" @click="handleLogout" title="Logout">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </button>
        </div>
        <div v-else class="user-info guest-user" @click="navigate('/login')">
          <div class="user-avatar">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
          </div>
          <span class="user-name">Login</span>
        </div>
      </div>
    </aside>

    <!-- Main Content Area -->
    <div class="main-content">
      <!-- Header -->
      <header class="header">
        <div class="header-left">
          <!-- Hamburger Menu Button (Mobile Only) -->
          <button class="hamburger-btn" @click="toggleSidebar" aria-label="Toggle menu">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <h1 class="page-title">{{ route.name || 'Dashboard' }}</h1>
        </div>
        <div class="header-center">
          <!-- Project Selector -->
          <div v-if="currentProject" class="project-selector">
            <div class="project-badge">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <span class="project-name">{{ currentProject.title }}</span>
            <span class="project-status" :class="currentProject.status.toLowerCase()">
              {{ currentProject.status }}
            </span>
          </div>
        </div>
        <div class="header-right">
          <!-- Actions -->
          <button class="header-action" title="Search (Ctrl+K)" @click="openSearch">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </button>
          <button class="header-action" title="Notifications">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </button>
        </div>
      </header>

      <!-- Page Content -->
      <main class="content">
        <router-view />
      </main>
    </div>

    <!-- Global Search Modal -->
    <GlobalSearch v-model="showSearch" />
  </div>
</template>

<style scoped>
/* ========== MAIN LAYOUT ========== */
.main-layout {
  display: flex;
  min-height: 100vh;
  background-color: var(--color-bg-primary);
  transition: background-color var(--transition-base);
}

/* ========== SIDEBAR ========== */
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 260px;
  background: var(--color-bg-elevated);
  border-right: 1px solid var(--color-border);
  box-shadow: 4px 0 20px rgba(44, 36, 22, 0.05);
  display: flex;
  flex-direction: column;
  z-index: 100;
  transition: all var(--transition-base);
}

/* Sidebar Header */
.sidebar-header {
  padding: var(--space-6) var(--space-6) var(--space-4);
  border-bottom: 1px solid var(--color-border-light);
}

.brand {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  transition: color var(--transition-fast);
}

.brand-icon:hover {
  color: var(--color-primary-hover);
}

.brand-name {
  font-family: var(--font-serif);
  font-size: var(--font-size-h4);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
}

/* Navigation */
.sidebar-nav {
  flex: 1;
  padding: var(--space-4) 0;
  overflow-y: auto;
}

.nav-list {
  list-style: none;
  padding: 0 var(--space-4);
  margin: 0;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  width: 100%;
  height: 44px;
  padding: 0 var(--space-4);
  margin-bottom: var(--space-1);
  border: none;
  background: transparent;
  border-radius: var(--radius-md);
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  font-weight: 500;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
  text-align: left;
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--color-primary);
  transform: scaleY(0);
  transition: transform var(--transition-fast);
}

.nav-item:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
}

.nav-item:hover::before {
  transform: scaleY(0.6);
}

.nav-item.active {
  background: var(--color-primary-muted);
  color: var(--color-primary);
}

.nav-item.active::before {
  transform: scaleY(1);
}

.nav-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.nav-item:hover .nav-icon {
  transform: scale(1.1);
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Sidebar Footer */
.sidebar-footer {
  padding: var(--space-4);
  border-top: 1px solid var(--color-border-light);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  transition: all var(--transition-fast);
  cursor: pointer;
}

.user-info:not(.guest-user):hover {
  background: var(--color-bg-secondary);
  border-color: var(--color-border);
}

.guest-user {
  opacity: 0.7;
}

.guest-user:hover {
  opacity: 1;
}

.user-avatar {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg-tertiary);
  border-radius: var(--radius-full);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border-light);
}

.user-details {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  overflow: hidden;
}

.user-name {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-email {
  font-family: var(--font-sans);
  font-size: 11px;
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  background: transparent;
  border-radius: var(--radius-sm);
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
  flex-shrink: 0;
}

.logout-btn:hover {
  background: rgba(155, 44, 44, 0.1);
  color: var(--color-error);
}

/* ========== MAIN CONTENT ========== */
.main-content {
  flex: 1;
  margin-left: 260px;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Header */
.header {
  position: sticky;
  top: 0;
  height: 64px;
  background: var(--color-bg-elevated);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--space-6);
  z-index: 90;
  transition: all var(--transition-base);
}

.header-left,
.header-center,
.header-right {
  display: flex;
  align-items: center;
}

.header-left {
  flex: 0 0 auto;
}

.header-center {
  flex: 1;
  justify-content: center;
}

.header-right {
  flex: 0 0 auto;
  gap: var(--space-2);
}

.page-title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h3);
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  margin: 0;
}

/* Project Selector */
.project-selector {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-4);
  background: var(--color-bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-fast);
}

.project-selector:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-focus);
}

.project-badge {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
}

.project-name {
  font-family: var(--font-sans);
  font-size: var(--font-size-body-sm);
  font-weight: 600;
  color: var(--color-text-primary);
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.project-status {
  font-family: var(--font-sans);
  font-size: 0.75rem;
  font-weight: 600;
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  text-transform: capitalize;
  letter-spacing: 0.02em;
}

.project-status.active,
.project-status.writing {
  background: rgba(74, 124, 89, 0.15);
  color: var(--color-success);
}

.project-status.draft,
.project-status.planning {
  background: rgba(184, 134, 11, 0.15);
  color: var(--color-warning);
}

.project-status.completed {
  background: rgba(139, 90, 43, 0.15);
  color: var(--color-primary);
}

/* Header Actions */
.header-action {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid var(--color-border-light);
  background: var(--color-bg-primary);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.header-action:hover {
  background: var(--color-bg-secondary);
  color: var(--color-text-primary);
  border-color: var(--color-border);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.header-action:active {
  transform: translateY(0);
}

/* Content Area */
.content {
  flex: 1;
  padding: var(--space-6);
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  animation: fadeInUp var(--transition-slow);
}

/* ========== ANIMATIONS ========== */
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

/* ========== RESPONSIVE ========== */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
  }

  .sidebar.sidebar-open {
    transform: translateX(0);
  }

  /* Sidebar Overlay for Mobile */
  .sidebar-overlay {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
    opacity: 0;
    transition: opacity var(--transition-base);
  }

  .sidebar.sidebar-open .sidebar-overlay {
    display: block;
    opacity: 1;
  }

  .main-content {
    margin-left: 0;
  }

  .header-center {
    display: none;
  }

  .page-title {
    font-size: var(--font-size-h4);
  }

  /* Hamburger Button */
  .hamburger-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    margin-right: var(--space-3);
    background: transparent;
    border: none;
    border-radius: var(--radius-md);
    color: var(--color-text-primary);
    cursor: pointer;
    transition: all var(--transition-fast);
  }

  .hamburger-btn:hover {
    background: var(--color-bg-secondary);
  }

  .header-left {
    display: flex;
    align-items: center;
  }
}

/* ========== DARK MODE OVERRIDES ========== */
@media (prefers-color-scheme: dark) {
  .sidebar {
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.25);
  }

  .nav-item.active {
    background: rgba(166, 123, 91, 0.2);
  }

  .project-status.active,
  .project-status.writing {
    background: rgba(74, 124, 89, 0.2);
  }

  .project-status.draft,
  .project-status.planning {
    background: rgba(184, 134, 11, 0.2);
  }

  .project-status.completed {
    background: rgba(166, 123, 91, 0.2);
  }
}
</style>
