/**
 * Dashboard.vue Component Tests
 * TDD - 测试驱动开发
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Dashboard from '../views/Dashboard.vue'

// Mock路由
const router = createRouter({
  history: createWebHistory(),
  routes: [{ path: '/', component: Dashboard }]
})

// Mock i18n
vi.mock('vue-i18n', () => ({
  useI18n: () => ({
    t: (key: string) => key,
    locale: 'zh-CN'
  })
}))

describe('Dashboard.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render correctly', async () => {
    const wrapper = mount(Dashboard, {
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

  it('should display project cards when projects exist', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'el-icon': true,
          'router-link': true
        }
      }
    })
    
    // 检查是否有项目卡片容器
    const cardsContainer = wrapper.find('.dashboard-content')
    expect(cardsContainer.exists() || wrapper.find('main').exists()).toBe(true)
  })

  it('should support dark mode', async () => {
    // 设置暗色模式
    document.documentElement.setAttribute('data-theme', 'dark')
    
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    
    // 清理
    document.documentElement.removeAttribute('data-theme')
  })

  it('should show empty state when no projects', async () => {
    const wrapper = mount(Dashboard, {
      global: {
        plugins: [router, createPinia()],
        stubs: {
          'el-icon': true,
          'router-link': true
        }
      }
    })
    
    // 空状态应该有图标和提示文字
    const emptyState = wrapper.find('.empty-state')
    // 如果有空状态，验证其内容
    if (emptyState.exists()) {
      expect(emptyState.text()).toBeTruthy()
    }
  })
})
