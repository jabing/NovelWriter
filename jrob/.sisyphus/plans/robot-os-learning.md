# jrob - 机器人OS学习项目计划

## TL;DR

> **Quick Summary**: 从零构建一个学习型机器人仿真平台，通过渐进式实践掌握物理引擎、机器人建模和控制系统核心原理
> 
> **Deliverables**: 
> - 可运行的2D/3D机器人仿真器
> - URDF模型解析器
> - 基础控制系统实现
> - 人形/四足机器人模型示例
> 
> **Estimated Effort**: Large (14-22周)
> **Parallel Execution**: YES - 多模块可并行开发
> **Critical Path**: 物理引擎 → URDF解析 → 控制系统 → 集成

---

## Context

### Original Request
用户希望学习创建自己的机器人OS，需要一个开源仿真平台作为参考，目标是理解机器人OS的核心架构和原理。

### Interview Summary
**Key Discussions**:
- 经验水平：新手入门，C++背景
- 目标机器人：人形/四足机器人（高复杂度）
- 学习重点：全面基础（物理引擎、URDF、控制系统）
- 架构选择：独立架构，不依赖ROS
- 学习方式：边学边实践

**Research Findings**:
- Box2D 是学习物理引擎的最佳起点（API简单、教程丰富）
- URDF 是标准的机器人描述格式（ROS生态）
- MuJoCo 展示了高质量物理仿真的设计模式
- 从2D到3D是合理的学习路径

### Key Resources Discovered
- **Physics**: Box2D (iforce2d.net/b2dtut), Bullet Physics
- **Formats**: URDF (ROS Wiki), SDF (SDFormat.org)
- **Examples**: Bots2D (github.com/artfulbytes/bots2d), PythonRobotics
- **Books**: "Modern Robotics" (Lynch & Park, free online)

---

## Work Objectives

### Core Objective
构建一个学习型机器人仿真平台，涵盖物理引擎、机器人建模、控制系统三大核心模块，最终能够仿真人形/四足机器人。

### Concrete Deliverables
- `jrob/core/physics/` - 物理引擎模块 (Box2D封装 → Bullet封装)
- `jrob/core/model/` - URDF解析器和机器人模型
- `jrob/core/control/` - 控制系统 (PID, 轨迹跟踪)
- `jrob/visualization/` - 简单可视化 (OpenGL/SFML)
- `jrob/examples/` - 示例机器人 (倒立摆 → 机械臂 → 四足)

### Definition of Done
- [ ] 可以加载URDF文件并在仿真中显示机器人
- [ ] 机器人可以响应控制指令并稳定运动
- [ ] 物理仿真结果合理（符合基本物理定律）
- [ ] 代码结构清晰，模块化程度高

### Must Have
- 物理引擎核心功能（刚体、碰撞、约束）
- URDF模型加载
- 基础PID控制
- 简单可视化

### Must NOT Have (Guardrails)
- 不要过度工程化（保持简单，学习优先）
- 不要过早优化（先跑起来，再优化）
- 不要引入不必要的依赖（最小化第三方库）
- 不要追求ROS兼容性（独立架构）
- 不要一开始就做复杂的人形机器人（从简单模型开始）

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO
- **Automated tests**: YES (TDD - 测试驱动学习)
- **Framework**: Catch2 (C++测试框架)
- **TDD Workflow**: 每个模块先写测试，再实现

### QA Policy
每个任务包含 Agent-Executed QA Scenarios：
- **物理引擎**: 运行仿真，验证物理行为（碰撞、重力）
- **URDF解析**: 加载模型，验证解析结果
- **控制系统**: 发送指令，验证机器人响应

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately — 项目骨架 + 2D基础):
├── Task 1: 项目结构和构建系统 [quick]
├── Task 2: 测试框架集成 (Catch2) [quick]
├── Task 3: Box2D集成和基础封装 [quick]
├── Task 4: 简单2D粒子仿真示例 [quick]
└── Task 5: 2D刚体动力学示例 [quick]

Wave 2 (After Wave 1 — URDF解析 + 建模):
├── Task 6: XML解析器集成 (tinyxml2) [quick]
├── Task 7: URDF数据结构定义 [quick]
├── Task 8: URDF解析器实现 [deep]
├── Task 9: 机器人模型类 (Link, Joint) [quick]
└── Task 10: 正向运动学计算 [deep]

Wave 3 (After Wave 2 — 2D机器人控制):
├── Task 11: 差分驱动机器人模型 [quick]
├── Task 12: 轮式编码器传感器模拟 [quick]
├── Task 13: PID控制器实现 [quick]
├── Task 14: 轨迹跟踪控制器 [deep]
└── Task 15: 2D可视化 (SFML/OpenGL) [visual-engineering]

Wave 4 (After Wave 3 — 3D迁移):
├── Task 16: Bullet物理引擎集成 [quick]
├── Task 17: 3D刚体和碰撞 [deep]
├── Task 18: 3D正向运动学 [deep]
├── Task 19: 3D可视化基础 [visual-engineering]
└── Task 20: URDF 3D几何支持 [deep]

Wave 5 (After Wave 4 — 复杂机器人):
├── Task 21: 多关节机械臂模型 [deep]
├── Task 22: 四足机器人模型 [deep]
├── Task 23: 平衡控制器 [deep]
├── Task 24: 步态规划基础 [deep]
└── Task 25: 完整仿真演示 [deep]

Wave FINAL (验证 + 文档):
├── Task F1: 集成测试 [deep]
├── Task F2: 文档和示例 [writing]
├── Task F3: 代码审查和优化 [unspecified-high]
└── Task F4: 学习总结 [writing]
```

### Dependency Matrix

| Tasks | Depends On | Blocks |
|-------|------------|--------|
| 1-5 | — | 6-15 |
| 6-10 | 1, 2, 3 | 11-20 |
| 11-15 | 3, 8, 9 | 16-25 |
| 16-20 | 4, 5, 10 | 21-25 |
| 21-25 | 16, 17, 18 | F1-F4 |

### Agent Dispatch Summary
- **Wave 1**: 5 tasks → `quick` (项目搭建)
- **Wave 2**: 5 tasks → 3 `quick` + 2 `deep` (核心解析)
- **Wave 3**: 5 tasks → 3 `quick` + 1 `deep` + 1 `visual-engineering` (控制)
- **Wave 4**: 5 tasks → 1 `quick` + 3 `deep` + 1 `visual-engineering` (3D)
- **Wave 5**: 5 tasks → 5 `deep` (复杂机器人)
- **FINAL**: 4 tasks → 1 `deep` + 2 `writing` + 1 `unspecified-high`

---

## TODOs

### Wave 1: 项目骨架 + 2D基础

- [ ] 1. 项目结构和构建系统

  **What to do**:
  - 创建 C++ 项目结构 (CMake)
  - 配置构建系统 (CMakeLists.txt)
  - 设置目录结构: `src/`, `include/`, `tests/`, `examples/`
  - 初始化 Git 仓库

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO (其他任务依赖此任务)
  - **Blocks**: 所有其他任务

  **Acceptance Criteria**:
  - [ ] CMakeLists.txt 创建完成
  - [ ] 目录结构正确
  - [ ] `cmake -B build && cmake --build build` 成功
  - [ ] Git 初始化完成

  **QA Scenarios**:
  ```
  Scenario: 构建系统验证
    Tool: Bash
    Steps:
      1. cmake -B build
      2. cmake --build build
    Expected Result: 构建成功，无错误
    Evidence: .sisyphus/evidence/task-01-build.log
  ```

  **Commit**: YES
  - Message: `chore: initialize project structure`

- [ ] 2. 测试框架集成 (Catch2)

  **What to do**:
  - 添加 Catch2 作为测试依赖
  - 创建基础测试文件 `tests/main_test.cpp`
  - 配置 CMake 测试目标

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 3-5)
  - **Blocked By**: Task 1

  **Acceptance Criteria**:
  - [ ] Catch2 集成完成
  - [ ] 测试框架可运行
  - [ ] 至少一个示例测试通过

  **QA Scenarios**:
  ```
  Scenario: 测试框架验证
    Tool: Bash
    Steps:
      1. cmake --build build
      2. ./build/bin/jrob_tests
    Expected Result: 测试运行成功
    Evidence: .sisyphus/evidence/task-02-tests.log
  ```

  **Commit**: YES
  - Message: `feat(test): add Catch2 test framework`

- [ ] 3. Box2D集成和基础封装

  **What to do**:
  - 添加 Box2D 作为依赖 (FetchContent 或 vcpkg)
  - 创建 `src/physics/world2d.cpp` 封装 Box2D 世界
  - 创建 `include/jrob/physics/world2d.hpp` 头文件
  - 实现基础物理世界类

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2, 4, 5)
  - **Blocked By**: Task 1

  **References**:
  - Box2D 官方文档: https://box2d.org/documentation/
  - Box2D 教程: https://www.iforce2d.net/b2dtut/

  **Acceptance Criteria**:
  - [ ] Box2D 库成功链接
  - [ ] World2D 类可创建物理世界
  - [ ] 基础单元测试通过

  **QA Scenarios**:
  ```
  Scenario: Box2D 集成验证
    Tool: Bash
    Steps:
      1. 运行 Box2D 相关测试
      2. 创建简单物理世界并步进
    Expected Result: 物理世界创建成功，步进正常
    Evidence: .sisyphus/evidence/task-03-box2d.log
  ```

  **Commit**: YES
  - Message: `feat(physics): add Box2D integration`

- [ ] 4. 简单2D粒子仿真示例

  **What to do**:
  - 实现 Verlet 积分粒子系统
  - 创建 `examples/particle_sim.cpp`
  - 演示重力、碰撞基本效果

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2, 3, 5)
  - **Blocked By**: Task 1, Task 3

  **References**:
  - Verlet 积分教程: https://maurycyz.com/tutorials/a_super_simple_physics_engine

  **Acceptance Criteria**:
  - [ ] 粒子系统可运行
  - [ ] 粒子受重力影响
  - [ ] 基础碰撞检测工作

  **QA Scenarios**:
  ```
  Scenario: 粒子仿真验证
    Tool: Bash
    Steps:
      1. 运行粒子仿真示例
      2. 验证粒子位置更新正确
    Expected Result: 粒子位置按物理规律更新
    Evidence: .sisyphus/evidence/task-04-particles.log
  ```

  **Commit**: YES
  - Message: `feat(example): add 2D particle simulation`

- [ ] 5. 2D刚体动力学示例

  **What to do**:
  - 使用 Box2D 创建刚体
  - 实现简单的碰撞检测
  - 创建 `examples/rigid_body_sim.cpp`

  **Recommended Agent Profile**:
  - **Category**: `quick`
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 2, 3, 4)
  - **Blocked By**: Task 1, Task 3

  **Acceptance Criteria**:
  - [ ] 刚体创建成功
  - [ ] 碰撞检测工作
  - [ ] 物理响应正确

  **QA Scenarios**:
  ```
  Scenario: 刚体动力学验证
    Tool: Bash
    Steps:
      1. 运行刚体仿真
      2. 验证碰撞响应
    Expected Result: 刚体碰撞后正确反弹
    Evidence: .sisyphus/evidence/task-05-rigidbody.log
  ```

  **Commit**: YES
  - Message: `feat(example): add 2D rigid body dynamics`

### Wave 2: URDF解析 + 建模

- [ ] 6. XML解析器集成 (tinyxml2)

  **What to do**:
  - 添加 tinyxml2 依赖
  - 创建 XML 解析工具类
  - 编写基础解析测试

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 7)
  - **Blocked By**: Task 1

  **Commit**: YES
  - Message: `feat(xml): add tinyxml2 integration`

- [ ] 7. URDF数据结构定义

  **What to do**:
  - 定义 Link, Joint, Robot 数据结构
  - 创建 `include/jrob/model/types.hpp`
  - 添加单元测试

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 6)
  - **Blocked By**: Task 1

  **Commit**: YES
  - Message: `feat(model): define URDF data structures`

- [ ] 8. URDF解析器实现

  **What to do**:
  - 实现 URDF XML 解析
  - 解析 link, joint 元素
  - 处理 inertia, visual, collision 属性
  - 创建 `src/model/urdf_parser.cpp`

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Parallelization**:
  - **Blocked By**: Task 6, Task 7

  **References**:
  - URDF 规范: https://wiki.ros.org/urdf/XML

  **Acceptance Criteria**:
  - [ ] 可解析简单 URDF 文件
  - [ ] Link 和 Joint 正确解析
  - [ ] 错误处理完善

  **Commit**: YES
  - Message: `feat(model): implement URDF parser`

- [ ] 9. 机器人模型类 (Link, Joint)

  **What to do**:
  - 实现机器人模型类
  - 支持模型树结构
  - 添加模型验证

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Commit**: YES
  - Message: `feat(model): add RobotModel class`

- [ ] 10. 正向运动学计算

  **What to do**:
  - 实现正向运动学 (FK) 算法
  - 支持多关节链
  - 添加测试用例

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **References**:
  - Modern Robotics 书籍

  **Commit**: YES
  - Message: `feat(kinematics): implement forward kinematics`

### Wave 3: 2D机器人控制

- [ ] 11. 差分驱动机器人模型

  **What to do**:
  - 创建差分驱动机器人类
  - 实现运动学模型
  - 创建示例 URDF

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Commit**: YES
  - Message: `feat(robot): add differential drive model`

- [ ] 12. 轮式编码器传感器模拟

  **What to do**:
  - 实现编码器传感器类
  - 计算轮子转数
  - 生成里程计数据

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Commit**: YES
  - Message: `feat(sensor): add wheel encoder simulation`

- [ ] 13. PID控制器实现

  **What to do**:
  - 实现通用 PID 控制器类
  - 支持位置、速度控制
  - 添加抗积分饱和

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Commit**: YES
  - Message: `feat(control): implement PID controller`

- [ ] 14. 轨迹跟踪控制器

  **What to do**:
  - 实现轨迹跟踪算法
  - 支持 Pure Pursuit
  - 添加测试场景

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **References**:
  - PythonRobotics: https://github.com/AtsushiSakai/PythonRobotics

  **Commit**: YES
  - Message: `feat(control): add trajectory tracking`

- [ ] 15. 2D可视化 (SFML/OpenGL)

  **What to do**:
  - 集成 SFML 或 OpenGL
  - 实现基础渲染
  - 支持调试绘制

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
  - **Skills**: [`frontend-design`]

  **Commit**: YES
  - Message: `feat(viz): add 2D visualization`

### Wave 4: 3D迁移

- [ ] 16. Bullet物理引擎集成

  **What to do**:
  - 添加 Bullet Physics 依赖
  - 创建 3D 物理世界封装
  - 实现基础接口

  **Recommended Agent Profile**:
  - **Category**: `quick`

  **Commit**: YES
  - Message: `feat(physics): add Bullet integration`

- [ ] 17. 3D刚体和碰撞

  **What to do**:
  - 实现 3D 刚体创建
  - 支持基础碰撞形状
  - 添加约束系统

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(physics): add 3D rigid body dynamics`

- [ ] 18. 3D正向运动学

  **What to do**:
  - 扩展 FK 到 3D
  - 支持 SO(3) 旋转
  - 添加 SE(3) 变换

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(kinematics): add 3D forward kinematics`

- [ ] 19. 3D可视化基础

  **What to do**:
  - 实现基础 3D 渲染
  - 支持相机控制
  - 添加简单光照

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`

  **Commit**: YES
  - Message: `feat(viz): add 3D visualization`

- [ ] 20. URDF 3D几何支持

  **What to do**:
  - 扩展 URDF 解析支持 3D
  - 支持网格加载
  - 添加材质系统

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(model): add URDF 3D geometry support`

### Wave 5: 复杂机器人

- [ ] 21. 多关节机械臂模型

  **What to do**:
  - 创建 6-DOF 机械臂 URDF
  - 实现关节控制
  - 添加工作空间可视化

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(robot): add 6-DOF arm model`

- [ ] 22. 四足机器人模型

  **What to do**:
  - 创建四足机器人 URDF
  - 实现 12 自由度模型
  - 添加腿部分组

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(robot): add quadruped model`

- [ ] 23. 平衡控制器

  **What to do**:
  - 实现姿态平衡控制
  - 支持质心控制
  - 添加稳定器

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(control): add balance controller`

- [ ] 24. 步态规划基础

  **What to do**:
  - 实现基础步态生成
  - 支持小跑步态
  - 添加足端轨迹

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Commit**: YES
  - Message: `feat(control): add gait planning`

- [ ] 25. 完整仿真演示

  **What to do**:
  - 集成所有模块
  - 创建四足行走演示
  - 添加用户交互

  **Recommended Agent Profile**:
  - **Category**: `deep`

  **Acceptance Criteria**:
  - [ ] 四足机器人可站立
  - [ ] 可执行简单步态
  - [ ] 仿真稳定运行

  **Commit**: YES
  - Message: `feat(demo): add quadruped simulation demo`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE.

- [ ] F1. **集成测试** — `deep`
  运行所有示例，验证每个模块功能正常。检查物理仿真合理性。

- [ ] F2. **文档和示例** — `writing`
  编写README、API文档、示例代码。确保新用户可以快速上手。

- [ ] F3. **代码审查和优化** — `unspecified-high`
  检查代码质量、内存管理、性能瓶颈。运行静态分析工具。

- [ ] F4. **学习总结** — `writing`
  总结学习过程中的关键知识点、踩坑经验、改进方向。

---

## Commit Strategy

- **每个Task完成后提交**
- 格式: `feat(module): description`
- 示例: `feat(physics): add Box2D integration`

---

## Success Criteria

### Verification Commands
```bash
# 构建项目
cmake -B build && cmake --build build

# 运行测试
./build/bin/jrob_tests

# 运行示例
./build/bin/example_2d_robot
./build/bin/example_quadruped
```

### Final Checklist
- [ ] 所有Must Have功能已实现
- [ ] 所有Must NOT Have约束已遵守
- [ ] 至少3个机器人示例可运行
- [ ] 测试覆盖率 > 60%
- [ ] 文档完整