# 🎬 PolyTheater - 多视角故事世界引擎

> **One World, Infinite Perspectives**  
> 一个故事世界，无限视角叙事

---

## 📖 项目简介

**PolyTheater** 是一个基于知识图谱和多智能体模拟的多视角故事生成引擎。借鉴 MiroFish 的预测引擎架构，将其创新性地应用于创意写作领域。

### 核心特性

- 🌐 **知识图谱构建** - 将故事世界观、人物关系转化为结构化图谱
- 👥 **多视角叙事** - 每个主角有独立的视角 Agent，生成风格独特的叙事
- 🎭 **角色分层架构** - 核心主角、重要配角、普通配角、社会公众 4 层设计
- ⏱️ **节奏控制** - 智能控制故事节奏，确保里程碑事件发生
- 🔄 **记忆演化** - 图谱从"过去"演化到"未来"，支持长期一致性
- 🎨 **视角偏向** - 性别、MBTI、认知风格影响叙事声音

---

## 🏗️ 项目结构

```
polytheater/
├── backend/                 # Python 后端
│   ├── app/
│   │   ├── core/           # 核心模块
│   │   ├── graph/          # 知识图谱层
│   │   ├── agents/         # Agent 管理层
│   │   ├── simulation/     # 模拟控制层
│   │   ├── narrative/      # 叙事生成层
│   │   ├── api/            # API 层
│   │   └── utils/          # 工具模块
│   ├── scripts/            # 脚本
│   └── tests/              # 测试
│
├── frontend/               # Vue 3 前端
│   └── src/
│       ├── views/          # 页面视图
│       ├── components/     # 组件
│       └── api/            # API 调用
│
├── docs/                   # 文档
│   ├── architecture.md     # 架构说明
│   ├── api.md             # API 文档
│   └── tutorial.md        # 教程
│
└── examples/              # 示例项目
    ├── mystery_novel/     # 悬疑小说
    └── romance_story/     # 言情故事
```

---

## 🚀 快速开始

### 环境要求

#### Docker 部署（推荐）
- Docker 20.10+
- Docker Compose 2.0+

#### 本地开发
- Python 3.11+
- Node.js 18+
- uv (Python 包管理器)

### 安装

```bash
# 克隆项目
cd /mnt/c/dev_projects
git clone <repo-url> PolyTheater
cd PolyTheater

# 安装后端依赖
cd backend
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
uv pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install
```

### 配置

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑配置文件
nano backend/.env
```

**必需配置项**：

```bash
# LLM API 配置
LLM_API_KEY=your-api-key
LLM_BASE_URL=https://api.openai.com/v1

# 应用环境
APP_ENV=production

# CORS 配置（生产环境修改为实际域名）
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 日志级别
LOG_LEVEL=INFO

# 数据库连接（默认 SQLite，生产环境建议 PostgreSQL）
DATABASE_URL=sqlite:///./polytheater.db
```

详细配置说明请查看 [配置指南](docs/configuration.md)。

### 启动

#### 方式一：Docker 部署（推荐）

```bash
# 配置环境变量
cp backend/.env.example backend/.env

# 编辑配置文件，填入必要参数
nano backend/.env

# 一键启动
docker-compose up -d

# 访问应用
open http://localhost
```

**配置检查清单**：

- [ ] `LLM_API_KEY` - 填入你的 API 密钥
- [ ] `LLM_BASE_URL` - 确认 API 地址
- [ ] `APP_ENV` - 设置运行环境（development/production）
- [ ] `CORS_ORIGINS` - 配置允许的源
- [ ] `LOG_LEVEL` - 设置日志级别
- [ ] `DATABASE_URL` - 配置数据库连接

详细部署说明请查看：
- [部署指南](docs/deployment.md) - Docker 部署、生产环境配置
- [配置指南](docs/configuration.md) - 环境变量详解、故障排除

#### 方式二：本地开发

```bash
# 启动后端
cd backend
python main.py

# 启动前端（新终端）
cd frontend
npm run dev
```

访问 http://localhost:3000 开始使用。

---

## 📚 文档

### 核心文档

- [架构设计](docs/architecture.md)
- [API 文档](docs/api.md)
- [使用教程](docs/tutorial.md)
- [数据模型](docs/data_models.md)

### 部署与配置

- [部署指南](docs/deployment.md) - Docker 部署、生产环境配置
- [配置指南](docs/configuration.md) - 环境变量、应用配置详解
- [错误码文档](docs/error_codes.md) - 错误代码说明和排查指南

---

## 🛠️ 技术栈

### 后端
- Flask 3.0+ - Web 框架
- Zep Cloud - 知识图谱
- OpenAI API - LLM 调用
- asyncio - 异步处理

### 前端
- Vue 3.5+ - 前端框架
- Vite 7+ - 构建工具
- D3.js 7+ - 数据可视化
- Axios - HTTP 客户端

---

## 🗓️ 开发路线图

### Phase 1: 基础架构 (2-3周)
- [x] 项目初始化
- [ ] 知识图谱模块
- [ ] 本体生成器
- [ ] 基础 API

### Phase 2: Agent 系统 (3-4周)
- [ ] 角色人设生成器
- [ ] 认知图谱管理器
- [ ] Agent 分层架构

### Phase 3: 模拟引擎 (4-5周)
- [ ] 故事世界模拟器
- [ ] 节奏控制器
- [ ] 里程碑检查器

### Phase 4: 叙事生成 (3-4周)
- [ ] 视角偏向系统
- [ ] Perspective Agent
- [ ] 叙事质量检查

### Phase 5: 前端界面 (4-5周)
- [ ] 故事世界视图
- [ ] 章节编辑器
- [ ] 多视角预览

---

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)。

---

## 📄 许可证

MIT License

---

## 🙏 致谢

本项目借鉴了 [MiroFish](https://github.com/xxx/mirofish) 的优秀架构设计，特此感谢！
