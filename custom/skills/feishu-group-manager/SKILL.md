---
name: feishu-group-manager
version: 1.0
description: 飞书群-Agent 绑定管理，支持通过对话设置群归属
category: devops
---

# 飞书群-Agent 绑定管理

## 触发条件

- BOSS 在飞书群中 @Bot 询问群归属或要求设置/修改群绑定
- BOSS 私聊要求查看或管理群绑定
- 需要查询某个群由哪个 Agent 负责

## 管理脚本

路径: `~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py`

### 命令

| 命令                           | 用途           | 示例                                                       |
| ------------------------------ | -------------- | ---------------------------------------------------------- |
| `list`                         | 列出所有群绑定 | `python3 group_manager.py list`                            |
| `agents`                       | 列出所有Agent  | `python3 group_manager.py agents`                          |
| `bind <群ID> <AgentID> [群名]` | 绑定群到Agent  | `python3 group_manager.py bind oc_xxx bi4sight_ops 运维群` |
| `unbind <群ID>`                | 解除群绑定     | `python3 group_manager.py unbind oc_xxx`                   |
| `reassign <群ID> <AgentID>`    | 重新分配群     | `python3 group_manager.py reassign oc_xxx main`            |
| `info <群ID>`                  | 查询群信息     | `python3 group_manager.py info oc_xxx`                     |

### Agent ID 对照表

| Agent ID                | 名称            | 主题         |
| ----------------------- | --------------- | ------------ |
| main                    | Beta 🦞         | 项目智能中心 |
| bi4sight_ops            | BI4Sight Ops 🔧 | 运维执行     |
| bi4sight_code_manager   | Code Manager 📦 | 代码管理     |
| bi4sight_product_expert | 产品专家 💡     | 产品知识     |
| bi4sight_qa             | 答疑助手 🎯     | 产品答疑     |

## 操作流程

### 1. 查看当前绑定

```
python3 ~/.openclaw/skills/feishu-group-manager/scripts/group_manager.py list
```

### 2. 设置群绑定

当 BOSS 在群中说"把这个群交给运维"或"设置群归属为xxx"时:

1. 获取当前群ID (从消息上下文的 peer.id)
2. 确认目标 Agent
3. 执行: `python3 group_manager.py bind <群ID> <AgentID> <群名>`
4. 重启网关使生效: `openclaw gateway restart`
5. 回复确认信息

### 3. 修改群绑定

当 BOSS 要求更换群归属时:

1. 执行: `python3 group_manager.py reassign <群ID> <新AgentID>`
2. 重启网关
3. 回复确认

### 4. 解除群绑定

当 BOSS 要求移除群绑定时:

1. 执行: `python3 group_manager.py unbind <群ID>`
2. 重启网关
3. 该群将落入 catch-all → bi4sight_qa

## 重要规则

1. **绑定顺序**: 脚本自动将新绑定插入到 catch-all 之前，确保优先匹配
2. **catch-all**: 最后一个绑定(无 peer)是 catch-all，所有未绑定群→bi4sight_qa
3. **BOSS私聊**: 固定路由到 main(Beta)，不可修改
4. **每次修改后必须重启网关**: `openclaw gateway restart`
5. **群名可选**: 建议提供群名便于管理，不提供则用群ID代替

## 数据文件

- 绑定配置: `~/.openclaw/openclaw.json` → bindings[]
- 群信息库: `~/.openclaw/workspace/groups.json`

## 常见对话意图映射

| BOSS 说法                       | 操作                           |
| ------------------------------- | ------------------------------ |
| "这个群归运维" / "把群交给ops"  | bind → bi4sight_ops            |
| "这个群归产品专家"              | bind → bi4sight_product_expert |
| "这个群归Beta" / "我来管这个群" | bind → main                    |
| "这个群谁在管?"                 | info                           |
| "列出所有群" / "群绑定情况"     | list                           |
| "换个人管这个群"                | reassign                       |
| "这个群不用管了"                | unbind                         |
