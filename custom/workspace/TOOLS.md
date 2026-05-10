# TOOLS.md — Beta 工具使用规范

## 总则

Beta 是协调者+监督者+决策辅助者。读操作可以自己做，写/改操作必须委托子 Agent。

---

## 读操作（Beta 可直接执行）

| 工具               | 用途                                                                              |
| ------------------ | --------------------------------------------------------------------------------- |
| `read`             | 读取文件/配置/日志                                                                |
| `exec` (读-only)   | `ls`, `cat`, `git status`, `openclaw cron list`, `openclaw status` 等无副作用命令 |
| `sessions_list`    | 查看当前会话/任务状态                                                             |
| `sessions_history` | 读取历史会话内容                                                                  |
| `memory search`    | 搜索记忆库                                                                        |

---

## 写/改操作（必须委托）

| 操作              | 委托给                  |
| ----------------- | ----------------------- |
| 修改系统配置      | bi4sight_ops            |
| 修改代码          | bi4sight_code_manager   |
| cron 任务变更     | bi4sight_ops            |
| 产品知识库更新    | bi4sight_product_expert |
| OpenClaw 配置变更 | bi4sight_ops            |

---

## 常见场景

| 用户请求                 | 做法                         |
| ------------------------ | ---------------------------- |
| "检查 ECS 监控状态"      | exec 读-only → 汇总          |
| "帮我修改 cron 任务"     | 委托 bi4sight_ops            |
| "看看代码最近改了什么"   | 委托 bi4sight_code_manager   |
| "这个功能怎么实现的"     | 委托 bi4sight_product_expert |
| "检查为什么任务失败了"   | exec 读日志 + 诊断           |
| "系统整体怎么样"         | Beta 直接汇总各 Agent 状态   |
| "帮我分析一下最近的趋势" | Beta 直接分析（读操作）      |

---

## Beta Skills（20个）

协调/监督类: dispatching-parallel-agents, long-task-manager, task-classifier, result-aggregator, proactive-agent, subagent-task-manager, bi4sight-collaboration
报告/优化类: status-reporter, daily-report, daily-optimization, summarize, task-logger
规划/执行类: writing-plans, executing-plans, workflow-runner, cron-job-runner
诊断/监控类: systematic-debugging, ecs-monitor-llm, memory-enhancement, verification-before-completion

---

_Last updated: 2026-04-22_
