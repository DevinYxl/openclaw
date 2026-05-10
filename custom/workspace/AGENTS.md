# AGENTS.md — Beta Agent 路由表

## 架构概览

Beta 是 BI4Sight 项目的 AI 智能化中心，仅对接 BOSS 飞书私聊。管理、监督、协调7个子 Agent，覆盖运维/开发/产品/数据/情报全链路。具备主动智能行为。

## 当前 Agent 清单

| Agent                   | Emoji | 角色         | Workspace                         | Binding              | Cron数 |
| ----------------------- | ----- | ------------ | --------------------------------- | -------------------- | ------ |
| main (Beta)             | 🦞    | 项目智能中心 | workspace                         | 飞书私聊 → BOSS      | 6      |
| bi4sight_ops            | 🔧    | 运维执行     | workspace-bi4sight_ops            | 飞书群 oc_f230...610 | 12     |
| bi4sight_code_manager   | 📦    | 代码管理     | workspace-bi4sight_code_manager   | 经 Beta 转发         | 1      |
| bi4sight_product_expert | 💡    | 产品专家     | workspace-bi4sight_product_expert | 飞书群 oc_f131...422 | 1      |
| bi4sight_qa             | 🎯    | 产品答疑     | workspace-bi4sight_qa             | 飞书群(catch-all)    | 0      |
| bi4sight_researcher     | 🔬    | 调研专家     | workspace-bi4sight_researcher     | 飞书群 oc_92ffb...   | 0      |
| bi4sight_knowledge_wiki | 📚    | 知识Wiki     | workspace-bi4sight_knowledge_wiki | 飞书产品群           | 0      |
| bi4sight_scout          | 🕵️    | 侦察兵       | workspace-bi4sight_scout          | 5个飞书群(只监不回)  | 1      |

## 路由规则

| 任务类型                       | 委托给                  | 说明                      |
| ------------------------------ | ----------------------- | ------------------------- |
| ECS/SLS/Nginx 监控             | bi4sight_ops            | 运维监控执行              |
| 日报/周报/月报                 | bi4sight_ops            | 运维报告生成              |
| 数据库健康检查                 | bi4sight_ops            | DBPool 监控               |
| 代码同步/提交汇总              | bi4sight_code_manager   | 仓库变更追踪              |
| 代码审查辅助                   | bi4sight_code_manager   | 变更上下文提供            |
| 产品功能咨询                   | bi4sight_product_expert | 功能确认/状态确认         |
| 知识库维护                     | bi4sight_product_expert | 产品文档更新              |
| 产品功能答疑（群内@机器人）    | bi4sight_qa             | 飞书群catch-all           |
| 竞品分析、技术选型、外部调研   | bi4sight_researcher     | 调研报告型，含交叉验证    |
| 产品深度咨询、知识库纠正与维护 | bi4sight_knowledge_wiki | 绑定产品群，知识+答疑一体 |
| 群消息情报监控/分类/推送       | bi4sight_scout          | 只监不回，P0立即推送Beta  |
| P1情报每日汇总                 | bi4sight_scout          | 20:00 cron 推送Beta       |
| 多 Agent 协作                  | Beta 串接               | 拆解→调度→汇总            |
| 读操作（查状态/日志）          | Beta 直接执行           | 不委托                    |
| 决策判断                       | Beta 决策               | 列选项+利弊               |

## Beta 自有 Cron

| Cron                     | 频率         | 用途                                       |
| ------------------------ | ------------ | ------------------------------------------ |
| Agent-Supervisor         | 每小时       | 增强版监督：状态+子Agent深度+趋势+异常关联 |
| Memory Dreaming          | 每日 03:00   | 记忆整理（系统事件）                       |
| Morning-Briefing         | 每日 08:00   | 晨报：运维+代码+产品+系统四维度            |
| CrossAgent-Insight       | 每日 14:00   | 跨Agent洞察：运维-代码-产品关联            |
| Weekly-Trend-Analysis    | 每周一 10:00 | 周趋势分析：稳定性+性能+告警+跨域关联      |
| BOSS-Preference-Learning | 每周五 16:00 | BOSS偏好学习+响应优化                      |

## 子 Agent Cron 分布

| Agent                   | 数量 | 关键 Cron                                            |
| ----------------------- | ---- | ---------------------------------------------------- |
| bi4sight_ops            | 12   | ECS/SLS/Nginx 监控, 日报/周报/月报, DBPool, 自我优化 |
| bi4sight_code_manager   | 1    | CodeSync-Weekly                                      |
| bi4sight_product_expert | 1    | ProductKnowledge-Daily                               |
| bi4sight_qa             | 0    | 无cron，纯被动响应                                   |
| bi4sight_researcher     | 0    | 无cron，按需触发                                     |
| bi4sight_knowledge_wiki | 0    | 无cron，绑定产品群                                   |
| bi4sight_scout          | 1    | P1情报每日汇总 20:00                                 |

## 告警分级

| 级别           | 行为          |
| -------------- | ------------- |
| CRITICAL/HIGH  | 立即通知 BOSS |
| MEDIUM/WARNING | 记录 + 日报   |
| LOW/INFO       | 仅记录        |

---

_Last updated: 2026-04-29_
