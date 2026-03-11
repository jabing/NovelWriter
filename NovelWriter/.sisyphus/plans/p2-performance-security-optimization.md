# P2: 性能优化与安全加固计划

## TL;DR

> **目标**: 性能优化、安全加固、文档生态完善
> 
> **时间线**: 3个月
> 
> **关键成果**: 
> - 1000+角色选择 < 100ms
> - 200+章节知识图谱查询 < 1s
> - API限流和安全认证
> - 完整文档生态

---

## Context

### 当前状态

**已完成**:
- ✅ P0: 基础设施修复 (测试通过率 99.7%)
- ✅ P1: 核心功能增强 (novelwriter-shared, Writer-LSP集成)

**当前性能**:
- CharacterSelector: 代码简洁，需基准测试
- KnowledgeGraph: 已有索引系统，需大规模测试
- API: 无限流，无认证

**安全状态**:
- API密钥明文存储
- 无请求限流
- 无数据加密

---

## Work Objectives

### 目标

1. **性能优化**: 支持大规模场景 (1000+角色, 200+章节)
2. **安全加固**: API限流、数据加密、认证
3. **文档完善**: 完整的贡献者指南和架构文档

---

## TODOs

### Wave 1: 性能基准测试 (Week 1)

- [ ] **P2-BENCH-1. 建立性能基准测试框架**

  **What to do**:
  - 创建 `tests/performance/` 目录
  - 安装 pytest-benchmark
  - 创建基准测试配置

  **Implementation**:
  ```bash
  # 安装依赖
  pip install pytest-benchmark memory_profiler

  # 创建目录
  mkdir -p Writer/tests/performance
  ```

  **Acceptance Criteria**:
  - [ ] pytest-benchmark 配置完成
  - [ ] 可运行基准测试
  - [ ] 生成性能报告

- [ ] **P2-BENCH-2. CharacterSelector 基准测试**

  **What to do**:
  - 测试 100/500/1000/5000 角色场景
  - 测量选择时间
  - 测量内存使用

  **Performance Target**:
  - 100角色: < 10ms
  - 500角色: < 50ms
  - 1000角色: < 100ms
  - 5000角色: < 500ms

  **Acceptance Criteria**:
  - [ ] 基准测试文件创建
  - [ ] 性能数据记录
  - [ ] 瓶颈识别

- [ ] **P2-BENCH-3. KnowledgeGraph 基准测试**

  **What to do**:
  - 测试 50/100/200/500 章节场景
  - 测量查询时间
  - 测量内存使用

  **Performance Target**:
  - 50章节: < 100ms
  - 100章节: < 300ms
  - 200章节: < 1000ms
  - 500章节: < 3000ms

  **Acceptance Criteria**:
  - [ ] 基准测试文件创建
  - [ ] 性能数据记录
  - [ ] 瓶颈识别

---

### Wave 2: 性能优化 (Week 2-3)

- [ ] **P2-OPT-1. CharacterSelector 性能优化**

  **What to do**:
  - 分析基准测试结果
  - 实现缓存机制 (LRU Cache)
  - 优化选择算法
  - 批量处理支持

  **Implementation**:
  ```python
  from functools import lru_cache
  
  @lru_cache(maxsize=128)
  def _get_tier_characters(self, tier: int) -> tuple:
      # Cache tier lookups
      pass
  ```

  **Acceptance Criteria**:
  - [ ] 性能提升 > 50%
  - [ ] 1000角色 < 100ms
  - [ ] 内存使用合理

- [ ] **P2-OPT-2. KnowledgeGraph 性能优化**

  **What to do**:
  - 实现增量更新
  - 添加查询缓存
  - 优化索引结构
  - 支持批量操作

  **Implementation**:
  ```python
  from functools import lru_cache
  import hashlib

  @lru_cache(maxsize=256)
  def _cached_query(self, query_hash: str) -> list:
      pass
  ```

  **Acceptance Criteria**:
  - [ ] 200章节查询 < 1s
  - [ ] 增量更新工作正常
  - [ ] 内存使用 < 500MB

---

### Wave 3: 安全加固 (Week 4-6)

- [ ] **P2-SEC-1. API 请求限流**

  **What to do**:
  - 实现基于 IP 的请求限流
  - 使用 slowapi 或自定义中间件
  - 配置限流策略

  **Implementation**:
  ```python
  from fastapi import Request
  from slowapi import Limiter
  from slowapi.util import get_remote_address

  limiter = Limiter(key_func=get_remote_address)

  @app.get("/api/characters")
  @limiter.limit("100/minute")
  async def get_characters(request: Request):
      pass
  ```

  **Acceptance Criteria**:
  - [ ] 限流中间件实现
  - [ ] 超限返回 429 状态码
  - [ ] 配置可调整

- [ ] **P2-SEC-2. API 密钥加密存储**

  **What to do**:
  - 使用 cryptography 库加密
  - 实现密钥管理
  - 安全存储配置

  **Implementation**:
  ```python
  from cryptography.fernet import Fernet
  import keyring

  class SecureConfig:
      def __init__(self):
          self._key = keyring.get_password("novelwriter", "encryption_key")
          self._cipher = Fernet(self._key)

      def encrypt(self, value: str) -> str:
          return self._cipher.encrypt(value.encode()).decode()

      def decrypt(self, value: str) -> str:
          return self._cipher.decrypt(value.encode()).decode()
  ```

  **Acceptance Criteria**:
  - [ ] API 密钥加密存储
  - [ ] 安全密钥管理
  - [ ] 无明文敏感数据

- [ ] **P2-SEC-3. HTTPS 配置**

  **What to do**:
  - 生成自签名证书（开发）
  - 配置 FastAPI HTTPS
  - 文档说明生产配置

  **Acceptance Criteria**:
  - [ ] HTTPS 配置完成
  - [ ] 开发证书生成
  - [ ] 文档完善

- [ ] **P2-SEC-4. 安全审计**

  **What to do**:
  - 运行安全扫描工具
  - 检查依赖漏洞
  - 修复安全问题

  **Implementation**:
  ```bash
  pip install safety bandit
  safety check
  bandit -r src/
  ```

  **Acceptance Criteria**:
  - [ ] 无高危漏洞
  - [ ] 安全报告生成
  - [ ] 问题修复完成

---

### Wave 4: 文档完善 (Week 7-10)

- [ ] **P2-DOC-1. CONTRIBUTING.md**

  **What to do**:
  - 贡献流程说明
  - 代码风格指南
  - PR 检查清单

  **Content**:
  - 开发环境搭建
  - 代码规范
  - 测试要求
  - PR 流程

  **Acceptance Criteria**:
  - [ ] CONTRIBUTING.md 创建
  - [ ] 包含完整流程
  - [ ] 符合社区标准

- [ ] **P2-DOC-2. ARCHITECTURE.md**

  **What to do**:
  - 系统架构图
  - 模块依赖关系
  - 数据流图

  **Content**:
  - 系统概览
  - 组件说明
  - 接口定义
  - 部署架构

  **Acceptance Criteria**:
  - [ ] 架构图创建
  - [ ] 模块说明完整
  - [ ] 新开发者可理解

- [ ] **P2-DOC-3. API 使用示例**

  **What to do**:
  - 创建 examples/ 目录
  - 编写使用示例
  - 添加 Jupyter notebooks

  **Content**:
  - 快速开始
  - 常见用例
  - 最佳实践

  **Acceptance Criteria**:
  - [ ] 10+ 使用示例
  - [ ] 代码可运行
  - [ ] 文档注释完整

- [ ] **P2-DOC-4. 性能调优指南**

  **What to do**:
  - 性能基准数据
  - 优化建议
  - 故障排查

  **Content**:
  - 性能基准
  - 优化方法
  - 监控指标
  - 故障排查

  **Acceptance Criteria**:
  - [ ] 基准数据记录
  - [ ] 优化建议明确
  - [ ] 可操作性强

---

### Wave 5: 最终验证 (Week 11-12)

- [ ] **P2-FV-1. 性能验证**

  **What to do**:
  - 运行所有性能测试
  - 验证目标达成
  - 生成性能报告

  **Verification Commands**:
  ```bash
  cd Writer && pytest tests/performance/ -v --benchmark-only
  ```

  **Acceptance Criteria**:
  - [ ] 1000角色 < 100ms
  - [ ] 200章节 < 1s
  - [ ] 无性能退化

- [ ] **P2-FV-2. 安全验证**

  **What to do**:
  - 运行安全扫描
  - 验证加密存储
  - 测试限流功能

  **Verification Commands**:
  ```bash
  safety check
  bandit -r src/
  ```

  **Acceptance Criteria**:
  - [ ] 无安全漏洞
  - [ ] 敏感数据加密
  - [ ] 限流工作正常

- [ ] **P2-FV-3. 文档验证**

  **What to do**:
  - 检查文档完整性
  - 验证示例可运行
  - 新开发者测试

  **Acceptance Criteria**:
  - [ ] 所有文档完整
  - [ ] 示例可运行
  - [ ] 新开发者可理解

---

## Execution Strategy

### 依赖关系

```
Wave 1 (基准测试):
├── P2-BENCH-1 (框架) [quick]
├── P2-BENCH-2 (CharacterSelector) [unspecified-high]
└── P2-BENCH-3 (KnowledgeGraph) [unspecified-high]

Wave 2 (优化) - 依赖 Wave 1:
├── P2-OPT-1 (CharacterSelector) [deep]
└── P2-OPT-2 (KnowledgeGraph) [deep]

Wave 3 (安全) - 独立:
├── P2-SEC-1 (限流) [quick]
├── P2-SEC-2 (加密) [unspecified-high]
├── P2-SEC-3 (HTTPS) [quick]
└── P2-SEC-4 (审计) [quick]

Wave 4 (文档) - 独立:
├── P2-DOC-1 (CONTRIBUTING) [writing]
├── P2-DOC-2 (ARCHITECTURE) [writing]
├── P2-DOC-3 (示例) [writing]
└── P2-DOC-4 (性能指南) [writing]

Wave 5 (验证) - 依赖所有:
├── P2-FV-1 (性能) [deep]
├── P2-FV-2 (安全) [quick]
└── P2-FV-3 (文档) [quick]
```

### 并行执行

- Wave 1: 串行（框架先建）
- Wave 2: 并行（两个优化独立）
- Wave 3: 并行（4个安全任务独立）
- Wave 4: 并行（4个文档任务独立）
- Wave 5: 并行（3个验证独立）

---

## Success Criteria

### 定量指标

- [ ] 1000角色选择 < 100ms
- [ ] 200章节查询 < 1s
- [ ] 0 高危安全漏洞
- [ ] 文档覆盖率 > 80%

### 定性指标

- [ ] 新开发者可在 30 分钟内上手
- [ ] 所有示例可运行
- [ ] 安全审计通过

---

## Commit Strategy

**Wave 1**:
```
test(perf): add performance benchmark framework
```

**Wave 2**:
```
perf(selector): optimize character selection with caching
perf(graph): optimize knowledge graph queries
```

**Wave 3**:
```
feat(security): add API rate limiting
feat(security): add encrypted config storage
feat(security): add HTTPS support
```

**Wave 4**:
```
docs: add CONTRIBUTING.md
docs: add ARCHITECTURE.md
docs: add API examples
```

**Wave 5**:
```
test(perf): verify performance targets met
test(security): verify security audit passed
docs: verify documentation completeness
```
