# NovelWriter API Documentation

## Base URL

```
Development: http://localhost:8000
Production: https://api.novelwriter.app
```

## Authentication

No authentication required (single-user local application).

## Endpoints

### Projects

#### List Projects

```http
GET /api/projects
```

**Response**:
```json
{
  "projects": [
    {
      "id": "novel_abc123",
      "title": "My Novel",
      "genre": "Fantasy",
      "status": "in_progress",
      "word_count": 50000,
      "chapter_count": 12,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-03-10T08:45:00Z"
    }
  ],
  "total": 1
}
```

#### Create Project

```http
POST /api/projects
Content-Type: application/json

{
  "title": "My New Novel",
  "genre": "Science Fiction",
  "description": "A space adventure",
  "target_words": 80000,
  "target_chapters": 20
}
```

**Response**: `201 Created`

```json
{
  "id": "novel_xyz789",
  "title": "My New Novel",
  "genre": "Science Fiction",
  "status": "draft",
  "word_count": 0,
  "chapter_count": 0,
  "created_at": "2024-03-10T09:00:00Z"
}
```

#### Get Project

```http
GET /api/projects/{project_id}
```

**Response**: `200 OK`

```json
{
  "id": "novel_abc123",
  "title": "My Novel",
  "genre": "Fantasy",
  "status": "in_progress",
  "word_count": 50000,
  "chapter_count": 12,
  "premise": "A young wizard discovers...",
  "themes": ["friendship", "courage"],
  "platforms": ["wattpad", "royalroad"],
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-03-10T08:45:00Z"
}
```

#### Update Project

```http
PUT /api/projects/{project_id}
Content-Type: application/json

{
  "title": "Updated Title",
  "status": "completed"
}
```

**Response**: `200 OK`

#### Delete Project

```http
DELETE /api/projects/{project_id}
```

**Response**: `204 No Content`

---

### Chapters

#### List Chapters

```http
GET /api/novels/{novel_id}/chapters
```

**Response**:
```json
{
  "chapters": [
    {
      "id": "chapter_001",
      "novel_id": "novel_abc123",
      "number": 1,
      "title": "The Beginning",
      "status": "published",
      "word_count": 3500,
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-02-20T14:30:00Z"
    }
  ],
  "total": 12
}
```

#### Get Chapter

```http
GET /api/novels/{novel_id}/chapters/{chapter_number}
```

**Response**:
```json
{
  "id": "chapter_001",
  "novel_id": "novel_abc123",
  "number": 1,
  "title": "The Beginning",
  "status": "published",
  "word_count": 3500,
  "content": "# Chapter 1: The Beginning\n\n...",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-02-20T14:30:00Z"
}
```

---

### Characters

#### List Characters

```http
GET /api/novels/{novel_id}/characters
```

**Response**:
```json
{
  "characters": [
    {
      "id": "char_001",
      "name": "Alice",
      "role": "protagonist",
      "tier": 1,
      "status": "active",
      "description": "A brave young wizard",
      "relationships": [
        {"character_id": "char_002", "type": "ally"}
      ]
    }
  ],
  "total": 5,
  "main_characters": 2,
  "supporting_characters": 3
}
```

#### Create Character

```http
POST /api/novels/{novel_id}/characters
Content-Type: application/json

{
  "name": "Bob",
  "role": "supporting",
  "tier": 2,
  "description": "Alice's best friend"
}
```

**Response**: `201 Created`

---

### Agents

#### List Agents

```http
GET /api/agents
```

**Response**:
```json
{
  "agents": [
    {
      "id": "plot_agent",
      "name": "Plot Agent",
      "type": "plot",
      "status": "idle",
      "last_run": "2024-03-09T15:00:00Z"
    },
    {
      "id": "character_agent",
      "name": "Character Agent",
      "type": "character",
      "status": "running",
      "last_run": "2024-03-10T09:30:00Z"
    }
  ]
}
```

#### Trigger Agent

```http
POST /api/agents/{agent_type}/run
Content-Type: application/json

{
  "project_id": "novel_abc123",
  "params": {
    "chapter_range": [1, 5]
  }
}
```

**Response**: `202 Accepted`

```json
{
  "task_id": "task_xyz123",
  "status": "queued",
  "agent_type": "plot",
  "project_id": "novel_abc123"
}
```

---

### Monitoring

#### Health Check

```http
GET /api/monitoring/health
```

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-03-10T09:45:00Z",
  "checks": {
    "database": "ok",
    "llm_api": "ok",
    "storage": "ok"
  }
}
```

#### System Metrics

```http
GET /api/monitoring/metrics
```

**Response**:
```json
{
  "projects": 5,
  "total_words": 250000,
  "total_chapters": 50,
  "agent_runs_today": 12,
  "uptime_seconds": 86400
}
```

---

### Publishing

#### List Platforms

```http
GET /api/publishing/platforms
```

**Response**:
```json
{
  "platforms": [
    {
      "id": "wattpad",
      "name": "Wattpad",
      "connected": true,
      "last_sync": "2024-03-10T08:00:00Z"
    },
    {
      "id": "royalroad",
      "name": "Royal Road",
      "connected": false
    }
  ]
}
```

#### Publish Chapter

```http
POST /api/publishing/publish
Content-Type: application/json

{
  "project_id": "novel_abc123",
  "platform": "wattpad",
  "chapter_numbers": [1, 2, 3],
  "auto_publish": false
}
```

**Response**: `202 Accepted`

#### Get Comments

```http
GET /api/publishing/comments/{novel_id}
```

**Response**:
```json
{
  "comments": [
    {
      "id": "comment_001",
      "platform": "wattpad",
      "chapter": 1,
      "author": "Reader123",
      "content": "Great story!",
      "sentiment": "positive",
      "timestamp": "2024-03-09T12:00:00Z"
    }
  ],
  "total": 42
}
```

---

## WebSocket

### Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/agents')

ws.onopen = () => {
  console.log('Connected to agent updates')
}

ws.onmessage = (event) => {
  const data = JSON.parse(event.data)
  console.log('Agent update:', data)
}
```

### Message Format

```json
{
  "type": "agent_status",
  "data": {
    "agent_type": "plot",
    "status": "running",
    "progress": 0.65,
    "project_id": "novel_abc123"
  }
}
```

### Message Types

| Type | Description |
|------|-------------|
| `agent_status` | Agent status change |
| `task_complete` | Agent task finished |
| `health_update` | System health change |
| `alert` | System alert |

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid request parameters",
  "errors": [
    {
      "field": "title",
      "message": "Title is required"
    }
  ]
}
```

### 404 Not Found

```json
{
  "detail": "Project not found: novel_xyz999"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error",
  "error_id": "err_abc123"
}
```

---

## Rate Limits

| Endpoint Type | Limit |
|---------------|-------|
| Read operations | 100/minute |
| Write operations | 30/minute |
| Agent triggers | 10/minute |

---

## Versioning

API version is included in the URL:

```
/api/v1/projects
```

Current version: `v1`
