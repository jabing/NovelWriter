# NovelWriter Documentation

## Documentation Index

### Getting Started

| Document | Description |
|----------|-------------|
| [../README.md](../README.md) | Project overview and quick start |
| [../web/README.md](../web/README.md) | Frontend documentation |
| [API.md](API.md) | REST API and WebSocket documentation |
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | Current project status |

### Backend Documentation

| Document | Location |
|----------|----------|
| Architecture | [../docs/writer/ARCHITECTURE.md](../docs/writer/ARCHITECTURE.md) |
| Development Guide | [../docs/writer/DEVELOPMENT.md](../docs/writer/DEVELOPMENT.md) |
| User Manual | [../docs/writer/USER_MANUAL.md](../docs/writer/USER_MANUAL.md) |
| Quick Start | [../docs/writer/QUICKSTART.md](../docs/writer/QUICKSTART.md) |

### Planning Documents

| Document | Location |
|----------|----------|
| Vue3 Web Interface Plan | [../.sisyphus/plans/vue3-web-interface.md](../.sisyphus/plans/vue3-web-interface.md) |
| E2E Tests Plan (Windows) | [../.sisyphus/plans/e2e-tests-windows.md](../.sisyphus/plans/e2e-tests-windows.md) |

### Test Reports

| Category | Status |
|----------|--------|
| Backend Unit Tests | 43/43 ✅ |
| Frontend Unit Tests | 40/40 ✅ |
| E2E Tests | Pending (Windows) |

## Quick Links

### Running the Application

```bash
# Backend (Terminal 1)
python -m uvicorn src.novel_agent.api.main:app --reload --port 8000

# Frontend (Terminal 2)
cd web
npm run dev
```

### Running Tests

```bash
# Backend tests
pytest tests/agents/ -v

# Frontend tests
cd web
npm run test:run

# E2E tests (Windows)
cd web
npx playwright test
```

### Building for Production

```bash
# Frontend
cd web
npm run build

# Output: web/dist/
```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Support

- GitHub Issues: [Report a bug](https://github.com/your-repo/issues)
- Documentation: This folder
- API Reference: [API.md](API.md)
