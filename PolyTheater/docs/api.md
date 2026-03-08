# PolyTheater API 设计文档

> 版本: 1.0.0
> 最后更新: 2025-03-08

---

## 1. API 概述

### 1.1 基础信息

- **Base URL**: `http://localhost:5001/api`
- **Content-Type**: `application/json`
- **认证**: Bearer Token (可选)

### 1.2 响应格式

```json
{
  "success": true,
  "data": { ... },
  "message": "操作成功",
  "timestamp": "2025-03-08T10:00:00Z"
}
```

### 1.3 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "参数验证失败",
    "details": { ... }
  },
  "timestamp": "2025-03-08T10:00:00Z"
}
```

---

## 2. 故事项目 API

### 2.1 创建项目

```
POST /api/stories
```

**请求体**:
```json
{
  "title": "悬疑故事示例",
  "description": "一个关于神秘失踪案的多视角悬疑小说",
  "genre": "mystery",
  "target_length": 100000,
  "target_chapters": 20,
  "setting_documents": [
    {
      "filename": "世界观设定.txt",
      "content": "..."
    }
  ]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_abc123",
    "title": "悬疑故事示例",
    "status": "draft",
    "graph_id": "graph_xyz789",
    "created_at": "2025-03-08T10:00:00Z"
  }
}
```

### 2.2 获取项目

```
GET /api/stories/{project_id}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "project_id": "proj_abc123",
    "title": "悬疑故事示例",
    "description": "...",
    "genre": "mystery",
    "target_length": 100000,
    "target_chapters": 20,
    "graph_id": "graph_xyz789",
    "characters_count": 15,
    "perspective_characters": ["char_001", "char_002"],
    "generated_chapters_count": 5,
    "status": "in_progress",
    "created_at": "2025-03-08T10:00:00Z",
    "updated_at": "2025-03-08T12:00:00Z"
  }
}
```

### 2.3 列出项目

```
GET /api/stories?page=1&limit=20&status=in_progress
```

### 2.4 更新项目

```
PUT /api/stories/{project_id}
```

### 2.5 删除项目

```
DELETE /api/stories/{project_id}
```

---

## 3. 知识图谱 API

### 3.1 构建图谱

```
POST /api/stories/{project_id}/graph/build
```

**请求体**:
```json
{
  "documents": [
    {
      "filename": "世界观设定.txt",
      "content": "故事发生在2024年的上海市..."
    }
  ],
  "custom_entity_types": ["超自然生物", "魔法物品"],
  "custom_relation_types": ["宿敌", "契约"]
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "graph_id": "graph_xyz789",
    "status": "building",
    "estimated_time_seconds": 60,
    "progress_url": "/api/stories/proj_abc123/graph/build/status"
  }
}
```

### 3.2 获取图谱构建状态

```
GET /api/stories/{project_id}/graph/build/status
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "completed",
    "progress": 100,
    "statistics": {
      "total_entities": 45,
      "total_relations": 120,
      "entity_types": {
        "Character": 15,
        "Location": 10,
        "Organization": 8,
        "Item": 12
      }
    }
  }
}
```

### 3.3 查询实体

```
GET /api/stories/{project_id}/graph/entities?type=Character&limit=50
```

### 3.4 查询关系

```
GET /api/stories/{project_id}/graph/relations?source={entity_id}
```

### 3.5 查询时间线

```
GET /api/stories/{project_id}/graph/timeline?start=2024-01-01&end=2024-12-31
```

### 3.6 搜索图谱

```
POST /api/stories/{project_id}/graph/search
```

**请求体**:
```json
{
  "query": "谁是主角的敌人？",
  "search_type": "insight",  // "quick", "panorama", "insight"
  "limit": 10
}
```

---

## 4. 角色 API

### 4.1 创建角色

```
POST /api/stories/{project_id}/characters
```

**请求体**:
```json
{
  "name": "林晓雨",
  "age": 28,
  "gender": "female",
  "occupation": "刑警",
  "character_layer": 1,
  "has_pov": true,
  "mbti": "INTJ",
  "thinking_style": "analytical",
  "emotional_tone": "rational",
  "bio": "一名冷静理性的女刑警，擅长逻辑推理..."
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "character_id": "char_001",
    "name": "林晓雨",
    "character_layer": 1,
    "has_pov": true,
    "activity_level": 0.9,
    "influence_weight": 2.5,
    "detailed_persona": "...",
    "perspective_bias": {
      "gender": "female",
      "mbti": "INTJ",
      "thinking_style": "analytical",
      "emotional_tone": "rational",
      "attention_focus": ["details", "actions"],
      "narrative_voice": "formal",
      "vocabulary_theme": "intellectual"
    }
  }
}
```

### 4.2 批量生成角色

```
POST /api/stories/{project_id}/characters/batch-generate
```

**请求体**:
```json
{
  "layer": 4,
  "template": "crowd_bystander",
  "count": 100
}
```

### 4.3 获取角色

```
GET /api/stories/{project_id}/characters/{character_id}
```

### 4.4 获取角色认知图谱

```
GET /api/stories/{project_id}/characters/{character_id}/beliefs
```

**响应**:
```json
{
  "success": true,
  "data": {
    "character_id": "char_001",
    "beliefs": [
      {
        "belief_id": "belief_001",
        "about_entity_id": "char_002",
        "property_name": "is_alive",
        "believed_value": false,
        "confidence": 0.95,
        "source": "direct",
        "is_false": true
      }
    ]
  }
}
```

### 4.5 更新角色认知

```
PUT /api/stories/{project_id}/characters/{character_id}/beliefs
```

---

## 5. 模拟 API

### 5.1 运行章节模拟

```
POST /api/stories/{project_id}/simulate/chapter/{chapter}
```

**请求体**:
```json
{
  "active_characters": ["char_001", "char_002", "char_003"],
  "pacing_override": {
    "target_pacing": "medium",
    "max_events": 5
  },
  "force_milestones": true
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_xyz789",
    "chapter": 1,
    "status": "running",
    "estimated_time_seconds": 120,
    "progress_url": "/api/stories/proj_abc123/simulate/sim_xyz789/status"
  }
}
```

### 5.2 获取模拟状态

```
GET /api/stories/{project_id}/simulate/{simulation_id}/status
```

**响应**:
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_xyz789",
    "status": "completed",
    "progress": 100,
    "events_generated": 5,
    "active_characters": ["char_001", "char_002", "char_003"],
    "checks": {
      "milestone": {
        "passed": true,
        "completed_milestones": ["milestone_001"]
      },
      "timeline": {
        "passed": true
      }
    }
  }
}
```

### 5.3 获取模拟结果

```
GET /api/stories/{project_id}/simulate/{simulation_id}/result
```

---

## 6. 叙事生成 API

### 6.1 生成章节叙事

```
POST /api/stories/{project_id}/narratives/chapter/{chapter}
```

**请求体**:
```json
{
  "perspective_characters": ["char_001", "char_002"],
  "simulation_id": "sim_xyz789",
  "style_override": {
    "narrative_voice": "lyrical",
    "detail_level": "high"
  }
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "generation_id": "gen_abc456",
    "chapter": 1,
    "status": "generating",
    "perspective_characters": ["char_001", "char_002"],
    "estimated_time_seconds": 60,
    "progress_url": "/api/stories/proj_abc123/narratives/gen_abc456/status"
  }
}
```

### 6.2 获取生成状态

```
GET /api/stories/{project_id}/narratives/{generation_id}/status
```

### 6.3 获取生成的叙事

```
GET /api/stories/{project_id}/narratives/{generation_id}/result
```

**响应**:
```json
{
  "success": true,
  "data": {
    "chapter": 1,
    "narratives": {
      "char_001": {
        "character_name": "林晓雨",
        "narrative_text": "我站在窗前，望着窗外闪烁的霓虹灯...",
        "word_count": 2500,
        "quality_score": 0.85
      },
      "char_002": {
        "character_name": "陈明轩",
        "narrative_text": "这个案子越来越复杂了...",
        "word_count": 2300,
        "quality_score": 0.82
      }
    },
    "events_count": 5,
    "checks": {
      "milestone": {"passed": true},
      "timeline": {"passed": true},
      "character": {"passed": true},
      "belief": {"passed": true}
    }
  }
}
```

### 6.4 获取章节叙事（已保存）

```
GET /api/stories/{project_id}/chapters/{chapter}
```

---

## 7. 一致性检查 API

### 7.1 检查时间线

```
POST /api/stories/{project_id}/checks/timeline
```

**请求体**:
```json
{
  "events": [
    {"event_id": "evt_001", "occurred_at": "2024-03-01T10:00:00"},
    {"event_id": "evt_002", "occurred_at": "2024-03-01T09:00:00"}
  ]
}
```

### 7.2 检查人物一致性

```
POST /api/stories/{project_id}/checks/character
```

### 7.3 检查认知冲突

```
POST /api/stories/{project_id}/checks/belief
```

### 7.4 全面检查

```
POST /api/stories/{project_id}/checks/full
```

**响应**:
```json
{
  "success": true,
  "data": {
    "passed": false,
    "issues": [
      {
        "type": "timeline",
        "severity": "high",
        "description": "事件时间顺序错误",
        "details": {...},
        "suggestion": "调整事件 evt_002 的时间"
      },
      {
        "type": "character",
        "severity": "medium",
        "description": "角色行为不符合性格",
        "details": {...}
      }
    ]
  }
}
```

---

## 8. 控制配置 API

### 8.1 获取控制配置

```
GET /api/stories/{project_id}/config
```

### 8.2 更新控制配置

```
PUT /api/stories/{project_id}/config
```

**请求体**:
```json
{
  "pacing_configs": {
    "1": {
      "target_pacing": "slow",
      "max_events": 3,
      "min_dialogue_ratio": 0.6
    }
  },
  "milestones": [
    {
      "chapter": 1,
      "event_description": "主角发现第一具尸体",
      "must_happen": true
    }
  ]
}
```

### 8.3 添加里程碑

```
POST /api/stories/{project_id}/config/milestones
```

### 8.4 添加角色约束

```
POST /api/stories/{project_id}/config/constraints/{character_id}
```

---

## 9. WebSocket API (实时更新)

### 9.1 连接

```
ws://localhost:5001/api/ws?token={auth_token}
```

### 9.2 订阅事件

```json
{
  "action": "subscribe",
  "channel": "story:{project_id}",
  "events": ["simulation_progress", "narrative_generated", "check_completed"]
}
```

### 9.3 事件消息

**模拟进度**:
```json
{
  "event": "simulation_progress",
  "data": {
    "simulation_id": "sim_xyz789",
    "progress": 50,
    "current_round": 5,
    "total_rounds": 10
  }
}
```

**叙事生成完成**:
```json
{
  "event": "narrative_generated",
  "data": {
    "generation_id": "gen_abc456",
    "chapter": 1,
    "character_id": "char_001",
    "preview": "我站在窗前..."
  }
}
```

---

## 10. 导出 API

### 10.1 导出项目

```
GET /api/stories/{project_id}/export?format=json
```

### 10.2 导出章节

```
GET /api/stories/{project_id}/chapters/{chapter}/export?format=md
```

### 10.3 导出全本

```
GET /api/stories/{project_id}/export/full?format=txt&merge_perspectives=false
```

---

## 11. 错误代码

详细的错误代码说明，请参考 [错误码文档](error_codes.md)。

### 常用错误代码速查

| 代码 | 说明 | HTTP 状态码 |
|------|------|------------|
| `VALIDATION_ERROR` | 参数验证失败 | 400 |
| `NOT_FOUND` | 资源不存在 | 404 |
| `ALREADY_EXISTS` | 资源已存在 | 409 |
| `SIMULATION_FAILED` | 模拟失败 | 500 |
| `GENERATION_FAILED` | 生成失败 | 500 |
| `CHECK_FAILED` | 一致性检查失败 | 422 |
| `GRAPH_ERROR` | 图谱操作错误 | 500 |
| `LLM_ERROR` | LLM 调用错误 | 503 |
| `RATE_LIMIT` | 请求频率超限 | 429 |
| `UNAUTHORIZED` | 未授权访问 | 401 |
| `FORBIDDEN` | 禁止访问 | 403 |
| `INTERNAL_ERROR` | 服务器内部错误 | 500 |

### 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误描述",
    "details": {
      "field": "具体错误信息"
    }
  },
  "timestamp": "2025-03-08T10:00:00Z",
  "path": "/api/stories/proj_123"
}
```

### 错误处理最佳实践

1. **客户端处理**：根据错误码采取不同处理策略
2. **重试机制**：对 `LLM_ERROR`、`RATE_LIMIT` 等临时错误实现指数退避重试
3. **用户提示**：将技术错误码转换为用户友好的提示信息
4. **日志记录**：记录完整错误上下文便于排查

---

这就是 PolyTheater 的完整 API 设计！
