---
name: beta-group
version: 1.0
description: Beta专属群（oc_aa8228b8af4e9067ae66fd52f25d732d）技能沉淀，支持 SLS 日志查询、飞书群管理等
category: collaboration
---

# Beta 专属群 Skills

## 群组信息

- **群ID**: oc_aa8228b8af4e9067ae66fd52f25d732d
- **绑定Agent**: main (Beta)
- **群名**: Beta专属群

---

## 目录

1. [SLS 客户运营数据上报查询](#sls-客户运营数据上报查询)
2. [飞书群-Agent 绑定管理](#飞书群-agent-绑定管理)

---

## SLS 客户运营数据上报查询

**Skill路径**: `~/.openclaw/skills/sls-tenant-report/`

### 功能说明

查询 SLS `all-log` 库中 GlobalExceptionHandlerMiddleware 记录的 operation_api 请求日志，按 tenant_id 分组统计数量。

### 查询条件

- **Logstore**: all-log
- **Project**: bi4sight-back-sg1
- **查询语句**: `class: "HuntMobi.BI4Sight.Architecture.Infrastructures.Middleware.GlobalExceptionHandlerMiddleware" and message: operation_api`
- **分组**: tenant_id
- **时间范围**: 支持当天/昨天/自定义

### 使用方式

```bash
python3 ~/.openclaw/skills/sls-tenant-report/query_tenant_report.py
```

指定时间范围：

```bash
python3 ~/.openclaw/skills/sls-tenant-report/query_tenant_report.py --from 2026-04-25 --to 2026-04-28
```

### 输出格式

| tenant_id | 日志总数 |
| --------- | -------- |

### 前置依赖

`tenant_id` 字段必须开启 `doc_value=true` 才能进行 SQL 聚合：

```json
{
  "keys": {
    "tenant_id": {
      "type": "long",
      "doc_value": true
    }
  }
}
```

**如果没有开启 doc_value，SQL 聚合将返回 null。**

### 状态说明

- ✅ 正常：返回完整分组统计
- ⚠️ 需关注：tenant_id doc_value=false，SQL 聚合失效
- 🔴 异常：SLS API 调用失败

---

## 飞书群-Agent 绑定管理

**Skill路径**: `~/.openclaw/skills/feishu-group-manager/`

### 功能说明

通过对话管理飞书群的 Agent 归属绑定。

### 触发场景

- BOSS 在飞书群中 @Bot 询问群归属
- BOSS 要求设置/修改群绑定
- 需要查询某个群由哪个 Agent 负责

### 管理命令

```bash
# 查看当前绑定
python3 ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py list

# 绑定群到Agent
python3 ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py bind <群ID> <AgentID> [群名]

# 重新分配群
python3 ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py reassign <群ID> <AgentID>

# 解除绑定
python3 ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py unbind <群ID>

# 查询群信息
python3 ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py info <群ID>
```

### Agent ID 对照表

| Agent ID                | 名称            | 主题         |
| ----------------------- | --------------- | ------------ |
| main                    | Beta 🦞         | 项目智能中心 |
| bi4sight_ops            | BI4Sight Ops 🔧 | 运维执行     |
| bi4sight_code_manager   | Code Manager 📦 | 代码管理     |
| bi4sight_product_expert | 产品专家 💡     | 产品知识     |
| bi4sight_qa             | 答疑助手 🎯     | 产品答疑     |
| bi4sight_researcher     | 调研 🔍         | 竞品分析     |
| bi4sight_knowledge_wiki | 知识库 📚       | 产品咨询     |

### 重要规则

1. 每次修改绑定后必须执行：`openclaw gateway restart`
2. BOSS 私聊固定路由到 main (Beta)，不可修改
3. 未绑定群自动落入 bi4sight_qa（答疑助手）

### 常见对话意图

| BOSS 说法          | 操作                           |
| ------------------ | ------------------------------ |
| "这个群归运维"     | bind → bi4sight_ops            |
| "这个群归产品专家" | bind → bi4sight_product_expert |
| "这个群谁在管?"    | info                           |
| "列出所有群"       | list                           |
| "换个人管这个群"   | reassign                       |

---

_Last updated: 2026-04-28_
