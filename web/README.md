# NovelWriter Web Interface

> Vue3 + TypeScript frontend for NovelWriter

## Features

- **Dashboard**: Project overview with quick actions
- **Project Management**: Create, edit, delete projects
- **Reading Interface**: Bookshelf view with markdown reader
- **Agent Monitoring**: Real-time agent status dashboard
- **Publishing**: Multi-platform publishing workflow
- **Settings**: Language, theme, and API configuration

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Vue 3 (Composition API) |
| Language | TypeScript |
| Build | Vite |
| State | Pinia |
| UI | Element Plus |
| i18n | Vue I18n |
| Charts | ECharts |
| Router | Vue Router |
| HTTP | Axios |

## Project Structure

```
web/
├── src/
│   ├── api/              # API client
│   │   ├── client.ts     # Axios instance
│   │   ├── projects.ts   # Projects API
│   │   └── agents.ts     # Agents API + WebSocket
│   ├── components/       # Reusable components
│   │   ├── ChapterList.vue
│   │   ├── CharacterPanel.vue
│   │   ├── ProjectWizard.vue
│   │   └── ...
│   ├── views/            # Page views
│   │   ├── Dashboard.vue
│   │   ├── Projects.vue
│   │   ├── Reading.vue
│   │   └── ...
│   ├── stores/           # Pinia stores
│   │   ├── projectStore.ts
│   │   ├── agentStore.ts
│   │   └── settingsStore.ts
│   ├── locales/          # i18n translations
│   │   ├── zh.ts
│   │   └── en.ts
│   ├── layouts/          # Page layouts
│   ├── router/           # Vue Router config
│   ├── types/            # TypeScript types
│   └── i18n/             # i18n setup
├── e2e/                  # Playwright tests
│   ├── project-flow.spec.ts
│   ├── agent-monitoring.spec.ts
│   └── publishing.spec.ts
└── public/               # Static assets
```

## Quick Start

### Install Dependencies

```bash
npm install
```

### Development

```bash
npm run dev
```

Open http://localhost:5173

### Production Build

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

## Available Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Start dev server |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run test` | Run Vitest in watch mode |
| `npm run test:run` | Run all tests once |
| `npm run test:coverage` | Run tests with coverage |

## Testing

### Unit Tests (Vitest)

```bash
npm run test:run
```

**Coverage**: 40 tests, 100% pass rate

### E2E Tests (Playwright)

```bash
# Install browsers
npx playwright install

# Run tests
npx playwright test

# Run with UI
npx playwright test --ui
```

## Design System

### Colors

| Name | Value | Usage |
|------|-------|-------|
| Primary | `#007AFF` | Buttons, links, highlights |
| Background | `#F5F5F7` | Page background |
| Surface | `#FFFFFF` | Cards, panels |
| Text | `#1D1D1F` | Body text |
| Success | `#34C759` | Success states |
| Error | `#FF3B30` | Error states |
| Warning | `#FF9500` | Warning states |

### Typography

- **Title**: 28px Semibold
- **Heading**: 20px Medium
- **Body**: 16px Regular
- **Caption**: 14px Light

### Spacing

- **XS**: 4px
- **SM**: 8px
- **MD**: 16px
- **LG**: 24px
- **XL**: 32px

### Border Radius

- **Small**: 8px
- **Medium**: 12px
- **Large**: 16px
- **XL**: 24px

## API Integration

### Backend URL

Development: `http://localhost:8000`

### REST API

All API calls are made through the Axios client:

```typescript
import { getProjects, createProject } from '@/api/projects'

// Get all projects
const projects = await getProjects()

// Create project
const newProject = await createProject({
  title: 'My Novel',
  genre: 'Fantasy'
})
```

### WebSocket

Real-time agent status updates:

```typescript
import { useAgentStore } from '@/stores/agentStore'

const agentStore = useAgentStore()

// Connect to WebSocket
agentStore.connectWebSocket()

// Access agent data
const agents = agentStore.agients
const connectionStatus = agentStore.connectionStatus
```

## i18n

Supported languages:
- English (en)
- Chinese (zh)

Add new translation key:

```typescript
// locales/en.ts
export default {
  common: {
    save: 'Save',
    cancel: 'Cancel'
  }
}
```

Use in component:

```vue
<script setup>
const { t } = useI18n()
</script>

<template>
  <button>{{ t('common.save') }}</button>
</template>
```

## Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

## Contributing

1. Create a feature branch
2. Make your changes
3. Run tests: `npm run test:run`
4. Submit a pull request

## License

MIT
