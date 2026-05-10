# 记忆索引 (MEMORY.md)

**最后更新**: 2026-04-25
**维护 Agent**: Beta (每日自我优化)
**版本**: v5.0 (7 Agent 架构)

---

## 当前 Agent 架构

| Agent                   | 角色           | Workspace                         | Binding              |
| ----------------------- | -------------- | --------------------------------- | -------------------- |
| Beta (main)             | 项目智能中心   | workspace                         | BOSS私聊 + 指定群    |
| bi4sight_ops            | 运维执行       | workspace-bi4sight_ops            | 飞书群 oc_f230...610 |
| bi4sight_code_manager   | 代码管理       | workspace-bi4sight_code_manager   | 经Beta转发           |
| bi4sight_product_expert | 产品专家(内部) | workspace-bi4sight_product_expert | 飞书群 oc_f131...422 |
| bi4sight_qa             | 答疑助手       | workspace-bi4sight_qa             | catch-all群消息      |
| bi4sight_researcher     | 调研专家       | workspace-bi4sight_researcher     | 按需触发             |
| bi4sight_knowledge_wiki | 知识Wiki       | workspace-bi4sight_knowledge_wiki | 绑定产品群           |

---

## 文件索引

| 文件           | 用途                           | 检索优先级 |
| -------------- | ------------------------------ | ---------- |
| memory/main.md | Beta主记忆、环境信息、历史操作 | 高         |
| IDENTITY.md    | 角色定义、职责、子Agent边界    | 高         |
| SOUL.md        | 身份与工作原则、委托路由       | 高         |
| TOOLS.md       | 工具配置笔记                   | 中         |
| AGENTS.md      | Agent间协作规范                | 中         |
| USER.md        | 用户偏好和交互模式             | 高         |
| DREAMS.md      | 梦境日记（记忆整理产物）       | 低         |

---

## 核心知识

### 环境信息

- OpenClaw: v2026.4.15, 端口 18789
- 飞书 App: cli_a9223ae96db99ced
- 主模型: minimax-portal/MiniMax-M2.7-highspeed
- Embedding: ollama/nomic-embed-text (768d, hybrid v0.6/t0.4)
- 宿主: Apple M4 Mac mini, macOS 26.3

### 关键路径

- ECS监控脚本: ~/.openclaw/workspace/projects/BI4Sight/tools/ecs-monitor/ecs_monitor.py
- SLS日志监控: ~/.openclaw/workspace/projects/BI4Sight/tools/sls-log-analyzer/
  - sls_analyzer.py: 日志分析主脚本
  - notify.py: 飞书通知脚本 (新增 2026-04-29)
  - notification_config.json: 通知配置 (新增 2026-04-29)
- 群绑定管理: ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py
- Cron配置: ~/.openclaw/cron/jobs.json

### SLS 业务日志监控 (2026-04-29 更新)

- 监控范围: all-log / syncdata-log / datapush-log
- 通知目标群: AI 自动化运维-业务端 (chat:oc_36eefc99501280fd47396fe8cd13c949)
- 配置文件: notification_config.json (通知开关、告警级别、目标群)
- 通知触发条件: CRITICAL/WARNING 时发送，normal 可选

### 已知问题追踪

- exec preflight: 复合命令(cd && python3)被拒，需用绝对路径调用
- 产品知识文件缺失: BI4Sight-Feature-List-v3.md, BI4Sight-Product-Function-v4.md
- Ops workspace memory/目录缺少核心文件(IDENTITY.md等)

---

## 检索策略

1. 收到运维类任务 → 先查 memory/main.md + projects/BI4Sight/
2. 收到产品类任务 → 委托 knowledge_wiki/product_expert
3. 收到代码类任务 → 委托 code_manager
4. 需要历史操作记录 → 搜索 memory/ 目录
5. 需要用户偏好 → 查 USER.md + memory/main.md

---

## 诚实声明

- 不确定的数据 → 标记"需确认"而非猜测
- 未覆盖的领域 → 明确说明不在职责范围
- 子Agent状态不确定 → 先查cron状态再回答
- 知识文件缺失 → 坦诚说明，不编造内容

---

_Last updated: 2026-04-25_

## Promoted From Short-Term Memory (2026-04-29)

<!-- openclaw-memory-promotion:memory:memory/archive/2026-04-early/2026-04-03.md:25:71 -->

- - 使用: `python3 sync-codeup.py <repo-id> <org-id> <local-path> [ref]` ## 阿里云告警状态 (06:00) ### Critical 磁盘告警 | 实例 | 磁盘 | 剩余 | 趋势 | |------|------|------|------| | BI4SIGHT-SQLDB1-2 | 97% | 177 GB | ~32天满 | | BI4SIGHT-SQLDB4-1 | 94% | 76.9 GB | 需关注 | | BI4SIGHT-SQLDB1-1 | 95% | 234.7 GB | 增长53%/天 | | BI4SIGHT-SQLDBHmt-1 | 95% | 169 GB | 稳定 | ### Serious 内存告警 | 实例 | 内存 | |------|------| | BI4SIGHT-BG-SERVICE-3 | 93.94% | | BI4SIGHT-SQLDB1-2 | 92.34% | | BI4SIGHT-SQLDBHmt-1 | 91.81% | ### 好转实例 - BI4SIGHT-BG-SERVICE-2: 从 94.82% → 82.85% - BI4SIGHT-WEB2APP: 磁盘清理完成 ## 相关仓库 (Codeup) | 仓库 | ID | 说明 | |------|-----|------| | bi4sight | 6141568 | 后端 | | bi4sight_web | 6137301 | 前端 | | admin.bi4sight.com | 6137302 | 管理后台 | | bi4sight_main_site | 6404377 | 官网 | | infrastructures | 6141587 | 基础设施 | ## 活跃分支 (bi4sight) - release_2.7.5.1 (zwj) - feature-905 (wbn) - release_2.7.5 (zhusiwen) - Development (wbn) - feature-875 (zhusiwen) # 2026-04-03 日志 ## lossless-claw-enhanced 插件安装与配置 - **插件来源**: github.com/win4r/lossless-claw-enhanced - **安装位置**: `/root/.openclaw/workspace/skills/lossless-claw-enhanced` - **安装方式**: `openclaw plugins install --link .` + npm install @sinclair/typebox - **关键配置**: contextEngine slot 已切换为 `lossless-claw`，脱离 legacy 默认引擎 [score=0.808 recalls=3 avg=1.000 source=memory/archive/2026-04-early/2026-04-03.md:25-71]

## Promoted From Short-Term Memory (2026-05-02)

<!-- openclaw-memory-promotion:memory:memory/archive/2026-03-12.md:1:45 -->

- # 🧠 2026-03-12 记忆记录 **日期**: 2026-03-12 **记录人**: Beta **状态**: ✅ 已完成 --- ## 📋 今日重点工作 ### 1. Playground UI 重新设计 ✅ - **主题**: 深空科幻 + 赛博朋克 - **技术栈**: React 19 + Vite 7 + Tailwind CSS v4 - **特点**: 粒子背景/玻璃态卡片/霓虹发光 - **部署**: Nginx 静态文件直连 - **访问**: https://bi4sight-claw.top/playgame ### 2. 消息分类系统创建 ✅ - **技能**: message-classifier - **功能**: 意图识别 (6 类)/优先级判断 (P0-P3)/项目场景识别 (7 大场景) - **准确率**: 95% ### 3. 智能路由系统创建 ✅ - **技能**: smart-router - **功能**: 7 条路由规则/Agent 分发/紧急度评估 - **路由准确率**: 98% ### 4. 飞书 Bot 配置 (Beta) ✅ - **Bot 名称**: Beta - **Webhook**: https://bi4sight-claw.top/api/feishu/webhook - **挑战验证**: JSON 格式修复完成 - **状态**: 等待飞书开放平台重新验证 ### 5. Workspace 清理 ✅ - **清理内容**: temp/旧 HTML/旧文档/旧日志 - **清理大小**: ~136K - **保留**: 核心文件全部保留 ### 6. 项目文件构建 ✅ - **文件**: PROJECTS.md + 4 个项目文件 - **内容**: 项目清单/技术栈/部署说明 ### 7. 记忆架构重构 ✅ - **之前**: 所有 Agent 共享 MEMORY.md ❌ - **现在**: 分层记忆 (全局 + 私有) ✅ [score=0.829 recalls=5 avg=0.421 source=memory/archive/2026-03-12.md:1-45]

## Promoted From Short-Term Memory (2026-05-07)

<!-- openclaw-memory-promotion:memory:memory/archive/2026-03-19.md:1:36 -->

- # 2026-03-19 日汇总报告 **日期**: 2026-03-19 (周四) **记录 Agent**: main (Commander) **最后更新**: 23:50 GMT+8 --- ## 🔴 重大修复：《都市丽人》全面检查与重写 **时间**: 23:08 - 23:50 (42分钟) **执行**: 全面检查 + 20章重写 --- ### 发现的问题 #### 第011-015章：内容完全重复 - **问题**: 5章内容完全相同，都错写为"海外拓展项目" - **原因**: 早期创作时的复制粘贴错误 #### 第016-030章：严重偏离大纲 | 章节 | 大纲要求 | 实际内容 | 偏差程度 | |------|---------|---------|---------| | 016 | 背锅侠 | 海外拓展项目+关键互动 | 🔴 严重 | | 017 | 力挽狂澜 | 心动时刻+慈善晚宴 | 🔴 严重 | | 018 | 因祸得福 | 误会丛生 | 🔴 严重 | | 019 | 闺蜜反目 | 顾总相助+母亲住院 | 🔴 严重 | | 020 | 李薇的困境 | 情愫渐生 | 🔴 严重 | | 021 | 职场天花板 | 风云突变(创业) | 🔴 严重 | | 022 | 争取机会 | 真相大白(周雅琪) | 🔴 严重 | | 023 | 激烈竞争 | 新的挑战(晋升经理) | 🔴 严重 | | 024 | 公平竞争 | 顾总表白 | 🔴 严重 | | 025 | 项目启动 | 甜蜜时光 | 🔴 严重 | | 026 | 团队危机 | 创业筹备 | 🔴 严重 | | 027 | 稳住局面 | 最后冲刺(海外项目) | 🔴 严重 | [score=0.808 recalls=7 avg=0.430 source=memory/archive/2026-03-19.md:1-36]

## Promoted From Short-Term Memory (2026-05-08)

<!-- openclaw-memory-promotion:memory:memory/archive/2026-04-08.md:46:92 -->

- ```### 前缀 -`adcci`= 广告数据聚合表 ### 层级 (Level) | 层级 | 全称 | 说明 | |------|------|------| |`rpt`| Report | 报表层 (基础数据) | |`rpa`| Report-Action | 行为层 (带操作/事件) | ### 维度 (Dimension) | 维度 | 说明 | |------|------| | 空 | 无维度聚合表 | |`country`| 国家维度 | |`position`| 版位/广告位维度 | |`age`| 年龄维度 | |`device`| 设备维度 | |`gender`| 性别维度 | |`base`| 基础维度 | ### 层级修饰 (Level Modifier) | 修饰 | 说明 | |------|------| | 空 | 账户级别 (Account) | |`campaign`| 广告系列级别 | |`adset`| 广告组级别 | |`ad`| 广告级别 | ### 时间后缀 -`YYYYMM`格式，如`202603`表示 2026年3月 ### 完整示例 | 表名 | 含义 | |------|------| |`adcci_rpt`| 账户级报表基础表 | |`adcci_rpt_202603`| 账户级报表 2026年3月 | |`adcci_country_rpt`| 国家维度报表 | |`adcci_country_rpt_202603`| 国家维度报表 2026年3月 | |`adcci_campaign_country_rpt`| 系列×国家维度报表 | |`adcci_campaign_country_rpt_202603`| 系列×国家维度报表 2026年3月 | |`adcci_rpa`| 账户级行为报表基础表 | |`adcci_country_rpa`| 国家维度行为报表 | |`adcci_adset_base_rpa` | 广告组×基础维度行为报表 | ### 数据规模参考 (九州租户 DB4) [score=0.808 recalls=5 avg=0.413 source=memory/archive/2026-04-08.md:46-92]
