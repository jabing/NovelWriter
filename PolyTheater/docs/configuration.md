# PolyTheater 配置指南

> 版本：1.0.0  
> 最后更新：2025-03-08

---

## 目录

- [快速开始](#快速开始)
- [环境变量配置](#环境变量配置)
- [应用配置](#应用配置)
- [数据库配置](#数据库配置)
- [CORS 配置](#cors 配置)
- [日志配置](#日志配置)
- [模拟配置](#模拟配置)
- [安全配置](#安全配置)
- [配置示例](#配置示例)
- [故障排除](#故障排除)

---

## 快速开始

### 1. 复制配置模板

```bash
cd backend
cp .env.example .env
```

### 2. 编辑配置文件

使用文本编辑器打开 `.env` 文件：

```bash
# Linux/Mac
nano .env

# Windows
notepad .env
```

### 3. 配置必要参数

至少需要配置以下变量：

```bash
# LLM API 配置（必需）
LLM_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1

# 应用环境
APP_ENV=production
```

### 4. 验证配置

```bash
# 启动服务
docker-compose up -d

# 检查日志
docker-compose logs backend
```

---

## 环境变量配置

### 配置优先级

环境变量按以下优先级加载（从高到低）：

1. 系统环境变量
2. `.env` 文件中的配置
3. 默认值

### 配置分类

#### 核心配置（必需）

这些配置必须设置，否则应用无法正常运行。

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM API 密钥 | `sk-xxx` |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.openai.com/v1` |

#### 应用配置（可选）

这些配置有合理的默认值，可根据需要调整。

| 变量 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `APP_ENV` | 运行环境 | `production` | `development`, `production`, `testing` |
| `FLASK_HOST` | 监听地址 | `0.0.0.0` | - |
| `FLASK_PORT` | 监听端口 | `5001` | - |
| `FLASK_DEBUG` | 调试模式 | `false` | `true`, `false` |

#### 数据库配置（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DATABASE_URL` | 数据库连接 URL | `sqlite:///./polytheater.db` |
| `DATABASE_POOL_SIZE` | 连接池大小 | `5` |
| `DATABASE_MAX_OVERFLOW` | 最大溢出连接数 | `10` |

#### 网络与安全（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `CORS_ORIGINS` | CORS 允许的源 | `http://localhost:3000,http://localhost:5173` |
| `SECRET_KEY` | Flask 密钥 | 自动生成 |
| `JWT_EXPIRATION` | JWT 过期时间 | `24h` |

#### 日志配置（可选）

| 变量 | 说明 | 默认值 | 可选值 |
|------|------|--------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

#### 模拟配置（可选）

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DEFAULT_MAX_ROUNDS` | 最大模拟轮数 | `144` |
| `DEFAULT_MINUTES_PER_ROUND` | 每轮分钟数 | `60` |

---

## 应用配置

### APP_ENV - 运行环境

控制应用的运行模式。

```bash
# 开发环境 - 启用详细错误、自动重载
APP_ENV=development

# 生产环境 - 优化性能、简化错误
APP_ENV=production

# 测试环境 - 最小化日志、模拟服务
APP_ENV=testing
```

**不同环境的行为差异**：

| 特性 | development | production | testing |
|------|-------------|------------|---------|
| 错误页面 | 详细堆栈 | 通用错误页 | 简化错误 |
| 自动重载 | ✅ | ❌ | ❌ |
| 日志级别 | DEBUG | INFO | WARNING |
| 外部服务 | 真实调用 | 真实调用 | 模拟 |

### FLASK_DEBUG - 调试模式

```bash
# 启用调试模式（仅开发环境）
FLASK_DEBUG=true

# 生产环境必须关闭
FLASK_DEBUG=false
```

**警告**：生产环境启用 `FLASK_DEBUG=true` 会导致安全风险！

---

## 数据库配置

### DATABASE_URL - 连接字符串

#### SQLite（默认）

适合开发和小型部署：

```bash
DATABASE_URL=sqlite:///./polytheater.db
```

#### PostgreSQL（推荐生产环境）

```bash
DATABASE_URL=postgresql://username:password@localhost:5432/polytheater
```

完整格式：
```bash
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require
```

#### MySQL

```bash
DATABASE_URL=mysql://username:password@localhost:3306/polytheater
```

### 连接池配置

```bash
# 连接池大小（并发连接数）
DATABASE_POOL_SIZE=5

# 超出池大小后允许的最大连接数
DATABASE_MAX_OVERFLOW=10

# 连接超时（秒）
DATABASE_POOL_TIMEOUT=30

# 连接回收时间（秒）
DATABASE_POOL_RECYCLE=3600
```

**调优建议**：

- 开发环境：`POOL_SIZE=2`, `MAX_OVERFLOW=5`
- 生产环境：`POOL_SIZE=10`, `MAX_OVERFLOW=20`
- 高并发：根据负载逐步增加

---

## CORS 配置

### CORS_ORIGINS - 允许的源

控制哪些前端可以访问后端 API。

#### 单个源

```bash
CORS_ORIGINS=https://yourdomain.com
```

#### 多个源

使用逗号分隔，**不要有空格**：

```bash
CORS_ORIGINS=https://example.com,https://app.example.com
```

#### 开发环境

```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

### CORS 高级配置

```bash
# 允许的方法
CORS_METHODS=GET,POST,PUT,DELETE,OPTIONS

# 允许的请求头
CORS_ALLOWED_HEADERS=Content-Type,Authorization

# 暴露的响应头
CORS_EXPOSED_HEADERS=X-Total-Count

# 预检请求缓存时间（秒）
CORS_MAX_AGE=600

# 允许携带凭证
CORS_SUPPORTS_CREDENTIALS=true
```

### 安全建议

1. **不要使用通配符** `*` 在生产环境
2. **仅列出信任的域名**
3. **使用 HTTPS** 源
4. **定期审查** 允许的源列表

---

## 日志配置

### LOG_LEVEL - 日志级别

```bash
# 最详细，包含所有调试信息
LOG_LEVEL=DEBUG

# 标准日志，推荐生产环境
LOG_LEVEL=INFO

# 仅警告和错误
LOG_LEVEL=WARNING

# 仅错误
LOG_LEVEL=ERROR

# 仅严重错误
LOG_LEVEL=CRITICAL
```

### 日志格式

默认日志格式包含：

- 时间戳
- 日志级别
- 模块名称
- 消息内容
- 上下文信息（请求 ID、用户 ID 等）

示例输出：
```
2025-03-08 10:00:00 INFO [app.api.stories] [req_abc123] Created story project proj_xyz789
```

### 日志输出

#### 控制台输出（默认）

```bash
# 所有日志输出到 stdout/stderr
# 适合 Docker 容器和现代日志系统
```

#### 文件输出（可选）

```bash
# 启用文件日志
LOG_TO_FILE=true
LOG_FILE_PATH=/var/log/polytheater/app.log
LOG_FILE_MAX_BYTES=10485760  # 10MB
LOG_FILE_BACKUP_COUNT=5     # 保留 5 个备份
```

---

## 模拟配置

### 默认模拟参数

```bash
# 最大模拟轮数
DEFAULT_MAX_ROUNDS=144

# 每轮代表的分钟数
DEFAULT_MINUTES_PER_ROUND=60
```

### 模拟行为配置

```bash
# 是否强制里程碑事件发生
FORCE_MILESTONES=true

# 默认 pacing 策略
DEFAULT_PACING=medium

# 最大并发事件数
MAX_CONCURRENT_EVENTS=5
```

---

## 安全配置

### SECRET_KEY - Flask 密钥

用于会话加密和 CSRF 保护。

```bash
# 生成安全密钥
python -c "import secrets; print(secrets.token_hex(32))"

# 设置密钥
SECRET_KEY=your-generated-secret-key-here
```

**安全建议**：
- 生产环境必须设置唯一的密钥
- 不要使用默认值或示例值
- 定期轮换密钥

### JWT_EXPIRATION - JWT 过期时间

```bash
# 24 小时（默认）
JWT_EXPIRATION=24h

# 7 天
JWT_EXPIRATION=7d

# 1 小时
JWT_EXPIRATION=1h
```

### API 密钥管理

```bash
# 使用环境变量存储敏感密钥
LLM_API_KEY=sk-xxx
ZEP_API_KEY=zep-xxx

# 或使用 Docker secrets（推荐生产环境）
# 参见 deployment.md
```

---

## 配置示例

### 开发环境配置

```bash
# .env.development

# 应用环境
APP_ENV=development
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# LLM 配置
LLM_API_KEY=sk-your-dev-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini

# 数据库（SQLite）
DATABASE_URL=sqlite:///./polytheater_dev.db

# CORS（允许本地开发服务器）
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 日志（详细输出）
LOG_LEVEL=DEBUG

# 模拟配置
DEFAULT_MAX_ROUNDS=50
DEFAULT_MINUTES_PER_ROUND=30
```

### 生产环境配置

```bash
# .env.production

# 应用环境
APP_ENV=production
FLASK_DEBUG=false
FLASK_HOST=0.0.0.0
FLASK_PORT=5001

# LLM 配置
LLM_API_KEY=sk-your-production-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o

# 数据库（PostgreSQL）
DATABASE_URL=postgresql://user:pass@db.example.com:5432/polytheater?sslmode=require
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# CORS（仅允许生产域名）
CORS_ORIGINS=https://yourdomain.com

# 日志（标准输出）
LOG_LEVEL=INFO

# 安全配置
SECRET_KEY=your-production-secret-key
JWT_EXPIRATION=24h

# 模拟配置
DEFAULT_MAX_ROUNDS=144
DEFAULT_MINUTES_PER_ROUND=60
```

### 测试环境配置

```bash
# .env.testing

# 应用环境
APP_ENV=testing
FLASK_DEBUG=false

# LLM 配置（使用模拟或测试密钥）
LLM_API_KEY=sk-test-key
LLM_BASE_URL=https://api.openai.com/v1

# 数据库（独立测试数据库）
DATABASE_URL=sqlite:///./polytheater_test.db

# CORS
CORS_ORIGINS=http://localhost:3000

# 日志（仅警告和错误）
LOG_LEVEL=WARNING

# 模拟配置（快速测试）
DEFAULT_MAX_ROUNDS=10
DEFAULT_MINUTES_PER_ROUND=5
```

---

## 故障排除

### 配置不生效

**症状**：修改 `.env` 后配置未生效

**解决方案**：
```bash
# 1. 检查文件格式（无空格、无 BOM）
cat -A .env

# 2. 重启服务
docker-compose restart backend

# 3. 验证环境变量
docker-compose exec backend env | grep YOUR_VAR
```

### CORS 错误

**症状**：浏览器报告 CORS 错误

**检查清单**：
- [ ] `CORS_ORIGINS` 包含当前前端地址
- [ ] 逗号分隔符后没有空格
- [ ] 协议匹配（http vs https）
- [ ] 端口号正确
- [ ] 已重启后端服务

### 数据库连接失败

**症状**：启动时报告数据库错误

**排查步骤**：
```bash
# 1. 检查 DATABASE_URL 格式
echo $DATABASE_URL

# 2. 测试连接
docker exec -it polytheater-backend python -c "from sqlalchemy import create_engine; create_engine('$DATABASE_URL').connect()"

# 3. 查看数据库日志
docker-compose logs db
```

### 日志不输出

**症状**：看不到预期的日志

**检查**：
```bash
# 1. 确认日志级别
grep LOG_LEVEL .env

# 2. 查看容器日志
docker-compose logs backend | tail -100

# 3. 检查日志驱动
docker inspect polytheater-backend | grep -A 10 LogPath
```

### 配置验证工具

使用内置命令验证配置：

```bash
# 进入容器
docker-compose exec backend bash

# 运行配置检查
python -m app.core.config --check

# 输出当前配置
python -m app.core.config --show
```

---

## 相关文档

- [部署指南](deployment.md) - 部署配置和最佳实践
- [API 文档](api.md) - API 接口说明
- [错误码文档](error_codes.md) - 错误代码详解

---

## 更新历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| 1.0.0 | 2025-03-08 | 初始版本 |
