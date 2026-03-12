# CharacterSelector 性能基准测试报告

## 测试概述

**测试日期**: 2026-03-09  
**测试文件**: `tests/performance/test_character_selector_1000.py`  
**Python 版本**: 3.14.3  
**pytest 版本**: 9.0.2  

## 性能目标

| 场景 | 目标 | 状态 |
|------|------|------|
| 1000 角色选择 | < 100ms | ✅ 达成 |
| 5000 角色选择 | < 500ms | ✅ 达成 |

## 测试角色分布 (1000 角色)

| Tier | 数量 | 占比 | 单角色预算 | 总预算 |
|------|------|------|-----------|--------|
| Tier 0 (核心主角) | 10 | 1% | 500 tokens | 5,000 tokens |
| Tier 1 (重要配角) | 90 | 9% | 300 tokens | 27,000 tokens |
| Tier 2 (普通配角) | 400 | 40% | 100 tokens | 40,000 tokens |
| Tier 3 (社会公众) | 500 | 50% | 0 tokens | 0 tokens |
| **总计** | **1,000** | **100%** | - | **72,000 tokens** |

## 测试结果

### 1. 主要性能测试 (1000 角色)

**测试方法**: `test_selection_performance_1000_chars`

- **场景**: 1000 角色，提及 90 个角色 (10 个 tier-0 + 30 个 tier-1 + 50 个 tier-2)
- **总预算**: 6000 tokens
- **结果**: ✅ PASSED
- **性能**: < 100ms
- **验证**:
  - 所有 10 个 tier-0 角色必须被选中
  - 剩余预算非负
  - 选择结果一致性

### 2. 少数提及测试

**测试方法**: `test_selection_performance_few_mentions`

- **场景**: 1000 角色，仅提及 3 个角色
- **总预算**: 4000 tokens
- **结果**: ✅ PASSED
- **性能**: < 100ms

### 3. 一致性测试

**测试方法**: `test_selection_consistency`

- **场景**: 连续 5 次运行相同选择
- **结果**: ✅ PASSED
- **验证**: 5 次运行产生完全相同的结果

### 4. 预算约束测试

**测试方法**: `test_budget_constraints`

- **测试预算**: [5000, 6000, 7000, 8000, 10000] tokens
- **结果**: ✅ PASSED
- **验证**:
  - 剩余预算始终非负
  - 预算计算准确
  - 不同预算下的选择行为正确

### 5. Tier 分布测试

**测试方法**: `test_tier_distribution_in_selection`

- **结果**: ✅ PASSED
- **验证**:
  - 所有 tier-0 角色被选中 (10 个)
  - Tier-3 角色不被选中 (模板处理)
  - Tier-1/2 根据预算和提及情况选择

### 6. 压力测试 (5000 角色)

**测试方法**: `test_selection_performance_5000_chars`

- **场景**: 5000 角色 (50 个 tier-0 + 450 个 tier-1 + 2000 个 tier-2 + 2500 个 tier-3)
- **总预算**: 4000 tokens
- **结果**: ✅ PASSED
- **性能**: < 500ms

## 性能分析

### 选择算法复杂度

CharacterSelector 使用线性扫描策略：

1. **Tier-0 选择**: O(n) - 扫描所有角色，选择所有 tier-0
2. **Tier-1 选择**: O(n × m) - 扫描所有角色，检查是否在提及列表中 (m 为提及数量)
3. **Tier-2 选择**: O(n × m) - 同 tier-1

总体复杂度：**O(n × m)**，其中：
- n = 角色总数
- m = 提及的角色数量

### 性能优化建议

如果未来性能下降，可考虑：

1. **预索引**: 为角色名建立哈希索引，加速提及检查
2. **按 tier 分组**: 预先按 tier 分组角色，减少扫描范围
3. **并行处理**: 对不同 tier 的选择进行并行处理

## 测试命令

```bash
# 运行所有性能测试
cd /mnt/c/dev_projects/NovelWriter/Writer
python -m pytest tests/performance/test_character_selector_1000.py -v

# 运行单个测试
python -m pytest tests/performance/test_character_selector_1000.py::TestCharacterSelectorPerformance::test_selection_performance_1000_chars -v

# 运行压力测试
python -m pytest tests/performance/test_character_selector_1000.py::TestCharacterSelectorStress::test_selection_performance_5000_chars -v
```

## 结论

CharacterSelector 在 1000 角色和 5000 角色场景下均满足性能目标：

- ✅ **1000 角色选择时间 < 100ms**
- ✅ **5000 角色选择时间 < 500ms**

当前实现采用简单的线性扫描策略，对于预期规模 (≤5000 角色) 表现良好。

## 附录：测试文件位置

- **测试文件**: `/mnt/c/dev_projects/NovelWriter/Writer/tests/performance/test_character_selector_1000.py`
- **被测代码**: `/mnt/c/dev_projects/NovelWriter/Writer/src/novel/character_selector.py`
- **角色模型**: `/mnt/c/dev_projects/NovelWriter/Writer/src/novel/character_profile.py`

---

*报告生成时间*: 2026-03-09  
*测试执行时间*: 0.88s (全部 6 项测试)
