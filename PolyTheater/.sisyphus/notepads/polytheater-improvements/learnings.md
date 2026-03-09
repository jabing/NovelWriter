## Task 1.1: flask_cors 依赖修复 (2026-03-09)

### 发现
1. **依赖安装位置很重要**
   - 使用 `pip install` 会安装到用户目录（`~/.local/`），但可能不是正确的 Python 环境
   - 使用 `python -m pip install` 确保安装到当前 Python 环境（`/home/jabing/py14env/`）
   - 测试时使用 `python -m pytest` 而不是直接 `pytest`，确保使用正确的环境

2. **requirements.txt 结构**
   - 已有按功能分组的注释结构：Web 框架、LLM、知识图谱、异步支持等
   - `flask-cors>=4.0.0` 应添加到 "Web 框架" 部分，在 flask 和 flask-sqlalchemy 之间（按字母顺序）

3. **CORS 配置现状**
   - `backend/main.py` 已有完整的 CORS 配置（lines 5, 26-32）
   - 配置从 `config.py` 导入：`CORS_ORIGINS, CORS_SUPPORTS_CREDENTIALS, CORS_METHODS, CORS_ALLOW_HEADERS`
   - 只缺少 `flask-cors` 依赖包

### 验证方法
```bash
# 1. 验证导入
python -c "import flask_cors; print(flask_cors.__version__)"
# 输出: 6.0.2

# 2. 运行测试（使用 python -m pytest）
python -m pytest tests/test_end_to_end.py -v
# 结果: 9 passed, 10 failed（无 CORS 导入错误）
```

### 残留问题（非本任务范围）
- SQLite 数据库文件访问问题：`unable to open database file`
- 部分 API 返回 400 而非 201
- 部分测试期望 400 但收到 201
- KeyError: 'entity_id' 问题

### 最佳实践
- 始终使用 `python -m pip` 和 `python -m pytest` 确保环境一致性
- 在 requirements.txt 中按字母顺序和功能分组添加依赖
- 测试失败时，区分"导入错误"和"逻辑错误"

## Task 1.2: Project 数据模型创建 (2026-03-09)

### 发现
1. **SQLAlchemy 2.0 的 Mapped 类型**
   - 使用 `Mapped[Optional[int]]` 和 `mapped_column()` 定义字段
   - ForeignKey 使用 `ForeignKey('table.column')` 语法
   - relationship 使用 `relationship('ClassName', back_populates='field')` 语法
   - 时间字段使用 `String(32)` 存储ISO格式字符串，而不是DateTime

2. **LSP 错误的误报**
   - basedpyright 会报告 "No parameter named" 错误
   - 这是因为 SQLAlchemy 动态生成 __init__ 方法
   - 这是已知问题，可以忽略，实际运行时正常
   - 测试导入和数据库迁移是真正的验证方法

3. **数据库迁移测试**
   - 使用内存 SQLite (`sqlite:///:memory:`) 进行测试
   - `db.create_all()` 创建所有表
   - `db.inspect(db.engine).get_table_names()` 检查表
   - `db.inspect(db.engine).get_columns('table')` 检查列

4. **模型设计遵循现有模式**
   - 保持与 CharacterDB 和 StoryEventDB 相同的字段风格
   - 添加 __repr__ 方法以保持一致性
   - 保持 docstring 风格一致

### 验证方法
```bash
# 1. 验证模型导入
python -c "from app.models.db_models import ProjectDB; print(ProjectDB.__tablename__)"
# 输出: projects

# 2. 验证字段存在
python -c "from app.models.db_models import CharacterDB; print(hasattr(CharacterDB, 'project_id'))"
# 输出: True

# 3. 验证数据库迁移（使用内存数据库）
python -c "from flask import Flask; from app.database import db; ..."
# 输出: Tables created: ['characters', 'projects', 'story_events']
```

### 最佳实践
- 使用内存 SQLite 进行快速测试，避免文件权限问题
- 忽略 SQLAlchemy 模型的 LSP 静态分析错误
- 添加外键时，同时添加 relationship 字段保持双向引用
- 保持代码风格与现有模型一致

## Task 1.3: Projects API 实现 (2026-03-09)

### 发现
1. **Flask Blueprint 模式**
   - 使用 Blueprint 组织 API 路由：`projects_bp = Blueprint('projects', __name__)`
   - 在 main.py 注册：`app.register_blueprint(projects_bp)`
   - Blueprint 可以有自己的 url_prefix，但这里直接在路由中指定完整路径

2. **Pydantic 验证模式**
   - 创建 schemas/project.py 定义请求验证
   - 使用 `ProjectCreate` 和 `ProjectUpdate` 分别验证创建和更新
   - `model_dump(exclude_unset=True)` 只获取用户设置的字段

3. **错误处理模式**
   - 使用统一的 `error_response()` 函数
   - 使用 ErrorCode 枚举定义错误类型
   - 返回结构化的错误响应：`{"error": ..., "message": ...}`

### 最佳实践
- API 路由使用 `/api/<resource>` 前缀
- 创建返回 201，更新返回 200，删除返回 200
- 使用 Pydantic 进行请求验证，分离验证逻辑

## Task 1.4: 数据库迁移和测试 (2026-03-09)

### 发现
1. **pytest fixture 最佳实践**
   - 在 conftest.py 中创建共享的 test_app 和 test_client fixtures
   - 使用 `yield` 模式进行 setup/teardown
   - 使用独立的 Flask app 实例而非修改全局 app

2. **数据库 fixture 设计**
   - 创建 test_app fixture 使用独立的 Flask 实例
   - 设置 `SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'`
   - 在 app_context 中创建表，测试后删除表
   - 避免修改 main.py 的全局 app 配置

3. **测试隔离问题**
   - 不要在测试中修改全局 Flask app 配置
   - 每个测试文件应该使用独立的 test_app fixture
   - SQLite 内存数据库必须在使用前创建所有表

4. **测试改进结果**
   - 添加 conftest.py fixtures 后：610→620 通过，23→13 失败
   - 新增 34 个项目测试全部通过
   - 修复了 10 个原有测试（fixture 配置问题）

### 验证方法
```bash
# 运行新测试
python -m pytest tests/test_project_model.py tests/test_project_api.py -v
# 结果: 34 passed

# 运行所有测试
python -m pytest tests/ -v --tb=line -q
# 结果: 620 passed, 13 failed
```

### 最佳实践
- 在 conftest.py 创建共享 fixtures，避免每个测试文件重复设置
- 测试数据库使用内存 SQLite，速度快且无文件权限问题
- 测试 docstrings 是必要的，用于记录测试目的
- 使用 test_app.app_context() 进行数据库操作

## Task 2.2: characterStore 创建 (2026-03-09)

### 发现

1. **Pinia Composition API 风格**
   - 使用 `defineStore('store-name', () => { ... })` setup 函数风格
   - State 使用 `ref()` 定义，Computed 使用 `computed()`
   - Actions 是普通函数，无需额外装饰器
   - 最后返回所有需要暴露的状态和方法

2. **Store 与 API 层的分离**
   - Store 调用 `characterApi` 方法，不直接使用 axios
   - Store 处理状态管理（loading, error），API 层处理 HTTP 请求
   - API 响应格式：`{ success, data, message, timestamp }`

3. **角色定位分组**
   - 角色有 4 个层级：protagonist, major, minor, public
   - 使用 computed 属性 `charactersByRole` 自动分组
   - 提供便捷的 computed：protagonists, majorCharacters

4. **与 storyStore 联动设计**
   - 使用 `currentProjectId` 状态跟踪当前项目
   - 提供 `setCurrentProject(projectId)` 方法供 storyStore 调用
   - 项目切换时自动清除旧数据并加载新数据

5. **错误处理模式**
   - 每个 action 都有 try-catch-finally 结构
   - loading 状态在 finally 中重置
   - error 状态存储错误信息，供 UI 显示

### 验证方法

```javascript
// 1. 导入 store
import { useCharacterStore } from '@/stores/characterStore'

// 2. 在组件中使用
const characterStore = useCharacterStore()
await characterStore.fetchCharacters('project-123')

// 3. 访问状态
console.log(characterStore.characters)
console.log(characterStore.protagonists)
```

### 最佳实践

- Store 使用 Composition API 风格，更灵活且类型推断更好
- 所有异步操作都有 loading 和 error 状态管理
- 使用 JSDoc 注释提供类型信息和 API 文档
- 分离状态管理和数据获取逻辑（Store vs API layer）
