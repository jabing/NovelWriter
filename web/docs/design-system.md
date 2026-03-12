# NovelWriter Design System

> A literary/book-inspired design system for the NovelWriter application.

## Overview

NovelWriter uses a **literary aesthetic** design system inspired by physical books, leather bindings, and aged paper. The design creates a warm, inviting atmosphere for writers while maintaining excellent readability and accessibility.

### Design Philosophy

- **Literary Aesthetic**: Warm leather browns, aged paper tones, and ink colors
- **Book-Inspired**: Components styled like physical book elements
- **Dark Mode Support**: Full dark theme with cozy, library-like atmosphere
- **Accessibility**: WCAG 2.1 AA compliant with reduced motion support

---

## Design Tokens

Design tokens are the visual design atoms of the design system. They are named entities that store visual design attributes.

### Color System

#### Primary Colors (Leather Brown)

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--color-primary` | `#8B5A2B` | `#A67B5B` | Primary actions, links |
| `--color-primary-hover` | `#A67B5B` | `#C49B7B` | Hover states |
| `--color-primary-active` | `#6B4423` | - | Active/pressed states |
| `--color-primary-light` | `#D4A574` | - | Light accents |
| `--color-primary-muted` | `#F5E6D3` | - | Backgrounds, highlights |

#### Background Colors (Paper Tones)

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--color-bg-primary` | `#F5F1E8` | `#1A1512` | Main background |
| `--color-bg-secondary` | `#EDE7DB` | `#252018` | Cards, sections |
| `--color-bg-tertiary` | `#E5DED0` | - | Tertiary areas |
| `--color-bg-elevated` | `#FAF8F3` | `#3A3128` | Elevated surfaces |
| `--color-bg-input` | `#FFFFFF` | - | Input fields |

#### Text Colors (Ink Tones)

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--color-text-primary` | `#2C2416` | `#F5F0E8` | Headings, body text |
| `--color-text-secondary` | `#5C4D3D` | `#D4C8B8` | Secondary text |
| `--color-text-tertiary` | `#8B7355` | - | Captions, hints |
| `--color-text-placeholder` | `#A09080` | - | Placeholder text |
| `--color-text-disabled` | `#B8A99A` | - | Disabled text |

#### Semantic Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-success` | `#4A7C59` | Success states, confirmations |
| `--color-warning` | `#B8860B` | Warnings, cautions |
| `--color-error` | `#9B2C2C` | Errors, destructive actions |
| `--color-info` | `#5B7C99` | Informational messages |

#### Accent Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--color-accent-gold` | `#C9A227` | Premium features, highlights |
| `--color-accent-bronze` | `#B87333` | Decorative accents |

#### Border Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--color-border` | `#D4C8B8` | `#4A4035` | Standard borders |
| `--color-border-light` | `#E5DED0` | - | Subtle dividers |
| `--color-border-focus` | `#8B5A2B` | `#A67B5B` | Focus rings |

---

### Typography

#### Font Families

```css
--font-serif: 'Merriweather', Georgia, 'Noto Serif SC', serif;
--font-sans: 'Source Sans 3', -apple-system, 'Noto Sans SC', sans-serif;
--font-mono: 'SF Mono', 'Fira Code', monospace;
```

**Usage:**
- **Serif** (`--font-serif`): Body text, chapter content, literary elements
- **Sans** (`--font-sans`): UI elements, buttons, navigation
- **Mono** (`--font-mono`): Code, technical content

#### Font Sizes

| Token | Value | Usage |
|-------|-------|-------|
| `--font-size-h1` | `3.052rem` | Page titles |
| `--font-size-h2` | `2.441rem` | Section headings |
| `--font-size-h3` | `1.953rem` | Subsection headings |
| `--font-size-h4` | `1.563rem` | Card titles |
| `--font-size-body` | `1rem` | Body text |
| `--font-size-body-sm` | `0.875rem` | Small text, captions |

---

### Spacing

Based on a **4px base unit** for consistent spacing throughout the application.

| Token | Value | Usage |
|-------|-------|-------|
| `--space-1` | `0.25rem` (4px) | Tight spacing |
| `--space-2` | `0.5rem` (8px) | Icon margins |
| `--space-3` | `0.75rem` (12px) | Small gaps |
| `--space-4` | `1rem` (16px) | Default spacing |
| `--space-6` | `1.5rem` (24px) | Section padding |
| `--space-8` | `2rem` (32px) | Large spacing |
| `--space-12` | `3rem` (48px) | Section margins |
| `--space-16` | `4rem` (64px) | Page margins |

---

### Shadows

Shadow tokens create depth and hierarchy while maintaining the literary aesthetic.

| Token | Light Mode | Usage |
|-------|------------|-------|
| `--shadow-sm` | `0 1px 2px rgba(44, 36, 22, 0.04)` | Subtle lift |
| `--shadow-md` | `0 2px 8px rgba(44, 36, 22, 0.06)` | Dropdowns |
| `--shadow-lg` | `0 4px 16px rgba(44, 36, 22, 0.08)` | Modals |
| `--shadow-card` | `0 2px 12px rgba(44, 36, 22, 0.06)` | Cards |
| `--shadow-card-hover` | `0 8px 24px rgba(44, 36, 22, 0.1)` | Card hover |

---

### Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | `4px` | Small elements, badges |
| `--radius-md` | `8px` | Buttons, inputs |
| `--radius-lg` | `12px` | Cards |
| `--radius-xl` | `16px` | Dialogs, large surfaces |
| `--radius-full` | `9999px` | Avatars, circular elements |

---

### Transitions

| Token | Value | Usage |
|-------|-------|-------|
| `--transition-fast` | `150ms ease-out` | Hover states, icons |
| `--transition-base` | `200ms ease-out` | Buttons, inputs |
| `--transition-slow` | `400ms ease-in-out` | Page transitions |

---

## Usage Guidelines

### Using Design Tokens

Always use design tokens instead of hardcoded values:

```css
/* ✅ Correct */
.my-component {
  color: var(--color-text-primary);
  background: var(--color-bg-elevated);
  padding: var(--space-4);
  border-radius: var(--radius-md);
}

/* ❌ Incorrect */
.my-component {
  color: #2C2416;
  background: #FAF8F3;
  padding: 16px;
  border-radius: 8px;
}
```

### Component Usage

Design tokens are imported in `main.ts`:

```typescript
// main.ts
import './assets/design-tokens.css'
import './assets/element-overrides.css'
```

### Dark Mode

Dark mode is activated via the `data-theme` attribute:

```html
<!-- Light mode (default) -->
<html>
  <!-- ... -->
</html>

<!-- Dark mode -->
<html data-theme="dark">
  <!-- ... -->
</html>
```

Toggle dark mode in Vue:

```typescript
const toggleDarkMode = () => {
  const html = document.documentElement
  html.setAttribute(
    'data-theme',
    html.getAttribute('data-theme') === 'dark' ? '' : 'dark'
  )
}
```

### Reduced Motion

Respect user preferences for reduced motion:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Component Styling

### Element Plus Overrides

The `element-overrides.css` file provides literary-themed styling for Element Plus components:

- **Buttons**: Leather-bound book styling with subtle shadows
- **Inputs**: Paper-texture input fields with ink-colored text
- **Cards**: Book-texture card components with spine-style headers
- **Dialogs**: Literary modal styling with decorative title bars
- **Icons**: Consistent color variants matching semantic colors

### Custom Components

When creating custom components:

1. **Use design tokens** for all visual properties
2. **Follow the naming convention** of existing tokens
3. **Support dark mode** with appropriate color variants
4. **Respect reduced motion** preferences

Example custom component:

```vue
<template>
  <div class="literary-card">
    <h3 class="literary-card__title">{{ title }}</h3>
    <p class="literary-card__content"><slot /></p>
  </div>
</template>

<style scoped>
.literary-card {
  background: var(--color-bg-elevated);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: var(--space-6);
  transition: all var(--transition-base);
}

.literary-card:hover {
  box-shadow: var(--shadow-card-hover);
  transform: translateY(-2px);
}

.literary-card__title {
  font-family: var(--font-serif);
  font-size: var(--font-size-h4);
  color: var(--color-text-primary);
  margin-bottom: var(--space-4);
}

.literary-card__content {
  font-family: var(--font-sans);
  font-size: var(--font-size-body);
  color: var(--color-text-secondary);
  line-height: 1.6;
}
</style>
```

---

## File Structure

```
web/src/assets/
├── design-tokens.css      # Core design tokens
└── element-overrides.css  # Element Plus component theming
```

---

## Accessibility

The design system follows WCAG 2.1 AA guidelines:

- **Color Contrast**: All text colors meet 4.5:1 contrast ratio
- **Focus States**: Visible focus rings using `--color-border-focus`
- **Reduced Motion**: Respects `prefers-reduced-motion`
- **Semantic HTML**: Proper heading hierarchy and landmarks

---

## Version

- **Version**: 2.0
- **Last Updated**: March 2026
- **Authors**: NovelWriter Design Team
