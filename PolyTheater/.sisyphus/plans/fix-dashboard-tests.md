# 修复 Dashboard 增强版 E2E 测试

## TL;DR

> **Quick Summary**: 修复 5 个失败的 Dashboard 增强版 E2E 测试，添加组件加载等待逻辑
> 
> **Deliverables**: 
> - 修改 `frontend/tests/e2e/dashboard-enhanced.spec.js` 添加等待逻辑
> - 所有 25 个 E2E 测试通过
> 
> **Estimated Effort**: Quick (5-10 分钟)
> **Parallel Execution**: NO - single task
> **Critical Path**: Task 1

---

## Context

### Problem Analysis
当前 E2E 测试结果：
- **总计**: 25 个测试
- **通过**: 20 个 (80%) ✅
- **失败**: 5 个 (20%) ❌

**失败的测试** (全部来自 `dashboard-enhanced.spec.js`):
1. Dashboard 页面应该加载增强版
2. Dashboard 应该显示统计卡片
3. Dashboard 应该显示图表
4. Dashboard 应该显示活动区域
5. Dashboard 应该有刷新按钮

### Root Cause
DashboardEnhanced.vue 组件使用了：
- ECharts 图表库（需要初始化时间）
- dashboardStore（异步加载数据）
- vue-echarts 组件（渲染需要时间）

测试在组件完全渲染前就检查元素，导致找不到选择器。

### Solution
在每个测试开始时添加 `page.waitForSelector('.dashboard-enhanced')` 等待组件加载。

---

## Work Objectives

### Core Objective
修复 5 个失败的 Dashboard 增强版测试，使所有 E2E 测试通过。

### Concrete Deliverables
- 修改 `frontend/tests/e2e/dashboard-enhanced.spec.js`
- 添加组件加载等待逻辑
- 运行测试验证全部通过

### Definition of Done
- [ ] 所有 25 个 E2E 测试通过
- [ ] 测试运行时间 < 30 秒

---

## Must Have
- 每个测试添加 `waitForSelector('.dashboard-enhanced')`
- 保持现有测试逻辑不变
- 不修改组件代码

## Must NOT Have (Guardrails)
- 不要修改 DashboardEnhanced.vue 组件
- 不要删除现有测试
- 不要降低断言标准

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (Playwright)
- **Automated tests**: YES (already configured)
- **Framework**: Playwright

### QA Policy
运行 `npm run test:e2e` 验证所有测试通过。

---

## Execution Strategy

### Single Task (Sequential)

```
Task 1: 修复 dashboard-enhanced.spec.js 测试文件
```

---

## TODOs

- [x] 1. 修复 Dashboard 增强版测试

  **What to do**:
  - 打开 `frontend/tests/e2e/dashboard-enhanced.spec.js`
  - 在每个测试的 `await page.goto('/dashboard')` 后添加：
    ```javascript
    await page.waitForSelector('.dashboard-enhanced', { timeout: 5000 });
    ```
  - 确保所有 7 个测试都添加了等待逻辑
  
  **修改后的测试示例**:
  ```javascript
  test('Dashboard 页面应该加载增强版', async ({ page }) => {
    await page.goto('/dashboard');
    
    // 验证 URL
    await expect(page).toHaveURL(/\/dashboard/);
    
    // 等待 Dashboard 组件完全加载
    await page.waitForSelector('.dashboard-enhanced', { timeout: 5000 });
    
    // 验证页面标题
    const title = page.locator('h1');
    await expect(title.first()).toBeVisible();
  });
  ```

  **Must NOT do**:
  - 不要修改其他测试文件
  - 不要修改组件代码
  - 不要改变测试断言逻辑

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: `[]` (simple test fix)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential
  - **Blocks**: None
  - **Blocked By**: None

  **References**:
  - `frontend/tests/e2e/dashboard-enhanced.spec.js` - 需要修改的测试文件
  - `frontend/src/views/DashboardEnhanced.vue:2` - 组件根元素选择器 `.dashboard-enhanced`

  **Acceptance Criteria**:
  - [ ] 所有 7 个测试都添加了 `waitForSelector`
  - [ ] 等待选择器为 `.dashboard-enhanced`
  - [ ] 超时时间设置为 5000ms

  **QA Scenarios**:

  ```
  Scenario: 运行所有 E2E 测试
    Tool: Bash
    Preconditions: 后端服务运行在 localhost:5001
    Steps:
      1. cd frontend
      2. npm run test:e2e
      3. 等待测试完成
    Expected Result: 25 个测试全部通过 (25/25)
    Failure Indicators: 任何测试失败
    Evidence: .sisyphus/evidence/task-1-all-tests-pass.txt
  ```

  **Evidence to Capture**:
  - [ ] 保存测试输出到证据文件
  - [ ] 包含测试统计信息

  **Commit**: YES
  - Message: `fix(tests): add wait logic to dashboard enhanced e2e tests`
  - Files: `frontend/tests/e2e/dashboard-enhanced.spec.js`
  - Pre-commit: `npm run test:e2e`

---

## Final Verification Wave

- [x] F1. **运行所有 E2E 测试** — `npm run test:e2e` 返回 25/25 通过 ✅

---

## Commit Strategy

- **1**: `fix(tests): add wait logic to dashboard enhanced e2e tests` — dashboard-enhanced.spec.js

---

## Success Criteria

### Verification Commands
```bash
cd frontend
npm run test:e2e

# Expected output:
# Running 25 tests using 8 workers
#  25 passed (X.Xs)
```

### Final Checklist
- [ ] 所有 25 个测试通过
- [ ] 没有超时或错误
- [ ] 测试运行时间合理 (< 30 秒)
