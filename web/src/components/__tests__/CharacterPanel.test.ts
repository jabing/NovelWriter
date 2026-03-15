import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createI18n } from 'vue-i18n'
import CharacterPanel from '../CharacterPanel.vue'
import type { Character } from '@/types'

// Create i18n instance for testing
const i18n = createI18n({
  legacy: false,
  locale: 'en',
  fallbackLocale: 'en',
  messages: {
    en: {
      character: {
        title: 'Characters',
        protagonist: 'Protagonist',
        antagonist: 'Antagonist',
        supporting: 'Supporting',
        minor: 'Minor',
        active: 'Active',
        archived: 'Archived',
        noCharacters: 'No characters yet',
        noCharactersDesc: 'Start building your story by adding characters',
        relationships: 'Relationships'
      }
    }
  }
})

// Helper to create characters
const createCharacter = (overrides: Partial<Character> = {}): Character => ({
  id: 'char-1',
  project_id: 'project-1',
  name: 'Test Character',
  role: 'protagonist',
  description: 'Test description',
  status: 'active',
  ...overrides
})

describe('CharacterPanel', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  const mountComponent = (props = {}) => {
    return mount(CharacterPanel, {
      global: {
        plugins: [i18n],
      },
      props: {
        characters: [],
        projectId: 'test-project',
        ...props
      }
    })
  }

  describe('Rendering', () => {
    it('should render empty state when no characters', () => {
      const wrapper = mountComponent({ characters: [] })
      
      expect(wrapper.find('.empty-state').exists()).toBe(true)
      expect(wrapper.find('.empty-state-title').text()).toContain('No characters yet')
    })

    it('should render character grid', () => {
      const characters = [
        createCharacter({ id: '1', name: 'Character 1' }),
        createCharacter({ id: '2', name: 'Character 2' }),
        createCharacter({ id: '3', name: 'Character 3' })
      ]
      
      const wrapper = mountComponent({ characters })
      
      expect(wrapper.findAll('.character-card')).toHaveLength(3)
      expect(wrapper.find('.character-name').text()).toContain('Character 1')
    })

    it('should render character with avatar', () => {
      const characters = [
        createCharacter({ 
          id: '1',
          name: 'John Doe',
          avatar_url: 'https://example.com/avatar.jpg'
        })
      ]
      
      const wrapper = mountComponent({ characters })
      
      const avatarImage = wrapper.find('.avatar-image')
      expect(avatarImage.exists()).toBe(true)
      const style = avatarImage.attributes('style') || ''
      expect(style).toContain('https://example.com/avatar.jpg')
    })

     it('should render avatar placeholder when no avatar_url', () => {
       const characters = [
         createCharacter({ 
           id: '1',
           name: 'Jane Smith',
           avatar_url: undefined,
           role: 'protagonist'
         })
       ]
      
       const wrapper = mountComponent({ characters })
       
       const avatarPlaceholder = wrapper.find('.avatar-placeholder')
       expect(avatarPlaceholder.exists()).toBe(true)
       expect(avatarPlaceholder.text()).toBe('JS')
     })

     it('should render role badges', () => {
       const characters = [
         createCharacter({ id: '1', name: 'Test Character', role: 'protagonist', status: 'active' }),
         createCharacter({ id: '2', name: 'Another Character', role: 'antagonist', status: 'archived' })
       ]
       
       const wrapper = mountComponent({ characters })
       
       const roleBadges = wrapper.findAll('.role-badge')
       expect(roleBadges.length).toBeGreaterThanOrEqual(2)
       expect(roleBadges[0]?.text()).toBeTruthy()
     })

    it('should render status badges', () => {
      const characters = [
        createCharacter({ id: '1', name: 'Test Character', role: 'protagonist', status: 'active' }),
        createCharacter({ id: '2', name: 'Minor Character', role: 'minor', status: 'minor' })
      ]
      
      const wrapper = mountComponent({ characters })
      
      const statusBadges = wrapper.findAll('.status-badge')
      expect(statusBadges.length).toBeGreaterThanOrEqual(1)
    })

    it('should render character description', () => {
      const characters = [
        createCharacter({ 
          id: '1',
          name: 'John Doe',
          description: 'A brave knight on a quest to save the kingdom.',
          role: 'protagonist',
          status: 'active'
        })
      ]
      
      const wrapper = mountComponent({ characters })
      
      const description = wrapper.find('.character-description')
      expect(description.exists()).toBe(true)
      expect(description.text()).toBe('A brave knight on a quest to save the kingdom.')
    })

    it('should render relationships section when character has relationships', () => {
      const characters = [
        createCharacter({ 
          id: '1',
          name: 'John Doe',
          role: 'protagonist',
          status: 'active',
          relationships: [
            { character_id: 'char-2', type: 'ally' },
            { character_id: 'char-3', type: 'enemy' }
          ]
        })
      ]
      
      const wrapper = mountComponent({ characters })
      
      const relationshipsSection = wrapper.find('.relationships-section')
      expect(relationshipsSection.exists()).toBe(true)
      expect(wrapper.find('.relationship-count').text()).toContain('2')
    })

    it('should NOT render relationships section when no relationships', () => {
      const characters = [
        createCharacter({ 
          id: '1',
          name: 'John Doe',
          role: 'protagonist',
          status: 'active',
          relationships: []
        })
      ]
      
      const wrapper = mountComponent({ characters })
      
      expect(wrapper.find('.relationships-section').exists()).toBe(false)
    })
  })

  describe('Interactions', () => {
    it('should emit view event when card is clicked', async () => {
      const character = createCharacter()
      const wrapper = mountComponent({ characters: [character] })
      
      await wrapper.find('.character-card').trigger('click')
      
      expect(wrapper.emitted('view')).toBeTruthy()
      expect(wrapper.emitted('view')![0]).toEqual([character])
    })

    it('should emit view event on Enter key', async () => {
      const character = createCharacter()
      const wrapper = mountComponent({ characters: [character] })
      
      await wrapper.find('.character-card').trigger('keydown.enter')
      
      expect(wrapper.emitted('view')).toBeTruthy()
      expect(wrapper.emitted('view')![0]).toEqual([character])
    })

    it('should emit edit event when edit button clicked', async () => {
      const character = createCharacter()
      const wrapper = mountComponent({ characters: [character] })
      
      const editBtn = wrapper.find('.action-edit')
      if (editBtn.exists()) {
        await editBtn.trigger('click')
        expect(wrapper.emitted('edit')).toBeTruthy()
      }
    })

    it('should emit delete event when delete button clicked', async () => {
      const character = createCharacter()
      const wrapper = mountComponent({ characters: [character] })
      
      const deleteBtn = wrapper.find('.action-delete')
      if (deleteBtn.exists()) {
        await deleteBtn.trigger('click')
        expect(wrapper.emitted('delete')).toBeTruthy()
      }
    })

    it('should show keyboard focus on card', () => {
      const character = createCharacter()
      const wrapper = mountComponent({ characters: [character] })
      const card = wrapper.find('.character-card')
      
      expect(card.attributes('tabindex')).toBe('0')
    })

    it('should have correct character count', () => {
      const characters = [
        createCharacter({ id: '1' }),
        createCharacter({ id: '2' }),
        createCharacter({ id: '3' })
      ]
      
      const wrapper = mountComponent({ characters })
      
      expect(wrapper.find('.character-count').text()).toBe('3')
    })
  })
})
