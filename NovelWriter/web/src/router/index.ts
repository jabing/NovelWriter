import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue'), meta: { requiresAuth: true } },
        { path: 'projects', name: 'Projects', component: () => import('@/views/Projects.vue'), meta: { requiresAuth: true } },
        { path: 'projects/:id', name: 'ProjectDetail', component: () => import('@/views/ProjectDetail.vue'), meta: { requiresAuth: true } },
        { path: 'projects/:projectId/characters/:characterId', name: 'CharacterDetail', component: () => import('@/views/CharacterDetail.vue'), meta: { requiresAuth: true } },
        { path: 'writing', name: 'Writing', component: () => import('@/views/Writing.vue'), meta: { requiresAuth: true } },
        { path: 'reading', name: 'Reading', component: () => import('@/views/Reading.vue'), meta: { requiresAuth: true } },
        { path: 'agents', name: 'Agents', component: () => import('@/views/Agents.vue'), meta: { requiresAuth: true } },
        { path: 'publish', name: 'Publish', component: () => import('@/views/Publish.vue'), meta: { requiresAuth: true } },
        { path: 'comments', name: 'Comments', component: () => import('@/views/Comments.vue'), meta: { requiresAuth: true } },
        { path: 'settings', name: 'Settings', component: () => import('@/views/Settings.vue'), meta: { requiresAuth: true } },
        { path: 'analytics', name: 'Analytics', component: () => import('@/views/Analytics.vue'), meta: { requiresAuth: true } }
      ]
    },
    // Full-screen reader (outside MainLayout)
    {
      path: '/reader/:chapter?/:total?',
      name: 'Reader',
      component: () => import('@/views/ReaderView.vue'),
      meta: { requiresAuth: false }
    }
  ]
})

// Route guard for authentication
router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  
  if (!authStore.token) {
    authStore.loadFromStorage()
  }
  
  const requiresAuth = to.meta.requiresAuth ?? true
  
  if (requiresAuth && !authStore.isLoggedIn) {
    next({ name: 'Login', query: { redirect: to.fullPath } })
  } else if (to.name === 'Login' && authStore.isLoggedIn) {
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
