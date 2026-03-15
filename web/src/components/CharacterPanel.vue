<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Character } from '@/types';

const props = defineProps<{
  characters: Character[];
  projectId: string;
}>();

const emit = defineEmits<{
  (e: 'edit', character: Character): void;
  (e: 'delete', character: Character): void;
  (e: 'view', character: Character): void;
}>();

const { t } = useI18n();

// Get initials from character name for avatar placeholder
const getInitials = (name: string): string => {
  return name
    .split(' ')
    .map((word) => word[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
};

// Role badge color mapping
const roleColors: Record<string, string> = {
  protagonist: 'var(--color-primary)',
  antagonist: 'var(--color-error)',
  supporting: 'var(--color-secondary)',
  minor: 'var(--color-text-tertiary)'
};

// Status badge style mapping
const statusStyles: Record<string, { bg: string; color: string }> = {
  active: { bg: 'rgba(52, 199, 89, 0.12)', color: 'var(--color-success)' },
  minor: { bg: 'rgba(90, 200, 250, 0.12)', color: 'var(--color-info)' },
  archived: { bg: 'rgba(174, 174, 178, 0.12)', color: 'var(--color-text-tertiary)' }
};

// Get role label from i18n
const getRoleLabel = (role: string): string => {
  return t(`character.${role}`);
};

// Handle card actions
const handleEdit = (character: Character): void => {
  emit('edit', character);
};

const handleDelete = (character: Character): void => {
  emit('delete', character);
};

const handleView = (character: Character): void => {
  emit('view', character);
};
</script>

<template>
  <div class="character-panel">
    <!-- Header -->
    <div class="panel-header">
      <h3 class="panel-title">{{ t('character.title') }}</h3>
      <span class="character-count">{{ characters.length }}</span>
    </div>

    <!-- Character Grid -->
    <div v-if="characters.length > 0" class="character-grid">
      <article
        v-for="character in characters"
        :key="character.id"
        class="character-card"
        tabindex="0"
        @click="handleView(character)"
        @keydown.enter="handleView(character)"
      >
        <!-- Avatar Section -->
        <div class="avatar-section">
          <div
            v-if="character.avatar_url"
            class="avatar-image"
            :style="{ backgroundImage: `url(${character.avatar_url})` }"
          />
          <div
            v-else
            class="avatar-placeholder"
            :style="{ backgroundColor: roleColors[character.role as string] || roleColors.minor }"
          >
            {{ getInitials(character.name) }}
          </div>
        </div>

        <!-- Info Section -->
        <div class="info-section">
          <h4 class="character-name">{{ character.name }}</h4>
          <div class="character-meta">
            <span
              class="role-badge"
              :style="{ backgroundColor: `${roleColors[character.role as string]}20`, color: roleColors[character.role as string] }"
            >
              {{ getRoleLabel(character.role) }}
            </span>
            <span
              class="status-badge"
              :style="statusStyles[character.status] || statusStyles.active"
            >
              {{ t(`character.${character.status}`) }}
            </span>
          </div>
          <p v-if="character.description" class="character-description">
            {{ character.description }}
          </p>
        </div>

        <!-- Relationships Section -->
        <div
          v-if="character?.relationships && character.relationships.length > 0"
          class="relationships-section"
        >
          <div class="relationship-line" />
          <span class="relationship-count">
            {{ character.relationships.length }} {{ t('character.relationships') }}
          </span>
        </div>

        <!-- Actions -->
        <div class="card-actions">
          <button
            type="button"
            class="action-btn"
            :aria-label="t('common.edit')"
            @click.stop="handleEdit(character)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
            </svg>
          </button>
          <button
            type="button"
            class="action-btn action-btn--danger"
            :aria-label="t('common.delete')"
            @click.stop="handleDelete(character)"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M3 6h18" />
              <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <line x1="10" y1="11" x2="10" y2="17" />
              <line x1="14" y1="11" x2="14" y2="17" />
            </svg>
          </button>
        </div>
      </article>
    </div>

    <!-- Empty State -->
    <div v-else class="empty-state">
      <div class="empty-state-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="12" cy="7" r="4" />
          <path d="M5.5 21a7.5 7.5 0 0 1 13 0" />
        </svg>
      </div>
      <h4 class="empty-state-title">{{ t('character.noCharacters') }}</h4>
      <p class="empty-state-description">{{ t('character.noCharactersDesc') }}</p>
    </div>
  </div>
</template>

<style scoped>
.character-panel {
  width: 100%;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-6);
}

.panel-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0;
}

.character-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 24px;
  height: 24px;
  padding: 0 var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-secondary);
  background: var(--color-border-light);
  border-radius: var(--radius-full);
}

/* Character Grid */
.character-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-5);
}

/* Character Card */
.character-card {
  position: relative;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
  padding: var(--space-5);
  cursor: pointer;
  transition: transform var(--transition-base), box-shadow var(--transition-base);
  outline: none;
}

.character-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-card-hover);
}

.character-card:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Avatar Section */
.avatar-section {
  display: flex;
  align-items: center;
  margin-bottom: var(--space-4);
}

.avatar-image,
.avatar-placeholder {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-image {
  background-size: cover;
  background-position: center;
}

.avatar-placeholder {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: white;
  background: var(--gradient-primary);
}

/* Info Section */
.info-section {
  flex: 1;
  min-width: 0;
}

.character-name {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.character-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-bottom: var(--space-3);
}

.role-badge,
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
}

.character-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  line-height: var(--line-height-relaxed);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* Relationships Section */
.relationships-section {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding-top: var(--space-3);
  margin-top: var(--space-3);
  border-top: 1px solid var(--color-border-light);
}

.relationship-line {
  width: 12px;
  height: 2px;
  background: var(--color-border);
  border-radius: var(--radius-full);
}

.relationship-count {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* Card Actions */
.card-actions {
  position: absolute;
  top: var(--space-3);
  right: var(--space-3);
  display: flex;
  gap: var(--space-2);
  opacity: 0;
  transition: opacity var(--transition-fast);
}

.character-card:hover .card-actions,
.character-card:focus-within .card-actions {
  opacity: 1;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  padding: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.action-btn:hover {
  background: var(--color-border-light);
  color: var(--color-text-primary);
}

.action-btn--danger:hover {
  background: rgba(255, 59, 48, 0.1);
  border-color: var(--color-error);
  color: var(--color-error);
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-12) var(--space-8);
  text-align: center;
  background: var(--color-surface);
  border-radius: var(--radius-xl);
  border: 1px dashed var(--color-border);
}

.empty-state-icon {
  color: var(--color-text-tertiary);
  margin-bottom: var(--space-4);
}

.empty-state-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
  margin: 0 0 var(--space-2) 0;
}

.empty-state-description {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
  margin: 0;
  max-width: 280px;
}

/* Responsive */
@media (max-width: 640px) {
  .character-grid {
    grid-template-columns: 1fr;
  }

  .card-actions {
    opacity: 1;
  }
}
</style>
