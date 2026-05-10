# Project Template - 项目模板定义

## 概述

标准化的项目目录结构，所有 Multi-Agent 项目应遵循此模板。

---

## 1. 标准目录结构

```
projects/
└── {project-id}/
    │
    ├── .project/                  # 项目元数据
    │   ├── config.json           # 项目配置
    │   ├── AGENTS.md             # 项目 Agent 定义
    │   └── context.md            # 项目上下文
    │
    ├── specs/                     # 需求规格
    │   ├── README.md             # 规格索引
    │   ├── requirements.md       # 需求文档
    │   └── api-spec.md           # API 规格（如有）
    │
    ├── src/                       # 源代码
    │   ├── module-a/
    │   └── module-b/
    │
    ├── tests/                     # 测试文件
    │   ├── unit/
    │   └── integration/
    │
    ├── docs/                      # 文档
    │   ├── architecture.md       # 架构文档
    │   └── guides/               # 使用指南
    │
    ├── reports/                   # 生成报告
    │   ├── daily/
    │   └── archive/
    │
    ├── memory/                    # 项目记忆
    │   ├── task_state.md         # 任务状态
    │   ├── decisions.md           # 关键决策
    │   └── notes.md              # 会议纪要/笔记
    │
    ├── output/                    # 任务输出
    │   └── {task-id}/
    │
    └── archive/                   # 归档
        └── {YYYY-MM}/
```

---

## 2. 必需文件

### 2.1 项目配置文件 (.project/config.json)

```json
{
  "id": "PROJ-001",
  "name": "项目名称",
  "description": "项目简述",
  "created_at": "2026-04-01T00:00:00+08:00",
  "owner": "main",
  "agents": ["code_gen_ali", "data_miner", "reviewer_agent"],
  "status": "active",
  "phase": "development"
}
```

### 2.2 项目 Agent 定义 (.project/AGENTS.md)

```markdown
# 项目 Agent 配置

## 参与 Agent

| Agent          | 角色   | 职责               |
| -------------- | ------ | ------------------ |
| main           | 调度者 | 任务分解、结果汇总 |
| code_gen_ali   | 开发者 | 代码生成           |
| reviewer_agent | 审查者 | 代码审查           |

## 任务分配规则

- code_gen: TASK-type = code_generation
- data_miner: TASK-type = data_mining
- reviewer_agent: TASK-type = review

## 特殊约定

- 输出格式: markdown
- 代码风格: eslint-standard
- ...
```

### 2.3 任务状态文件 (memory/task_state.md)

```markdown
# 任务状态

## 任务列表

| 任务ID   | 类型     | Agent          | 状态 | 依赖     | 输出              |
| -------- | -------- | -------------- | ---- | -------- | ----------------- |
| TASK-001 | code_gen | code_gen_ali   | ✅   | -        | src/a.py          |
| TASK-002 | review   | reviewer_agent | 🔄   | TASK-001 | reports/review.md |

## 进度

- 总体进度: 50%
- 已完成: 1
- 进行中: 1
- 待开始: 3

## 阻塞

- 无

## 更新记录

- 2026-04-01 19:00: TASK-001 完成
- 2026-04-01 19:30: TASK-002 开始
```

---

## 3. 项目初始化流程

### 3.1 Main Agent 创建项目

```bash
# 1. 创建目录结构
mkdir -p projects/{project-id}/.project
mkdir -p projects/{project-id}/specs
mkdir -p projects/{project-id}/src
mkdir -p projects/{project-id}/tests
mkdir -p projects/{project-id}/docs
mkdir -p projects/{project-id}/reports
mkdir -p projects/{project-id}/memory
mkdir -p projects/{project-id}/output
mkdir -p projects/{project-id}/archive

# 2. 创建配置文件
# 使用下方模板创建 .project/config.json
# 创建 specs/README.md
# 创建 memory/task_state.md
```

### 3.2 初始化文件内容

**specs/README.md**:

```markdown
# 需求规格

## 目录

- [requirements.md](./requirements.md) - 核心需求

## 变更记录

| 日期       | 变更     | 负责人 |
| ---------- | -------- | ------ |
| 2026-04-01 | 初始版本 | main   |
```

**memory/task_state.md**:

```markdown
# 任务状态

## 初始化

- 创建时间: 2026-04-01
- 创建者: main
- 状态: active

## 任务列表

（待填充）
```

---

## 4. 项目生命周期

```
创建 → 规划 → 执行 → 收尾 → 归档
  │       │       │       │       │
  └── 需求 ────────────────────┘       │
       └── 开发 ──────────────┘         │
            └── 测试 ────────┘         │
                 └── 部署 ────┘       │
                      └── 维护 ──┘     │
                           └── 归档   │
```

---

## 5. 命名规范

| 类型       | 规范                  | 示例                     |
| ---------- | --------------------- | ------------------------ |
| 项目 ID    | PROJ-{NNN}            | PROJ-001                 |
| 任务 ID    | TASK-{NNN}            | TASK-001                 |
| Agent ID   | {role}\_{name}        | code_gen_ali             |
| 目录       | kebab-case            | user-auth-module         |
| 文件       | kebab-case            | user-auth.md             |
| sessionKey | {agentId}\_\_{taskId} | code_gen_ali\_\_TASK-001 |

---

## 6. 现有项目模板参考

已存在：`projects/.template/`

结构：

```
.template/
├── AGENTS.md           # 模板 Agent 配置
├── memory/
│   └── .gitkeep
└── SESSION-STATE.md
```

---

_Last updated: 2026-04-01_
