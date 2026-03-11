<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import {
  ArrowLeft,
  ArrowRight,
  ArrowDown,
  Sunny,
  Moon,
  Setting,
  Close
} from '@element-plus/icons-vue';

// Route params
const route = useRoute();
const router = useRouter();

// Reader state
const currentChapter = ref<number>(1);
const totalChapters = ref<number>(10);
const scrollProgress = ref<number>(0);
const isNavVisible = ref<boolean>(true);
const isSettingsOpen = ref<boolean>(false);
const lastScrollY = ref<number>(0);
const scrollTimeout = ref<ReturnType<typeof setTimeout> | null>(null);

// Theme and font settings
const theme = ref<'light' | 'sepia' | 'dark'>('light');
const fontSize = ref<number>(18);
const lineHeight = ref<number>(1.8);

// Chapter content (placeholder - would come from route params/store)
const chapterContent = ref<string>(`
  <p>The morning sun cast long shadows across the cobblestone streets of Aldermere, painting the ancient buildings in shades of gold and amber. Elena pulled her cloak tighter against the autumn chill, her breath visible in the crisp air as she made her way toward the market square.</p>
  
  <p>She had lived in this city her entire life, yet something felt different today. Perhaps it was the peculiar dream that had woken her before dawn—a vision of crumbling towers and a voice calling her name across impossible distances. Or perhaps it was simply the changing of seasons, that time of year when the veil between worlds grew thin.</p>
  
  <p>The market was already bustling when she arrived. Merchants called out their wares, the smell of fresh bread mingled with spices from distant lands, and somewhere a lutist played a haunting melody that seemed to echo from another time entirely.</p>
  
  <h2>A Stranger's Arrival</h2>
  
  <p>It was then that she noticed him—a figure cloaked in midnight blue, standing perfectly still amidst the chaos of the crowd. While others hurried past with their baskets and burdens, this stranger seemed frozen in time, his face hidden beneath a hood that absorbed the morning light.</p>
  
  <p>Elena's grandmother had always warned her about strangers, especially those who seemed to exist outside the normal flow of the world. "The old blood remembers," she would say, her eyes distant with memories Elena could never quite understand. "When the shadows grow long and the world turns strange, trust only what your heart knows to be true."</p>
  
  <p>But something drew her forward, an invisible thread connecting her to this mysterious figure. As she approached, she could see that his cloak was embroidered with symbols she didn't recognize—ancient sigils that seemed to shift and move when she wasn't looking directly at them.</p>
  
  <blockquote>
    <p>"You feel it too, don't you?" The voice came from nowhere and everywhere, resonating in her bones rather than reaching her ears. "The calling. The awakening."</p>
  </blockquote>
  
  <p>Elena stopped, her heart racing. This was no ordinary encounter. This was the moment her grandmother had prepared her for, though she had never believed it would actually come to pass.</p>
  
  <h2>The Choice</h2>
  
  <p>"I don't understand," she managed, her voice barely a whisper. "Understand what? Who are you?"</p>
  
  <p>The figure raised a hand, and the world around them seemed to slow. The lutist's melody stretched into an endless note, the merchants' calls became distant murmurs, and the very air grew heavy with possibility.</p>
  
  <p>"I am a messenger, nothing more. But you—" the stranger paused, and Elena sensed rather than saw a smile beneath that impenetrable hood, "—you are the key. The one we have waited for across centuries of blood and shadow."</p>
  
  <p>He extended a hand toward her, palm up. Resting in his gloved palm was a single object: a silver compass, its face covered in the same shifting symbols as his cloak. Its needle spun wildly, then stopped, pointing directly at Elena's heart.</p>
  
  <p>"Take it," the stranger said. "Your journey begins now. But know this—once you step onto this path, there is no returning to the life you knew. The worlds will open to you, both their wonders and their terrors. You will see truths that will shake the foundations of everything you believe."</p>
  
  <p>Elena looked at the compass, then at the stranger, then back at the ordinary life continuing around her—oblivious to this moment of impossible choice. The market sounds seemed distant now, like memories of another lifetime.</p>
  
  <p>Her grandmother's voice echoed in her mind: "When the moment comes, do not hesitate. The old blood knows the way."</p>
  
  <p>She reached out and took the compass.</p>
`);

// Theme configurations
const themeConfigs = {
  light: {
    label: 'Light',
    icon: Sunny,
    bg: '#FFFFFF',
    text: '#1D1D1F',
    secondary: '#86868B',
    border: '#E5E5EA'
  },
  sepia: {
    label: 'Sepia',
    icon: Sunny,
    bg: '#F4ECD8',
    text: '#3B341F',
    secondary: '#7A6F56',
    border: '#D9CEB8'
  },
  dark: {
    label: 'Dark',
    icon: Moon,
    bg: '#1C1C1E',
    text: '#E5E5E7',
    secondary: '#8E8E93',
    border: '#38383A'
  }
};

// Font size options
const fontSizes = [14, 16, 18, 20, 22, 24];

// Computed styles for theme
const themeStyles = computed(() => ({
  '--reader-bg': themeConfigs[theme.value].bg,
  '--reader-text': themeConfigs[theme.value].text,
  '--reader-secondary': themeConfigs[theme.value].secondary,
  '--reader-border': themeConfigs[theme.value].border,
  '--reader-font-size': `${fontSize.value}px`,
  '--reader-line-height': lineHeight.value
}));

// Chapter navigation
const canGoPrev = computed(() => currentChapter.value > 1);
const canGoNext = computed(() => currentChapter.value < totalChapters.value);

function goToPrevChapter() {
  if (canGoPrev.value) {
    currentChapter.value--;
    scrollToTop();
  }
}

function goToNextChapter() {
  if (canGoNext.value) {
    currentChapter.value++;
    scrollToTop();
  }
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Scroll handling for nav visibility
function handleScroll() {
  const currentScrollY = window.scrollY;
  const documentHeight = document.documentElement.scrollHeight - window.innerHeight;
  
  // Calculate progress
  scrollProgress.value = documentHeight > 0 ? (currentScrollY / documentHeight) * 100 : 0;
  
  // Show/hide nav based on scroll direction
  if (currentScrollY > lastScrollY.value && currentScrollY > 100) {
    // Scrolling down - hide nav
    isNavVisible.value = false;
  } else {
    // Scrolling up - show nav
    isNavVisible.value = true;
  }
  
  lastScrollY.value = currentScrollY;
  
  // Clear existing timeout
  if (scrollTimeout.value) {
    clearTimeout(scrollTimeout.value);
  }
  
  // Show nav after scroll stops
  scrollTimeout.value = setTimeout(() => {
    isNavVisible.value = true;
  }, 1500);
}

// Theme handling
function setTheme(newTheme: 'light' | 'sepia' | 'dark') {
  theme.value = newTheme;
  // Save preference
  localStorage.setItem('reader-theme', newTheme);
}

// Font size handling
function setFontSize(size: number) {
  fontSize.value = size;
  localStorage.setItem('reader-font-size', size.toString());
}

// Toggle settings panel
function toggleSettings() {
  isSettingsOpen.value = !isSettingsOpen.value;
}

function closeSettings() {
  isSettingsOpen.value = false;
}

// Exit reader
function exitReader() {
  router.back();
}

// Keyboard navigation
function handleKeydown(e: KeyboardEvent) {
  switch (e.key) {
    case 'ArrowLeft':
      if (canGoPrev.value) goToPrevChapter();
      break;
    case 'ArrowRight':
      if (canGoNext.value) goToNextChapter();
      break;
    case 'Escape':
      if (isSettingsOpen.value) {
        closeSettings();
      } else {
        exitReader();
      }
      break;
  }
}

// Initialize from route params and stored preferences
onMounted(() => {
  // Get chapter info from route
  if (route.params.chapter) {
    currentChapter.value = parseInt(route.params.chapter as string) || 1;
  }
  if (route.params.total) {
    totalChapters.value = parseInt(route.params.total as string) || 10;
  }
  
  // Load saved preferences
  const savedTheme = localStorage.getItem('reader-theme') as 'light' | 'sepia' | 'dark' | null;
  if (savedTheme && ['light', 'sepia', 'dark'].includes(savedTheme)) {
    theme.value = savedTheme;
  }
  
  const savedFontSize = localStorage.getItem('reader-font-size');
  if (savedFontSize) {
    fontSize.value = parseInt(savedFontSize) || 18;
  }
  
  // Add event listeners
  window.addEventListener('scroll', handleScroll, { passive: true });
  window.addEventListener('keydown', handleKeydown);
  
  // Initial scroll position
  handleScroll();
});

onUnmounted(() => {
  window.removeEventListener('scroll', handleScroll);
  window.removeEventListener('keydown', handleKeydown);
  if (scrollTimeout.value) {
    clearTimeout(scrollTimeout.value);
  }
});
</script>

<template>
  <div 
    class="reader-view" 
    :style="themeStyles"
    :class="`theme-${theme}`"
  >
    <!-- Progress Bar (Fixed at Top) -->
    <div class="progress-container">
      <div 
        class="progress-bar"
        :style="{ width: `${scrollProgress}%` }"
      />
    </div>

    <!-- Main Reading Area -->
    <main class="reader-content" @click="isNavVisible = !isNavVisible">
      <article class="chapter-article">
        <!-- Chapter Header -->
        <header class="chapter-header">
          <span class="chapter-number">Chapter {{ currentChapter }}</span>
        </header>

        <!-- Chapter Content -->
        <div 
          class="chapter-text"
          v-html="chapterContent"
        />
      </article>

      <!-- Chapter Navigation -->
      <nav class="chapter-nav">
        <button
          v-if="canGoPrev"
          class="nav-link nav-prev"
          @click.stop="goToPrevChapter"
          aria-label="Previous chapter"
        >
          <el-icon><ArrowLeft /></el-icon>
          <span>Previous Chapter</span>
        </button>
        
        <button
          v-if="canGoNext"
          class="nav-link nav-next"
          @click.stop="goToNextChapter"
          aria-label="Next chapter"
        >
          <span>Next Chapter</span>
          <el-icon><ArrowRight /></el-icon>
        </button>
      </nav>
    </main>

    <!-- Floating Navigation Bar -->
    <Transition name="nav-slide">
      <div v-show="isNavVisible" class="floating-nav">
        <div class="nav-content">
          <!-- Back Button -->
          <button 
            class="nav-btn nav-back"
            @click="exitReader"
            aria-label="Exit reader"
          >
            <el-icon><ArrowDown /></el-icon>
          </button>

          <!-- Chapter Info -->
          <div class="chapter-info">
            <span class="chapter-current">Chapter {{ currentChapter }} of {{ totalChapters }}</span>
            <span class="chapter-progress">{{ Math.round(scrollProgress) }}% read</span>
          </div>

          <!-- Settings Button -->
          <button 
            class="nav-btn nav-settings"
            @click="toggleSettings"
            :class="{ active: isSettingsOpen }"
            aria-label="Reading settings"
          >
            <el-icon><Setting /></el-icon>
          </button>
        </div>
      </div>
    </Transition>

    <!-- Settings Panel -->
    <Transition name="settings-slide">
      <div v-if="isSettingsOpen" class="settings-panel">
        <div class="settings-header">
          <h3>Reading Settings</h3>
          <button 
            class="settings-close"
            @click="closeSettings"
            aria-label="Close settings"
          >
            <el-icon><Close /></el-icon>
          </button>
        </div>

        <!-- Theme Selection -->
        <div class="settings-section">
          <label class="settings-label">Theme</label>
          <div class="theme-options">
            <button
              v-for="(config, key) in themeConfigs"
              :key="key"
              :class="['theme-btn', { active: theme === key }]"
              @click="setTheme(key as 'light' | 'sepia' | 'dark')"
              :aria-label="`${config.label} theme`"
            >
              <span 
                class="theme-preview"
                :style="{ backgroundColor: config.bg }"
              >
                <span 
                  class="theme-preview-text"
                  :style="{ color: config.text }"
                >Aa</span>
              </span>
              <span class="theme-name">{{ config.label }}</span>
            </button>
          </div>
        </div>

        <!-- Font Size -->
        <div class="settings-section">
          <label class="settings-label">Font Size</label>
          <div class="font-size-options">
            <button
              v-for="size in fontSizes"
              :key="size"
              :class="['size-btn', { active: fontSize === size }]"
              @click="setFontSize(size)"
              :aria-label="`Font size ${size}px`"
            >
              {{ size }}
            </button>
          </div>
        </div>

        <!-- Keyboard Shortcuts -->
        <div class="settings-section shortcuts">
          <label class="settings-label">Keyboard Shortcuts</label>
          <div class="shortcuts-list">
            <div class="shortcut">
              <kbd>&larr;</kbd>
              <span>Previous chapter</span>
            </div>
            <div class="shortcut">
              <kbd>&rarr;</kbd>
              <span>Next chapter</span>
            </div>
            <div class="shortcut">
              <kbd>Esc</kbd>
              <span>Exit reader</span>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Settings Overlay -->
    <Transition name="fade">
      <div 
        v-if="isSettingsOpen" 
        class="settings-overlay"
        @click="closeSettings"
      />
    </Transition>
  </div>
</template>

<style scoped>
/* Reader Container */
.reader-view {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--reader-bg);
  color: var(--reader-text);
  overflow-y: auto;
  overflow-x: hidden;
  transition: background-color var(--transition-slow),
              color var(--transition-slow);
}

/* Progress Bar */
.progress-container {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--reader-border);
  z-index: 100;
}

.progress-bar {
  height: 100%;
  background: var(--gradient-primary);
  transition: width 0.1s ease-out;
  border-radius: 0 1px 1px 0;
}

/* Main Content */
.reader-content {
  min-height: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding: var(--space-16) var(--space-6) calc(var(--space-16) + 48px);
}

/* Chapter Article */
.chapter-article {
  font-family: var(--font-family);
}

.chapter-header {
  text-align: center;
  margin-bottom: var(--space-12);
}

.chapter-number {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--reader-secondary);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

/* Chapter Text */
.chapter-text {
  font-size: var(--reader-font-size);
  line-height: var(--reader-line-height);
  color: var(--reader-text);
  transition: font-size var(--transition-base);
}

.chapter-text :deep(p) {
  margin-bottom: 1.5em;
  text-align: justify;
  hyphens: auto;
}

.chapter-text :deep(h2) {
  font-size: calc(var(--reader-font-size) * 1.5);
  font-weight: var(--font-weight-semibold);
  color: var(--reader-text);
  margin-top: 2.5em;
  margin-bottom: 1em;
  line-height: 1.3;
}

.chapter-text :deep(blockquote) {
  margin: 2em 0;
  padding: var(--space-4) var(--space-6);
  border-left: 3px solid var(--color-primary);
  background: rgba(0, 122, 255, 0.05);
  border-radius: 0 var(--radius-md) var(--radius-md) 0;
}

.chapter-text :deep(blockquote p) {
  font-style: italic;
  margin-bottom: 0;
}

.chapter-text :deep(blockquote p:last-child) {
  margin-bottom: 0;
}

/* Chapter Navigation */
.chapter-nav {
  display: flex;
  justify-content: space-between;
  gap: var(--space-6);
  margin-top: var(--space-16);
  padding-top: var(--space-8);
  border-top: 1px solid var(--reader-border);
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: transparent;
  border: 1px solid var(--reader-border);
  border-radius: var(--radius-lg);
  color: var(--reader-text);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base);
}

.nav-link:hover {
  background: var(--reader-border);
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.nav-prev {
  margin-right: auto;
}

.nav-next {
  margin-left: auto;
}

/* Floating Navigation Bar */
.floating-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 48px;
  background: var(--reader-bg);
  border-top: 1px solid var(--reader-border);
  z-index: 50;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
}

.nav-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  max-width: 720px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.nav-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--reader-text);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.nav-btn:hover {
  background: var(--reader-border);
}

.nav-btn.active {
  background: var(--color-primary);
  color: white;
}

.chapter-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.chapter-current {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--reader-text);
}

.chapter-progress {
  font-size: var(--font-size-xs);
  color: var(--reader-secondary);
}

/* Settings Panel */
.settings-panel {
  position: fixed;
  bottom: 48px;
  right: var(--space-4);
  width: 320px;
  max-width: calc(100vw - var(--space-8));
  background: var(--reader-bg);
  border: 1px solid var(--reader-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  z-index: 60;
  overflow: hidden;
}

.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-4) var(--space-5);
  border-bottom: 1px solid var(--reader-border);
}

.settings-header h3 {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--reader-text);
  margin: 0;
}

.settings-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: transparent;
  border: none;
  border-radius: var(--radius-md);
  color: var(--reader-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.settings-close:hover {
  background: var(--reader-border);
  color: var(--reader-text);
}

.settings-section {
  padding: var(--space-4) var(--space-5);
}

.settings-section:not(:last-child) {
  border-bottom: 1px solid var(--reader-border);
}

.settings-label {
  display: block;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--reader-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-3);
}

/* Theme Options */
.theme-options {
  display: flex;
  gap: var(--space-2);
}

.theme-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3);
  background: transparent;
  border: 2px solid transparent;
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.theme-btn:hover {
  border-color: var(--reader-border);
}

.theme-btn.active {
  border-color: var(--color-primary);
}

.theme-preview {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.1);
}

.theme-preview-text {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
}

.theme-name {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--reader-text);
}

/* Font Size Options */
.font-size-options {
  display: flex;
  gap: var(--space-1);
}

.size-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 40px;
  background: transparent;
  border: 1px solid var(--reader-border);
  border-radius: var(--radius-md);
  font-family: var(--font-family);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--reader-text);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.size-btn:hover {
  background: var(--reader-border);
}

.size-btn.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

/* Keyboard Shortcuts */
.shortcuts-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.shortcut {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.shortcut kbd {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  height: 24px;
  padding: 0 var(--space-2);
  background: var(--reader-border);
  border-radius: var(--radius-sm);
  font-family: var(--font-family);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--reader-text);
}

.shortcut span {
  font-size: var(--font-size-sm);
  color: var(--reader-secondary);
}

/* Settings Overlay */
.settings-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
  z-index: 55;
}

/* Transitions */
.nav-slide-enter-active,
.nav-slide-leave-active {
  transition: transform var(--transition-base), opacity var(--transition-base);
}

.nav-slide-enter-from,
.nav-slide-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

.settings-slide-enter-active,
.settings-slide-leave-active {
  transition: transform var(--transition-base), opacity var(--transition-base);
}

.settings-slide-enter-from,
.settings-slide-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-fast);
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .reader-content {
    padding: var(--space-12) var(--space-4) calc(var(--space-12) + 48px);
  }

  .settings-panel {
    right: var(--space-2);
    left: var(--space-2);
    width: auto;
    max-width: none;
  }

  .chapter-nav {
    flex-direction: column;
    gap: var(--space-3);
  }

  .nav-link {
    width: 100%;
    justify-content: center;
  }
}

/* Dark theme specific adjustments */
.theme-dark .progress-container {
  background: rgba(255, 255, 255, 0.1);
}

.theme-dark .floating-nav {
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
}

.theme-dark .settings-panel {
  box-shadow: var(--shadow-xl), 0 0 40px rgba(0, 0, 0, 0.3);
}

/* Selection styling */
.reader-view ::selection {
  background-color: rgba(0, 122, 255, 0.3);
  color: inherit;
}

/* Focus states */
.nav-btn:focus-visible,
.nav-link:focus-visible,
.theme-btn:focus-visible,
.size-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* Respect reduced motion */
@media (prefers-reduced-motion: reduce) {
  .reader-view,
  .reader-view *,
  .reader-view *::before,
  .reader-view *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
