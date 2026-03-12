<template>
  <div class="comments-view">
    <div class="container">
      <h1 class="page-title">Comments Feed</h1>
      
      <div class="comments-container">
        <div 
          v-for="comment in comments" 
          :key="comment.id" 
          class="comment-card card fade-in"
        >
          <div class="comment-header">
            <div class="comment-author">
              <span class="author-name">{{ comment.author }}</span>
              <span class="platform-badge">{{ comment.platform }}</span>
            </div>
            <div class="comment-timestamp">{{ comment.timestamp }}</div>
          </div>
          
          <div class="comment-content">
            {{ comment.content }}
          </div>
          
          <div class="comment-footer">
            <div class="sentiment-badge" :class="`badge-${comment.sentiment}`">
              {{ comment.sentiment }}
            </div>
            
            <button class="btn btn-secondary auto-reply-btn">
              <span>Reply</span>
              <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

// Define the Comment interface as specified in the task
interface Comment {
  id: string
  platform: string
  content: string
  sentiment: 'positive' | 'neutral' | 'negative'
  author: string
  timestamp: string
}

// Mock data for demonstration (as per requirements - don't fetch data internally)
const comments = ref<Comment[]>([
  {
    id: '1',
    platform: 'Twitter',
    content: 'This story is absolutely amazing! The character development is fantastic and the plot keeps me on the edge of my seat.',
    sentiment: 'positive',
    author: 'Sarah Chen',
    timestamp: '2 hours ago'
  },
  {
    id: '2',
    platform: 'Reddit',
    content: 'I have some feedback about the pacing in chapter 3. It felt a bit rushed.',
    sentiment: 'neutral',
    author: 'LiteraryReader',
    timestamp: '5 hours ago'
  },
  {
    id: '3',
    platform: 'Goodreads',
    content: 'The writing style is beautiful, but I wish there was more world-building.',
    sentiment: 'positive',
    author: 'BookLover23',
    timestamp: '1 day ago'
  },
  {
    id: '4',
    platform: 'Twitter',
    content: 'I\'m really disappointed with the ending. It felt unresolved.',
    sentiment: 'negative',
    author: 'CritiqueKing',
    timestamp: '3 days ago'
  },
  {
    id: '5',
    platform: 'Instagram',
    content: 'Just finished reading and I\'m blown away! Can\'t wait for the next chapter!',
    sentiment: 'positive',
    author: 'StoryFanatic',
    timestamp: '1 week ago'
  }
])
</script>

<style scoped>
.comments-view {
  padding: var(--space-10) var(--space-6);
}

.container {
  max-width: 800px;
  margin: 0 auto;
}

.page-title {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  margin-bottom: var(--space-8);
  color: var(--color-text-primary);
}

.comments-container {
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}

.comment-card {
  padding: var(--space-6);
  border: 1px solid var(--color-border);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.author-name {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.platform-badge {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--color-text-tertiary);
  background: var(--color-border-light);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
}

.comment-timestamp {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

.comment-content {
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-secondary);
  margin-bottom: var(--space-4);
}

.comment-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sentiment-badge {
  padding: var(--space-1) var(--space-3);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-full);
}

.badge-positive {
  background: rgba(52, 199, 89, 0.12);
  color: var(--color-success);
}

.badge-neutral {
  background: rgba(90, 200, 250, 0.12);
  color: var(--color-info);
}

.badge-negative {
  background: rgba(255, 59, 48, 0.12);
  color: var(--color-error);
}

.auto-reply-btn {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-sm);
  min-height: 36px;
}

.icon {
  width: 16px;
  height: 16px;
}
</style>