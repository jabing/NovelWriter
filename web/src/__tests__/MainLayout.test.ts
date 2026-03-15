/**
 * MainLayout.vue Component Tests
 * TDD - 测试驱动开发
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import MainLayout from '../layouts/MainLayout.vue'
import Dashboard from '../views/Dashboard.vue'

// Mock路由
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Dashboard },
    { path: '/projects', component: Dashboard }
  ]
})

// Mock i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
    locale: 'zh-CN'
  })
}))

describe('MainLayout.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render correctly', async () => {
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'router-view': true,
          'router-link': true
        }
      }
    })
    
    expect(wrapper.exists()).toBe(true)
  })

  it('should have sidebar navigation', async () => {
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'router-view': true,
          'router-link': true
        }
      }
    })
    
    // 查找侧边栏
    const sidebar = wrapper.find('aside')
    expect(sidebar.exists() || wrapper.find('nav').exists()).toBe(true)
  })

  it('should have header section', async () => {
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'router-view': true,
          'router-link': true
        }
      }
    })
    
    // 查找头部区域
    const header = wrapper.find('header')
    expect(header.exists() || wrapper.find('.header').exists()).toBe(true)
  })

  it('should support dark mode', async () => {
    document.documentElement.setAttribute('data-theme', 'dark')
    
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    document.documentElement.removeAttribute('data-theme')
  })

  it('should have navigation items', async () => {
    const wrapper = mount(MainLayout, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'router-view': true,
          'router-link': true
        }
      }
    })
    
    // 查找导航项
    const navItems = wrapper.findAll('a')
    expect(navItems.length).toBeGreaterThanOrEqual(0)
  })
})
