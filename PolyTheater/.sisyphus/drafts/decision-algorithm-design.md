# Agent 决策算法设计文档

## 1. 概述

本文档定义 Agent 决策算法的核心逻辑，包括目标优先级评估和行动计划生成。算法设计遵循简洁、可预测、高性能原则。

## 2. 目标优先级评估算法

### 2.1 优先级计算公式

```
final_priority = base_priority × personality_modifier × urgency_modifier
```

### 2.2 参数定义

#### base_priority（基础优先级）
- 范围：1-10（整数）
- 由任务创建者指定
- 默认值：5

#### personality_modifier（性格调整系数）
- 范围：0.5-2.0
- 根据 Agent 性格类型调整

| 性格类型 | 保守型 | 平衡型 | 激进型 |
|---------|-------|-------|-------|
| 系数范围 | 0.5-1.2 | 0.8-1.5 | 1.0-2.0 |

#### urgency_modifier（紧急度系数）
- 范围：1.0-3.0
- 基于时间敏感度计算

| 紧急程度 | 系数 | 触发条件 |
|---------|------|---------|
| 普通 | 1.0 | 无时间压力 |
| 加急 | 1.5 | 截止时间 < 24 小时 |
| 紧急 | 2.0 | 截止时间 < 4 小时 |
| 严重 | 3.0 | 截止时间 < 1 小时 |

### 2.3 优先级分级

根据计算结果将目标分为四级：

| 等级 | 分数范围 | 处理策略 |
|------|---------|---------|
| P0 - 关键 | ≥ 15 | 立即执行，打断当前任务 |
| P1 - 高 | 10-14 | 加入当前批次优先处理 |
| P2 - 中 | 5-9 | 正常队列处理 |
| P3 - 低 | < 5 | 空闲时处理 |

### 2.4 算法伪代码

```python
def calculate_priority(goal, agent_personality, context):
    base = goal.base_priority  # 1-10
    
    # 性格系数
    personality_map = {
        'conservative': (0.5, 1.2),
        'balanced': (0.8, 1.5),
        'aggressive': (1.0, 2.0)
    }
    p_min, p_max = personality_map[agent_personality]
    personality = interpolate(p_min, p_max, goal.alignment_score)
    
    # 紧急度系数
    urgency = calculate_urgency(goal.deadline, context.current_time)
    
    final = base * personality * urgency
    return clamp(final, 0.5, 30.0)

def calculate_urgency(deadline, current_time):
    if not deadline:
        return 1.0
    
    hours_left = (deadline - current_time).total_seconds() / 3600
    
    if hours_left < 1:
        return 3.0
    elif hours_left < 4:
        return 2.0
    elif hours_left < 24:
        return 1.5
    else:
        return 1.0
```

## 3. 行动计划生成逻辑

### 3.1 计划生成流程

```
输入：目标 + 上下文
  ↓
1. 可行性评估
  ↓
2. 步骤分解
  ↓
3. 依赖分析
  ↓
4. 资源检查
  ↓
输出：行动计划
```

### 3.2 可行性评估

评估维度：

1. **能力匹配度** (0-1)
   - Agent 是否具备执行该目标所需的技能
   - 检查：所需技能 ⊆ Agent 技能集

2. **资源可用性** (0-1)
   - 所需工具、权限、数据是否可用
   - 检查：所需资源 ∩ 可用资源 ≠ ∅

3. **时间可行性** (0-1)
   - 预估执行时间 vs 可用时间窗口
   - 检查：estimated_time ≤ available_time

**可行性阈值**：综合得分 ≥ 0.6 视为可行

### 3.3 步骤分解策略

采用层次化分解：

```python
def decompose_goal(goal):
    if is_atomic(goal):
        return [goal]
    
    # 按领域分解
    sub_goals = split_by_domain(goal)
    
    # 按依赖排序
    ordered = topological_sort(sub_goals)
    
    return ordered
```

分解原则：
- 每个子步骤应该是原子的（不可再分）
- 步骤间依赖关系明确
- 单个步骤执行时间 < 5 分钟

### 3.4 依赖分析

依赖类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| blocks | 硬阻塞 | 必须先 A 后 B |
| related | 软关联 | A 和 B 相关但可并行 |
| parent-child | 父子关系 | 大任务拆分子任务 |
| discovered-from | 发现来源 | 工作中发现的新任务 |

### 3.5 计划生成伪代码

```python
def generate_action_plan(goal, context):
    # 1. 可行性评估
    feasibility = assess_feasibility(goal, context)
    if feasibility < 0.6:
        return Plan(status='infeasible', reason=feasibility_report)
    
    # 2. 步骤分解
    steps = decompose_goal(goal)
    
    # 3. 依赖分析
    dependencies = analyze_dependencies(steps)
    
    # 4. 资源检查
    resource_conflicts = check_resources(steps, context)
    if resource_conflicts:
        steps = resolve_conflicts(steps, resource_conflicts)
    
    # 5. 生成计划
    plan = Plan(
        goal=goal,
        steps=steps,
        dependencies=dependencies,
        estimated_time=sum(s.duration for s in steps),
        priority=goal.final_priority
    )
    
    return plan
```

## 4. 性能基准

### 4.1 决策时间要求

| 操作 | 目标时间 | 最大允许时间 |
|------|---------|------------|
| 优先级计算 | < 10ms | 50ms |
| 可行性评估 | < 30ms | 100ms |
| 计划生成 | < 50ms | 200ms |
| **总决策时间** | **< 100ms** | **350ms** |

### 4.2 性能优化策略

1. **缓存机制**
   - 缓存相同目标的可行性评估结果
   - TTL：5 分钟

2. **懒加载**
   - 仅在需要时计算详细计划
   - 初步筛选使用轻量评估

3. **并行处理**
   - 独立的可行性检查并行执行
   - 资源检查与依赖分析并行

### 4.3 基准测试场景

```python
# 场景 1：简单目标（原子任务）
# 预期：< 50ms

# 场景 2：中等目标（3-5 个子步骤）
# 预期：< 100ms

# 场景 3：复杂目标（10+ 子步骤，多依赖）
# 预期：< 350ms
```

## 5. 数据结构定义

### 5.1 Goal

```typescript
interface Goal {
  id: string
  title: string
  description: string
  base_priority: number  // 1-10
  deadline?: Date
  required_skills: string[]
  required_resources: string[]
  estimated_duration: number  // 分钟
  final_priority?: number  // 计算后
}
```

### 5.2 ActionPlan

```typescript
interface ActionPlan {
  id: string
  goal_id: string
  status: 'feasible' | 'infeasible' | 'pending_review'
  steps: ActionStep[]
  dependencies: Dependency[]
  estimated_time: number  // 分钟
  priority: number
  created_at: Date
}
```

### 5.3 ActionStep

```typescript
interface ActionStep {
  id: string
  description: string
  duration: number  // 分钟
  dependencies: string[]  // 依赖的步骤 ID
  required_resources: string[]
}
```

### 5.4 Dependency

```typescript
interface Dependency {
  from: string  // 步骤 ID
  to: string    // 步骤 ID
  type: 'blocks' | 'related' | 'parent-child' | 'discovered-from'
}
```

## 6. 错误处理

### 6.1 异常情况

| 异常 | 处理策略 |
|------|---------|
| 资源不可用 | 返回 infeasible，列出缺失资源 |
| 依赖循环 | 检测并报告循环依赖 |
| 超时 | 返回部分计划，标记未完成步骤 |
| 优先级计算失败 | 使用默认优先级 5 |

### 6.2 降级策略

当性能超时时：
1. 跳过详细依赖分析
2. 使用简化的可行性检查
3. 返回最小可行计划

## 7. 扩展点

### 7.1 预留接口

```python
# 自定义优先级规则（未来）
class PriorityRule:
    def evaluate(self, goal, context) -> float:
        pass

# 自定义分解策略（未来）
class DecompositionStrategy:
    def decompose(self, goal) -> List[Goal]:
        pass
```

### 7.2 配置项

```yaml
decision_algorithm:
  priority:
    min_base: 1
    max_base: 10
    default_personality: 'balanced'
  
  planning:
    feasibility_threshold: 0.6
    max_steps_before_review: 10
    atomic_step_max_duration: 5  # 分钟
  
  performance:
    target_decision_time_ms: 100
    cache_ttl_seconds: 300
```

## 8. 评审检查清单

- [ ] 优先级算法简洁易懂
- [ ] 未引入复杂的多因素评估
- [ ] 性能基准明确且可测量
- [ ] 数据结构定义完整
- [ ] 错误处理覆盖主要场景
- [ ] 预留扩展点但保持核心简洁

## 9. 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|---------|
| 1.0 | 2026-03-09 | 初始版本 |
