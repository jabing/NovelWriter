# NovelWriter

> AI-powered novel writing and publishing system with Vue3 web interface

## Overview

NovelWriter is a comprehensive AI-assisted novel writing platform that helps authors create, manage, and publish their stories. It features intelligent agents for plot development, character management, and automated publishing to multiple platforms.

## Features

### Core Features

- **Project Management**: Create, edit, and manage multiple novel projects with metadata tracking
- **Chapter Organization**: Hierarchical chapter structure with drag-and-drop reordering and navigation
- **Character Management**: Detailed character profiles with relationship tracking, role classification, and status management
- **AI Writing Assistants**: Multiple specialized agents for different writing tasks with real-time monitoring
- **Real-time Monitoring**: Live agent status, health monitoring, and system metrics via WebSocket
- **Multi-platform Publishing**: Export to Wattpad, Royal Road, Kindle, and more with platform-specific formatting
- **Analytics Dashboard**: Comprehensive writing metrics, progress tracking, and data visualization
- **Comments & Feedback**: Reader comment management and feedback tracking
- **Dark Mode**: Full dark theme support for comfortable writing sessions
- **Bilingual Interface**: Complete Chinese/English localization support

### Web Interface

- Modern Vue3 + TypeScript frontend
- Apple-inspired design system
- Responsive and accessible layout
- Real-time updates via WebSocket
- Interactive charts and visualizations (ECharts)
- Markdown rendering for content preview

## Project Structure

```
NovelWriter/
├── src/                      # Python source code
│   ├── novel_agent/         # Novel Agent System (AI writing backend)
│   │   ├── api/             # FastAPI REST API + WebSocket
│   │   ├── agents/          # AI writing agents
│   │   ├── studio/          # Core studio functionality
│   │   └── novel/           # Novel management logic
│   └── novelwriter_lsp/     # Language Server Protocol implementation
├── web/                      # Vue3 frontend
│   ├── src/
│   │   ├── components/      # Vue components
│   │   ├── views/           # Page views
│   │   ├── stores/          # Pinia state management
│   │   ├── api/             # API client
│   │   └── locales/         # i18n translations
│   └── e2e/                 # Playwright E2E tests
├── tests/                    # Test suites
│   ├── agents/              # Novel agent system tests
│   └── lsp/                 # LSP tests
├── docs/                     # Documentation
│   ├── writer/              # Writer documentation
│   └── lsp/                 # LSP documentation
├── novelwriter-shared/       # Shared data models (independent package)
├── data/                     # Data directory
└── scripts/                  # Utility scripts
```

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd Writer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
python -m uvicorn src.api.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd web

# Install dependencies
npm install

# Start development server
npm run dev
```

### Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Technology Stack

### Backend

- **Framework**: FastAPI
- **Language**: Python 3.10+
- **AI/ML**: LangChain, OpenAI, DeepSeek
- **Database**: SQLite, ChromaDB, Neo4j (optional)
- **Real-time**: WebSocket

### Frontend

- **Framework**: Vue 3
- **Language**: TypeScript
- **State Management**: Pinia
- **UI Library**: Element Plus
- **Build Tool**: Vite
- **Testing**: Vitest, Playwright

## API Overview

### REST Endpoints

#### Projects
| Endpoint | Description |
|----------|-------------|
| `GET /api/projects` | List all projects |
| `POST /api/projects` | Create new project |
| `GET /api/projects/{id}` | Get project details |
| `PUT /api/projects/{id}` | Update project |
| `DELETE /api/projects/{id}` | Delete project |

#### Chapters
| Endpoint | Description |
|----------|-------------|
| `GET /api/novels/{id}/chapters` | List chapters |
| `POST /api/novels/{id}/chapters` | Create new chapter |
| `PUT /api/chapters/{id}` | Update chapter |
| `DELETE /api/chapters/{id}` | Delete chapter |
| `PUT /api/chapters/{id}/reorder` | Reorder chapters |

#### Characters
| Endpoint | Description |
|----------|-------------|
| `GET /api/novels/{id}/characters` | List characters |
| `POST /api/novels/{id}/characters` | Create new character |
| `PUT /api/characters/{id}` | Update character |
| `DELETE /api/characters/{id}` | Delete character |

#### Agents
| Endpoint | Description |
|----------|-------------|
| `GET /api/agents` | List AI agents |
| `GET /api/agents/{id}/history` | Get agent execution history |
| `POST /api/agents/{id}/execute` | Trigger agent execution |

#### Monitoring
| Endpoint | Description |
|----------|-------------|
| `GET /api/monitoring/health` | Health check |
| `GET /api/monitoring/metrics` | System metrics |
| `GET /api/monitoring/alerts` | System alerts |

#### Publishing
| Endpoint | Description |
|----------|-------------|
| `GET /api/publish/platforms` | List publishing platforms |
| `POST /api/publish/export` | Export to platform |
| `GET /api/publish/status` | Get publish status |

### WebSocket

- **Endpoint**: `/ws/agents`
- **Purpose**: Real-time agent status updates
- **Message Format**: `{"type": "agent_status", "data": {...}}`

## Testing

### Backend Tests

```bash
cd Writer
pytest tests/api/ -v
```

**Coverage**: 43 tests, 100% pass rate

### Frontend Tests

```bash
cd web
npm run test
```

**Coverage**: 49 tests across components, views, and API layers
- Component tests: CharacterPanel, ChapterList, MainLayout, Dashboard
- API integration tests: Agents, Projects, Monitoring
- E2E tests: User workflows and critical paths

### E2E Tests

```bash
cd web
npx playwright install
npx playwright test
```

**Coverage**: 100 tests across 3 test suites

## Development

### Code Style

- **Python**: Ruff, Black, isort
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits

### Branch Strategy

- `main` - Stable release
- `develop` - Development branch
- `feature/*` - Feature branches

## Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Architecture](./Writer/docs/ARCHITECTURE.md) - System architecture
- [Development Guide](./Writer/docs/DEVELOPMENT.md) - Development setup
- [User Manual](./Writer/docs/USER_MANUAL.md) - End-user guide

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## License

MIT License - See [LICENSE](./LICENSE) for details.

## Acknowledgments

- Built with FastAPI and Vue 3
- AI powered by OpenAI and DeepSeek
- Inspired by professional writing tools

## Feature Checklist

### ✅ Completed Features

#### Backend (Python/FastAPI)
- [x] Project CRUD operations
- [x] Chapter management with reordering
- [x] Character profiles with relationships
- [x] AI agent system with multiple specialized agents
- [x] WebSocket real-time updates
- [x] Health monitoring and metrics
- [x] Multi-platform publishing exports
- [x] RESTful API with OpenAPI documentation
- [x] Database integration (SQLite, ChromaDB)
- [x] Agent execution history tracking

#### Frontend (Vue3/TypeScript)
- [x] Dashboard with project overview
- [x] Project management views
- [x] Chapter list and navigation
- [x] Character panel with filtering
- [x] Agent dashboard with real-time status
- [x] Agent execution history viewer
- [x] Analytics dashboard with charts
- [x] Publishing platform management
- [x] Comments and feedback system
- [x] Settings and preferences
- [x] Dark mode toggle
- [x] Bilingual support (i18n)
- [x] Responsive design
- [x] Markdown rendering
- [x] Interactive data visualizations

#### Testing
- [x] Backend unit tests (pytest)
- [x] Frontend component tests (Vitest)
- [x] API integration tests
- [x] E2E tests (Playwright)

#### Documentation
- [x] README.md with feature list
- [x] API documentation (OpenAPI/Swagger)
- [x] Architecture documentation
- [x] Development guide
- [x] User manual

### 🚧 In Progress
- [ ] TypeScript strict mode compliance
- [ ] Full test coverage (80%+ target)
- [ ] Performance optimization
- [ ] Advanced analytics features

### 📋 Planned Features
- [ ] Collaborative writing (multi-user)
- [ ] Version control integration
- [ ] Advanced AI suggestions
- [ ] Mobile app (React Native)
- [ ] Cloud sync and backup
- [ ] Plugin system
- [ ] Custom agent creation UI
