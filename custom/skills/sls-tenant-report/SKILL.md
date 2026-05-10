---
name: sls-tenant-report
version: 1.0
description: 查询客户运营数据的上报情况，按 tenant-id 分组统计 GlobalExceptionHandlerMiddleware + operation_api 日志
category: devops
---

# SLS 客户运营数据上报查询

## 功能说明

查询 SLS `all-log` 库中 GlobalExceptionHandlerMiddleware 记录的 operation_api 请求日志，按 tenant_id 分组统计数量。

## 查询条件

- **Logstore**: all-log
- **Project**: bi4sight-back-sg1
- **查询语句**: `class: "HuntMobi.BI4Sight.Architecture.Infrastructures.Middleware.GlobalExceptionHandlerMiddleware" and message: operation_api`
- **分组**: tenant_id
- **时间范围**: 支持当天/昨天/自定义

## 前置依赖

### 索引配置要求

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

## 使用方式

### 基础查询（当天+昨日）

```python
python3 ~/.openclaw/skills/sls-tenant-report/query_tenant_report.py
```

### 指定时间范围

```python
python3 ~/.openclaw/skills/sls-tenant-report/query_tenant_report.py --from 2026-04-25 --to 2026-04-28
```

## 输出格式

| tenant_id | 昨日数量 | 今日数量 | 合计 |
| --------- | -------- | -------- | ---- |

## 状态说明

- ✅ 正常：返回完整分组统计
- ⚠️ 需关注：tenant_id doc_value=false，SQL 聚合失效
- 🔴 异常：SLS API 调用失败
