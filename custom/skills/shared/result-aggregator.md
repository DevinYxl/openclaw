# Result Aggregator Protocol - 结果聚合协议

## 概述

执行 Agent 向 Main Agent 汇报结果的标准协议。

---

## 1. 结果汇报格式

### 1.1 标准结果消息

```json
{
  "protocol": "result_report",
  "version": "1.0",
  "task_id": "PROJ-001-TASK-001",
  "agent_id": "code_gen_ali",
  "status": "completed|failed|blocked",
  "timestamp": "2026-04-01T20:00:00+08:00",
  "output": {
    "files": ["文件路径列表"],
    "summary": "一句话结果总结",
    "details": "详细说明（可选）"
  },
  "next_steps": ["建议的后续任务列表"],
  "issues": [
    {
      "type": "error|warning|info",
      "description": "问题描述",
      "severity": "high|medium|low"
    }
  ],
  "metrics": {
    "duration_seconds": 120,
    "tokens_used": 5000
  }
}
```

---

## 2. 状态码定义

| 状态码                    | 含义         | 需要人工介入 |
| ------------------------- | ------------ | ------------ |
| `completed`               | 成功完成     | 否           |
| `completed_with_warnings` | 完成但有警告 | 是           |
| `failed`                  | 执行失败     | 是           |
| `blocked`                 | 因依赖阻塞   | 是           |
| `cancelled`               | 已取消       | 否           |

---

## 3. 聚合流程

```
┌─────────────────────────────────────────────┐
│               Main Agent                     │
│  1. 等待所有依赖任务完成                       │
│  2. 收集各 Agent 结果                         │
│  3. 检查失败/阻塞任务                         │
│  4. 汇总成功结果                             │
│  5. 决定下一步行动                           │
└─────────────────────────────────────────────┘
```

---

## 4. 结果汇总模板

```markdown
# 项目 {project_name} - 任务汇总

## 执行时间

{start_time} ~ {end_time}

## 任务完成情况

| 任务ID   | Agent          | 状态 | 输出                       |
| -------- | -------------- | ---- | -------------------------- |
| TASK-001 | code_gen_ali   | ✅   | src/a.py                   |
| TASK-002 | data_miner     | ✅   | data/b.csv                 |
| TASK-003 | reviewer_agent | ⚠️   | reports/review.md (有警告) |

## 总体状态

{PASSED|FAILED|PARTIAL}

## 问题清单

- [ ] TASK-003: 性能警告 - 建议优化

## 下一步行动

1. 修复 TASK-003 的警告
2. 执行集成测试
3. 准备部署
```

---

## 5. 失败处理

### 5.1 失败结果格式

```json
{
  "task_id": "PROJ-001-TASK-001",
  "status": "failed",
  "output": {},
  "issues": [
    {
      "type": "error",
      "description": "编译失败：缺少依赖",
      "severity": "high",
      "details": "Error: Cannot find module 'lodash'"
    }
  ],
  "attempts": [
    { "time": "2026-04-01T19:00:00+08:00", "error": "..." },
    { "time": "2026-04-01T19:05:00+08:00", "error": "..." }
  ]
}
```

### 5.2 失败处理策略

| 失败类型           | 处理方式                 |
| ------------------ | ------------------------ |
| 临时错误（网络等） | 自动重试 3 次，间隔 30s  |
| 永久错误（代码等） | 记录并上报，等待人工处理 |
| 超时               | 重试 1 次，仍超时则上报  |

---

## 6. 回调机制

执行 Agent 完成后，通过 `sessions_send` 回调 Main Agent：

```javascript
sessions_send((sessionKey = "main__PROJ-001-TASK-001"), (message = JSON.stringify(result_report)));
```

Main Agent 的 callback session 格式：

```
main__{projectId}-{taskId}
```

---

_Last updated: 2026-04-01_
