
## 决策算法设计 (2026-03-09)

**决策**: 采用基于规则的简单优先级评估算法

**内容**:
- 优先级公式：`final = base × personality × urgency`
- 性能目标：决策时间 < 100ms
- 避免复杂的多因素评估，保持算法可预测性

**原因**:
- 简洁易维护
- 性能可保证
- 便于调试和调优

详见：`.sisyphus/drafts/decision-algorithm-design.md`
