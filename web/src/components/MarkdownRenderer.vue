<template>
  <div 
    class="markdown-renderer" 
    :class="themeClass"
    v-html="sanitizedHtml"
  ></div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

// Props
const props = withDefaults(
  defineProps<{
    content: string
    theme?: 'light' | 'sepia' | 'dark'
  }>(),
  {
    theme: 'light'
  }
)

// Emits
const emit = defineEmits<{
  rendered: [html: string]
}>()

// Configure marked options
marked.setOptions({
  breaks: true, // Convert line breaks to <br>
  gfm: true, // GitHub Flavored Markdown
})

// Parse and sanitize markdown
const sanitizedHtml = computed(() => {
  if (!props.content) return ''
  
  // Parse markdown to HTML
  const rawHtml = marked.parse(props.content) as string
  
  // Sanitize HTML for security
  const cleanHtml = DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: [
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'p', 'br', 'hr',
      'ul', 'ol', 'li',
      'blockquote', 'pre', 'code',
      'strong', 'em', 'del', 's',
      'a', 'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'div', 'span'
    ],
    ALLOWED_ATTR: [
      'href', 'src', 'alt', 'title',
      'class', 'id'
    ]
  })
  
  // Emit rendered HTML
  emit('rendered', cleanHtml)
  
  return cleanHtml
})

// Theme class
const themeClass = computed(() => `markdown-renderer--${props.theme}`)
</script>

<style scoped>
.markdown-renderer {
  font-family: var(--font-family);
  font-size: var(--font-size-base);
  line-height: var(--line-height-relaxed);
  color: var(--color-text-primary);
  max-width: 100%;
  word-wrap: break-word;
}

/* Theme Variants */
.markdown-renderer--light {
  background-color: var(--color-surface);
  color: var(--color-text-primary);
}

.markdown-renderer--sepia {
  background-color: #f4ecd8;
  color: #433422;
}

.markdown-renderer--dark {
  background-color: #1a1a1a;
  color: #e0e0e0;
}

/* Headings */
.markdown-renderer :deep(h1) {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  margin: var(--space-8) 0 var(--space-4);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
}

.markdown-renderer :deep(h2) {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-semibold);
  margin: var(--space-6) 0 var(--space-3);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
}

.markdown-renderer :deep(h3) {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-semibold);
  margin: var(--space-5) 0 var(--space-3);
  line-height: var(--line-height-tight);
}

.markdown-renderer :deep(h4) {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-medium);
  margin: var(--space-4) 0 var(--space-2);
  line-height: var(--line-height-tight);
}

.markdown-renderer :deep(h5) {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  margin: var(--space-3) 0 var(--space-2);
}

.markdown-renderer :deep(h6) {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  margin: var(--space-3) 0 var(--space-2);
  color: var(--color-text-secondary);
}

/* Paragraphs and Text */
.markdown-renderer :deep(p) {
  margin: var(--space-4) 0;
  line-height: var(--line-height-relaxed);
}

.markdown-renderer :deep(strong) {
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}

.markdown-renderer :deep(em) {
  font-style: italic;
}

.markdown-renderer :deep(del),
.markdown-renderer :deep(s) {
  text-decoration: line-through;
  color: var(--color-text-tertiary);
}

/* Lists */
.markdown-renderer :deep(ul),
.markdown-renderer :deep(ol) {
  margin: var(--space-4) 0;
  padding-left: var(--space-6);
}

.markdown-renderer :deep(li) {
  margin: var(--space-2) 0;
  line-height: var(--line-height-normal);
}

.markdown-renderer :deep(ul) {
  list-style-type: disc;
}

.markdown-renderer :deep(ol) {
  list-style-type: decimal;
}

.markdown-renderer :deep(ul ul) {
  list-style-type: circle;
}

.markdown-renderer :deep(ul ul ul) {
  list-style-type: square;
}

/* Links */
.markdown-renderer :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all var(--transition-fast);
}

.markdown-renderer :deep(a:hover) {
  color: var(--color-primary-dark);
  border-bottom-color: var(--color-primary);
}

/* Images */
.markdown-renderer :deep(img) {
  max-width: 100%;
  height: auto;
  display: block;
  margin: var(--space-6) auto;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-md);
}

/* Blockquotes */
.markdown-renderer :deep(blockquote) {
  margin: var(--space-6) 0;
  padding: var(--space-4) var(--space-6);
  border-left: 4px solid var(--color-primary);
  background-color: var(--color-border-light);
  border-radius: var(--radius-md);
  font-style: italic;
}

.markdown-renderer :deep(blockquote p) {
  margin: var(--space-2) 0;
}

/* Code Blocks */
.markdown-renderer :deep(code) {
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  font-size: 0.9em;
  background-color: var(--color-border-light);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-sm);
  color: var(--color-text-primary);
}

.markdown-renderer :deep(pre) {
  margin: var(--space-6) 0;
  padding: var(--space-4);
  background-color: #f5f5f5;
  border-radius: var(--radius-md);
  overflow-x: auto;
  border: 1px solid var(--color-border);
}

.markdown-renderer :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-size: var(--font-size-sm);
  line-height: var(--line-height-normal);
}

/* Horizontal Rule */
.markdown-renderer :deep(hr) {
  margin: var(--space-8) 0;
  border: none;
  border-top: 2px solid var(--color-border);
}

/* Tables */
.markdown-renderer :deep(table) {
  width: 100%;
  margin: var(--space-6) 0;
  border-collapse: collapse;
  border-radius: var(--radius-md);
  overflow: hidden;
}

.markdown-renderer :deep(thead) {
  background-color: var(--color-border-light);
}

.markdown-renderer :deep(th) {
  padding: var(--space-3) var(--space-4);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  border-bottom: 2px solid var(--color-border);
}

.markdown-renderer :deep(td) {
  padding: var(--space-3) var(--space-4);
  border-bottom: 1px solid var(--color-border);
}

.markdown-renderer :deep(tbody tr:last-child td) {
  border-bottom: none;
}

/* Dark Theme Adjustments */
.markdown-renderer--dark :deep(code) {
  background-color: #2a2a2a;
  color: #e0e0e0;
}

.markdown-renderer--dark :deep(pre) {
  background-color: #2a2a2a;
  border-color: #3a3a3a;
}

.markdown-renderer--dark :deep(blockquote) {
  background-color: #2a2a2a;
  border-left-color: var(--color-primary);
}

.markdown-renderer--dark :deep(a) {
  color: #4da6ff;
}

.markdown-renderer--dark :deep(a:hover) {
  color: #66b3ff;
}

.markdown-renderer--dark :deep(th) {
  background-color: #2a2a2a;
}

.markdown-renderer--dark :deep(hr) {
  border-top-color: #3a3a3a;
}

.markdown-renderer--dark :deep(thead) {
  background-color: #2a2a2a;
}

.markdown-renderer--dark :deep(td) {
  border-bottom-color: #3a3a3a;
}

/* Sepia Theme Adjustments */
.markdown-renderer--sepia :deep(code) {
  background-color: #e6dcc6;
  color: #433422;
}

.markdown-renderer--sepia :deep(pre) {
  background-color: #e6dcc6;
  border-color: #d4c4a8;
}

.markdown-renderer--sepia :deep(blockquote) {
  background-color: #e6dcc6;
  border-left-color: #8b7355;
}

.markdown-renderer--sepia :deep(a) {
  color: #6b5d4f;
}

.markdown-renderer--sepia :deep(a:hover) {
  color: #8b7355;
}

.markdown-renderer--sepia :deep(th) {
  background-color: #e6dcc6;
}

.markdown-renderer--sepia :deep(hr) {
  border-top-color: #d4c4a8;
}

.markdown-renderer--sepia :deep(thead) {
  background-color: #e6dcc6;
}

.markdown-renderer--sepia :deep(td) {
  border-bottom-color: #d4c4a8;
}

/* First paragraph - no top margin */
.markdown-renderer :deep(p:first-child) {
  margin-top: 0;
}

/* Last element - no bottom margin */
.markdown-renderer :deep(*:last-child) {
  margin-bottom: 0;
}
</style>
