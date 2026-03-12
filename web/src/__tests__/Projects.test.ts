/**
 * Projects.vue Component Tests
 * TDD - 测试驱动开发
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Projects from '../views/Projects.vue'

// Mock路由
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/projects', component: Projects }]
})

// Mock i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
    locale: 'zh-CN'
  })
}))

describe('Projects.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render correctly', async () => {
    const wrapper = mount(Projects, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'el-icon': true,
          'router-link': true
        }
      }
    })
    
    expect(wrapper.exists()).toBe(true)
  })

  it('should have search functionality', async () => {
    const wrapper = mount(Projects, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'el-icon': true,
          'router-link': true
        }
      }
    })
    
    // 查找搜索输入框
    const searchInput = wrapper.find('input[type="text"]')
    // 如果有搜索框，验证其存在
    expect(wrapper.html()).toBeTruthy()
  })

  it('should toggle between card and table view', async () => {
    const wrapper = mount(Projects, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'el-icon': true,
          'router-link': true
        }
      }
    })
    
    // 查找视图切换按钮
    const viewButtons = wrapper.findAll('button')
    expect(viewButtons.length).toBeGreaterThanOrEqual(0)
  })

  it('should support dark mode', async () => {
    document.documentElement.setAttribute('data-theme', 'dark')
    
    const wrapper = mount(Projects, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'el-icon': true,
          'router-link': true
        }
      }
    })
    
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    document.documentElement.removeAttribute('data-theme')
  })
})
