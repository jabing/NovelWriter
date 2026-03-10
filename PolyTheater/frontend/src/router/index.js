import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/HomeView.vue')
  },
  {
    path: '/projects',
    name: 'Projects',
    component: () => import('../views/ProjectsView.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/DashboardEnhanced.vue')
  },
  {
    path: '/story/:projectId',
    name: 'StoryWorld',
    component: () => import('../views/StoryWorld.vue')
  },
  {
    path: '/story/:projectId/chapter/:chapterId',
    name: 'ChapterEditor',
    component: () => import('../views/ChapterEditor.vue')
  },
  {
    path: '/characters',
    name: 'Characters',
    component: () => import('../views/CharactersView.vue')
  },
  {
    path: '/narrative',
    name: 'Narrative',
    component: () => import('../views/NarrativeView.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const legacyRoutesNeedingProjectContext = ['/characters', '/narrative']

router.beforeEach((to, _from, next) => {
  if (legacyRoutesNeedingProjectContext.includes(to.path)) {
    next()
  } else {
    next()
  }
})

export default router
