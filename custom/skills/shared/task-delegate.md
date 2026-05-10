# Task Delegate Protocol - 任务委托协议

## 概述

Main Agent 向执行 Agent 分配任务的标准协议。

---

## 1. 任务分配格式

### 1.1 标准任务消息

```json
{
  "protocol": "task-delegate",
  "version": "1.0",
  "task_id": "PROJ-001-TASK-001",
  "type": "code_gen",
  "priority": "high|medium|low",
  "context": {
    "project": "项目名称",
    "description": "任务描述",
    "requirements": ["需求1", "需求2"],
    "input_files": ["路径1", "路径2"],
    "output_format": "markdown|json|code",
    "deadline": "2026-04-01T20:00:00+08:00"
  },
  "callback": {
    "session_key": "main__PROJ-001-TASK-001",
    "format": "result_report"
  }
}
```

### 1.2 sessionKey 命名规范

```
{agentId}__{projectId}-{taskId}
```

示例：

- `main__PROJ-001`
- `code_gen_ali__PROJ-001-TASK-001`
- `data_miner__PROJ-001-TASK-002`

---

## 2. 任务类型映射

| 任务类型             | 分配给           | 超时(s) |
| -------------------- | ---------------- | ------- |
| requirement_analysis | product_agent    | 300     |
| architecture_design  | architect_agent  | 600     |
| code_generation      | code_gen_ali     | 300     |
| code_review          | reviewer_agent   | 180     |
| data_mining          | data_miner       | 300     |
| testing              | test_runner      | 180     |
| documentation        | archivist_agent  | 120     |
| summarization        | summarizer_agent | 120     |

---

## 3. 任务状态

| 状态          | 含义             |
| ------------- | ---------------- |
| `pending`     | 已分配，等待执行 |
| `in_progress` | 执行中           |
| `completed`   | 已完成           |
| `failed`      | 失败             |
| `blocked`     | 阻塞             |

---

## 4. 委托流程

```
Main Agent                          执行 Agent
    │                                    │
    │──── sessions_spawn ────────────────>│
    │     task_id: PROJ-001-TASK-001      │
    │     sessionKey: code_gen_ali__...    │
    │                                    │
    │<─── sessions_send (状态更新) ───────│
    │     status: in_progress             │
    │                                    │
    │<─── sessions_send (结果汇报) ───────│
    │     status: completed              │
    │     output: {...}                  │
```

---

## 5. 使用示例

### 5.1 Main Agent 分配任务

```javascript
sessions_spawn(
  (task = "请完成用户模块的代码生成，需求详见 projects/PROJ-001/specs/user-module.md"),
  (agentId = "code_gen_ali"),
  (sessionKey = "code_gen_ali__PROJ-001-TASK-001"),
  (runtime = "subagent"),
);
```

### 5.2 执行 Agent 回报状态

```javascript
sessions_send(
  (sessionKey = "main__PROJ-001-TASK-001"),
  (message = JSON.stringify({
    task_id: "PROJ-001-TASK-001",
    status: "completed",
    output: {
      files: ["projects/PROJ-001/src/user.js"],
      summary: "用户模块代码生成完成",
    },
  })),
);
```

---

## 6. 错误处理

| 错误类型   | 处理方式                             |
| ---------- | ------------------------------------ |
| 超时       | 自动重试 1 次，仍失败则回报 `failed` |
| 执行失败   | 详细记录错误信息，回报 `failed`      |
| 依赖未完成 | 回报 `blocked`，说明依赖任务 ID      |

---

_Last updated: 2026-04-01_
