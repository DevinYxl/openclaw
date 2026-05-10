# BI4SIGHT Collaboration Skill

## 概述

BI4SIGHT 项目专用协作技能，定义标准化的任务委托、结果汇报和记忆同步流程。

## 适用项目

- 项目：BI4Sight
- 路径：`~/.openclaw/workspace/projects/bi4sight/`
- 架构：DDD + CQRS + .NET 6/7/8

## 任务委托协议

### 标准任务格式

```json
{
  "task_id": "BI4S-{module}-{number}",
  "type": "code_development|code_review|data_analysis|documentation",
  "module": "AdManage|Platform|Statistics|...",
  "context": {
    "project": "bi4sight",
    "requirements": "需求描述",
    "input_files": ["参考文件路径"],
    "output_format": "代码/Markdown"
  },
  "callback": {
    "session_key": "main__bi4sight-{task_id}"
  }
}
```

### Agent 分配规则

| 任务类型         | Agent           | 超时 |
| ---------------- | --------------- | ---- |
| code_development | code_gen_ali    | 300s |
| code_review      | reviewer_agent  | 180s |
| data_analysis    | data_miner      | 300s |
| documentation    | archivist_agent | 120s |

## 结果汇报格式

```json
{
  "task_id": "BI4S-AD-001",
  "status": "completed|failed|blocked",
  "output": {
    "files": ["输出文件列表"],
    "summary": "一句话总结"
  },
  "issues": [
    {
      "type": "error|warning",
      "description": "问题描述",
      "severity": "high|medium|low"
    }
  ]
}
```

## 协作流程

```
1. main 接收任务
         ↓
2. main 分配任务
   sessions_spawn(
     task="...",
     agentId="code_gen_ali",
     sessionKey="code_gen_ali__bi4sight-{task_id}"
   )
         ↓
3. 执行 Agent 获取文件锁
   读取 .project/task_state.md
   添加锁记录
         ↓
4. 执行 Agent 完成工作
         ↓
5. 执行 Agent 释放锁
   更新 .project/task_state.md
   sessions_send(callback, result)
         ↓
6. main 汇总结果
```

## 文件锁规则

1. 工作前必须获取文件锁
2. 被锁文件其他 Agent 不得写入
3. 任务完成后必须释放锁
4. 超时自动释放锁

## 记忆同步

- 项目记忆：`projects/bi4sight/memory/`
- Agent 记忆：`memory/agents/{agentId}.md`
- 任务状态：`.project/task_state.md`

---

_Last updated: 2026-04-01_
