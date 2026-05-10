# Memory Sync Protocol - 记忆同步协议

## 概述

Multi-Agent 环境下，Agent 之间同步上下文和记忆的标准协议。

---

## 1. 记忆文件结构

```
memory/
├── agents/                    # Agent 专属记忆
│   ├── {agentId}.md         # Agent 自身记忆
│   └── ...
├── projects/                  # 项目专属记忆
│   └── {projectId}/
│       ├── context.md        # 项目上下文
│       ├── task_state.md     # 任务状态
│       └── decisions.md       # 关键决策
└── global/                    # 全局共享记忆
    └── shared_context.md     # 跨项目共享信息
```

---

## 2. Agent 记忆文件格式

```markdown
# {AgentId} 记忆

## 身份

- Agent: {agentId}
- 角色: {role}
- 专长: {skills}

## 当前任务

- 任务ID: TASK-001
- 项目: PROJ-001
- 进度: 50%
- 状态: in_progress

## 项目上下文

- 项目名称: 示例项目
- 当前阶段: 开发
- 已知约束: ...

## 最近操作

- 2026-04-01 19:00: 完成模块A代码生成
- 2026-04-01 19:30: 开始模块B开发

## 待处理事项

- [ ] 等待 reviewer_agent 完成代码审查
- [ ] 准备集成测试

## 约定与规范

- 输出目录: projects/{project}/src/
- 代码风格: ESLint standard
- 文档格式: Markdown
```

---

## 3. 上下文传递格式

### 3.1 任务上下文

```json
{
  "project": {
    "id": "PROJ-001",
    "name": "示例项目",
    "phase": "development",
    "context_files": ["specs/requirements.md"]
  },
  "task": {
    "id": "TASK-001",
    "type": "code_generation",
    "goal": "生成用户模块代码",
    "input": ["specs/user-module.md"],
    "output_dir": "projects/PROJ-001/src"
  },
  "constraints": {
    "style": "eslint-standard",
    "naming": "camelCase",
    "max_lines_per_file": 500
  },
  "dependencies": {
    "completed": ["TASK-000"],
    "blocked": []
  }
}
```

### 3.2 跨 Agent 上下文继承

当执行 Agent 启动时，Main Agent 应传递：

1. 项目上下文（project context）
2. 任务具体要求（task requirements）
3. 已有的决策和规范（decisions & conventions）

---

## 4. 同步时机

| 时机     | 操作                 | 执行者          |
| -------- | -------------------- | --------------- |
| 任务开始 | 读取项目上下文       | 执行 Agent      |
| 任务完成 | 更新 agent 记忆      | 执行 Agent      |
| 任务完成 | 更新 task_state      | Main Agent      |
| 每日     | 汇总记忆到 MEMORY.md | Main Agent      |
| 项目结束 | 归档项目记忆         | archivist_agent |

---

## 5. 冲突处理

### 5.1 同一文件并发写入

**规则**：使用文件锁或时间戳区分

- 使用 `原子写入`（write 工具保证）
- 文件名添加时间戳：`task_state_20260401_1900.md`

### 5.2 上下文不一致

**规则**：以 Main Agent 的 task_state.md 为准

- 执行 Agent 发现冲突时，回报 Main Agent
- Main Agent 裁决后更新上下文

---

## 6. 记忆读取优先级

```
1. 当前任务相关（task_state.md）
2. 项目上下文（projects/{id}/context.md）
3. Agent 自身记忆（memory/agents/{agentId}.md）
4. 全局记忆（MEMORY.md）
5. 今日/昨日记忆（memory/YYYY-MM-DD.md）
```

---

## 7. 使用示例

### 7.1 Main Agent 传递上下文

```javascript
// 在 sessions_spawn 前准备
const context = {
  project: loadProjectContext("PROJ-001"),
  task: loadTaskRequirements("TASK-001"),
  conventions: loadConventions(),
};

// 在 task 参数中传递
sessions_spawn(
  (task = `项目: ${context.project.name}
        任务: ${context.task.goal}
        详细需求: ${context.task.requirements}`),
  (agentId = "code_gen_ali"),
  (sessionKey = "code_gen_ali__PROJ-001-TASK-001"),
);
```

### 7.2 执行 Agent 更新记忆

```markdown
<!-- 任务完成后更新 memory/agents/code_gen_ali.md -->

## 当前任务

- 任务ID: TASK-001 (已完成)
- 项目: PROJ-001
- 状态: completed
- 输出: projects/PROJ-001/src/user.js

## 最近操作

- 2026-04-01 20:00: 完成用户模块代码生成
```

---

_Last updated: 2026-04-01_
