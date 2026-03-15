import { createRouter, createWebHistory } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      component: MainLayout,
      children: [
        { path: '', name: 'Dashboard', component: () => import('@/views/Dashboard.vue') },
        { path: 'projects', name: 'Projects', component: () => import('@/views/Projects.vue') },
        { path: 'projects/:id', name: 'ProjectDetail', component: () => import('@/views/ProjectDetail.vue') },
        { path: 'projects/:id/graph/characters', name: 'CharacterGraph', component: () => import('@/views/CharacterGraph.vue') },
        { path: 'projects/:projectId/characters/:characterId', name: 'CharacterDetail', component: () => import('@/views/CharacterDetail.vue') },
        { path: 'writing', name: 'Writing', component: () => import('@/views/Reading.vue') },
        { path: 'reading', name: 'Reading', component: () => import('@/views/Reading.vue') },
        { path: 'agents', name: 'Agents', component: () => import('@/views/Agents.vue') },
        { path: 'publish', name: 'Publish', component: () => import('@/views/Publish.vue') },
        { path: 'comments', name: 'Comments', component: () => import('@/views/Comments.vue') },
        { path: 'settings', name: 'Settings', component: () => import('@/views/Settings.vue') },
        { path: 'analytics', name: 'Analytics', component: () => import('@/views/Analytics.vue') }
      ]
    },
    // Full-screen reader (outside MainLayout)
    {
      path: '/reader/:chapter?/:total?',
      name: 'Reader',
      component: () => import('@/views/ReaderView.vue')
    }
  ]
})

export default router
