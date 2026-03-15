import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import ChapterList from '../ChapterList.vue'
import type { Chapter, ChapterStatus } from '@/types'

// Mock router
const mockRoutePush = vi.fn()
vi.mock('vue-router', () => ({
  useRoute: () => ({ params: { projectId: 'test-project' } }),
  useRouter: () => ({ push: mockRoutePush })
}))

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      chapter: {
        draft: 'Draft',
        inProgress: 'In Progress',
        completed: 'Completed',
        published: 'Published',
        wordCount: 'words',
        create: 'New Chapter'
      },
      common: {
        noData: 'No Data',
        edit: 'Edit',
        delete: 'Delete'
      },
      publish: {
        publishNow: 'Publish Now'
      }
    }
  }
})

// Helper to create chapters
const createChapter = (overrides: Partial<Chapter> = {}): Chapter => ({
  id: 'chapter-1',
  project_id: 'project-1',
  number: 1,
  title: 'Test Chapter',
  status: 'draft' as ChapterStatus,
  word_count: 1000,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides
})

describe('ChapterList', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const mountComponent = (props = {}) => {
    return mount(ChapterList, {
      global: {
        plugins: [i18n],
      },
      props: {
        chapters: [],
        projectId: 'test-project',
        ...props
      }
    })
  }

  describe('Rendering', () => {
    it('should render empty state when no chapters', () => {
    const wrapper = mountComponent({ chapters: [] })
    
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.empty-state-title').text()).toContain('No Data')
  })

    it('should render list of chapters', () => {
    const chapters: Chapter[] = [
      createChapter({ id: 'chapter-1', number: 1, title: 'Chapter One' }),
      createChapter({ id: 'chapter-2', number: 2, title: 'Chapter Two' })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.findAll('.chapter-item')).toHaveLength(2)
    expect(wrapper.find('.chapter-number').text()).toBe('1')
  })

    it('should display chapter title correctly', () => {
    const chapters: Chapter[] = [
      createChapter({ title: 'The Beginning' })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.chapter-title').text()).toBe('The Beginning')
  })

  it('should display chapter number', () => {
    const chapters: Chapter[] = [
      createChapter({ number: 5 })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.chapter-number').text()).toBe('5')
  })
})

  describe('Status Display', () => {
    const statusCases: { status: ChapterStatus; expectedClass: string }[] = [
      { status: 'draft', expectedClass: 'badge-draft' },
      { status: 'in_progress', expectedClass: 'badge-progress' },
      { status: 'completed', expectedClass: 'badge-success' },
      { status: 'published', expectedClass: 'badge-published' }
    ]

    statusCases.forEach(({ status, expectedClass }) => {
      it(`should display ${status} status with correct styling`, () => {
        const chapters: Chapter[] = [
          createChapter({ status })
        ]
        
        const wrapper = mountComponent({ chapters })
        const statusBadge = wrapper.find('.chapter-status')
        
        expect(statusBadge.classes()).toContain(expectedClass)
      })
    })
  })

  describe('Word Count Formatting', () => {
    it('should format word count with locale string', () => {
    const chapters: Chapter[] = [
      createChapter({ word_count: 5000 })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.meta-item').text()).toContain('5,000')
  })

    it('should handle large word counts', () => {
    const chapters: Chapter[] = [
      createChapter({ word_count: 100000 })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.meta-item').text()).toContain('100,000')
  })
})

  describe('User Interactions', () => {
    it('should emit edit event when edit button clicked', async () => {
    const chapter = createChapter()
    const wrapper = mountComponent({ chapters: [chapter] })
    
    await wrapper.find('.action-edit').trigger('click')
    
    expect(wrapper.emitted('edit')).toBeTruthy()
    expect(wrapper.emitted('edit')![0]).toEqual([chapter])
  })

    it('should emit read event when read button clicked', async () => {
    const chapter = createChapter()
    const wrapper = mountComponent({ chapters: [chapter] })
    
    await wrapper.find('.action-read').trigger('click')
    
    expect(wrapper.emitted('read')).toBeTruthy()
    expect(wrapper.emitted('read')![0]).toEqual([chapter])
  })

    it('should emit delete event when delete button clicked', async () => {
    const chapter = createChapter()
    const wrapper = mountComponent({ chapters: [chapter] })
    
    await wrapper.find('.action-delete').trigger('click')
    
    expect(wrapper.emitted('delete')).toBeTruthy()
    expect(wrapper.emitted('delete')![0]).toEqual([chapter])
  })

    it('should emit publish event for completed chapters', async () => {
    const chapter = createChapter({ status: 'completed' })
    const wrapper = mountComponent({ chapters: [chapter] })
    
    const publishBtn = wrapper.find('.action-publish')
    await publishBtn.trigger('click')
    
    expect(wrapper.emitted('publish')).toBeTruthy()
    expect(wrapper.emitted('publish')![0]).toEqual([chapter])
  })

    it('should not show publish button for non-completed chapters', () => {
    const chapter = createChapter({ status: 'draft' })
    const wrapper = mountComponent({ chapters: [chapter] })
    
    expect(wrapper.find('.action-publish').exists()).toBe(false)
  })

    it('should not show publish button for already published chapters', () => {
    const chapter = createChapter({ status: 'published' })
    const wrapper = mountComponent({ chapters: [chapter] })
    
    expect(wrapper.find('.action-publish').exists()).toBe(false)
  })

    it('should emit read event when Enter key pressed on chapter item', async () => {
    const chapter = createChapter()
    const wrapper = mountComponent({ chapters: [chapter] })
    
    await wrapper.find('.chapter-item').trigger('keydown.enter')
    
    expect(wrapper.emitted('read')).toBeTruthy()
  })
})

  describe('Date Display', () => {
    it('should display formatted date', () => {
    const chapters: Chapter[] = [
      createChapter({ updated_at: '2024-03-15T10:30:00Z' })
    ]
    
    const wrapper = mountComponent({ chapters })
    const dateText = wrapper.findAll('.meta-item')[1]?.text()
    
    // Date formatting depends on locale, just verify it's present
    expect(dateText).toBeTruthy()
  })
})

  describe('Accessibility', () => {
    it('should have correct tabindex on chapter items', () => {
    const chapters: Chapter[] = [createChapter()]
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.chapter-item').attributes('tabindex')).toBe('0')
  })

    it('should have title attributes on action buttons', () => {
    const chapters: Chapter[] = [createChapter()]
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.action-read').attributes('title')).toBeTruthy()
    expect(wrapper.find('.action-edit').attributes('title')).toBeTruthy()
    expect(wrapper.find('.action-delete').attributes('title')).toBeTruthy()
  })
})

  describe('Edge Cases', () => {
    it('should handle empty chapter title gracefully', () => {
    const chapters: Chapter[] = [
      createChapter({ title: '' })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.chapter-title').text()).toBe('')
  })

    it('should handle zero word count', () => {
    const chapters: Chapter[] = [
      createChapter({ word_count: 0 })
    ]
    
    const wrapper = mountComponent({ chapters })
    
    expect(wrapper.find('.meta-item').text()).toContain('0')
  })

    it('should render all action buttons on hover/focus', async () => {
    const chapters: Chapter[] = [createChapter()]
    const wrapper = mountComponent({ chapters })
    
    // Actions should exist but may be hidden
    expect(wrapper.find('.action-read').exists()).toBe(true)
    expect(wrapper.find('.action-edit').exists()).toBe(true)
    expect(wrapper.find('.action-delete').exists()).toBe(true)
  })
})
})
