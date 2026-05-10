#!/usr/bin/env python3
"""
SLS 客户运营数据上报查询
查询 GlobalExceptionHandlerMiddleware + operation_api 日志，按 tenant_id 分组
"""

import json
import subprocess
import argparse
from datetime import datetime, timedelta
from collections import defaultdict


def get_timestamp(dt):
    """转换为时间戳"""
    return int(dt.timestamp())


def query_sls(logstore, query, from_time, to_time, limit=100, offset=0):
    """执行 SLS 查询"""
    query_body = {
        "query": query,
        "to": to_time,
        "from": from_time,
        "limit": limit,
        "offset": offset
    }
    body = json.dumps(query_body)
    cmd = [
        'aliyun', 'sls', 'GetLogsV2',
        '--project', 'bi4sight-back-sg1',
        '--logstore', logstore,
        '--region', 'ap-southeast-1',
        '--body', body
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None, result.stderr
    try:
        data = json.loads(result.stdout)
        return data, None
    except:
        return None, "JSON parse failed"


def check_tenant_id_index():
    """检查 tenant_id 是否开启了 doc_value"""
    cmd = [
        'aliyun', 'sls', 'get-index',
        '--project', 'bi4sight-back-sg1',
        '--logstore', 'all-log',
        '--region', 'ap-southeast-1'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return False, "无法获取索引配置"
    
    try:
        data = json.loads(result.stdout)
        keys = data.get('keys', {})
        tenant_config = keys.get('tenant_id', {})
        doc_value = tenant_config.get('doc_value', False)
        return doc_value, "tenant_id doc_value=" + str(doc_value)
    except:
        return False, "解析索引配置失败"


def query_with_sql_agg(from_time, to_time):
    """使用 SQL 聚合查询（需 tenant_id doc_value=true）"""
    query = 'class: "HuntMobi.BI4Sight.Architecture.Infrastructures.Middleware.GlobalExceptionHandlerMiddleware" and message: operation_api | select tenant_id, count(*) as total group by tenant_id order by total desc'
    
    query_body = {
        "query": query,
        "to": to_time,
        "from": from_time,
        "limit": 100
    }
    body = json.dumps(query_body)
    cmd = [
        'aliyun', 'sls', 'GetLogsV2',
        '--project', 'bi4sight-back-sg1',
        '--logstore', 'all-log',
        '--region', 'ap-southeast-1',
        '--body', body
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        return None, result.stderr
    
    data = json.loads(result.stdout)
    logs = data.get('data', [])
    meta = data.get('meta', {})
    
    # 检查是否返回 null（说明 doc_value 未开启）
    if logs and logs[0].get('tenant_id') == 'null':
        return None, "tenant_id doc_value=false，SQL 聚合不可用"
    
    return logs, None


def query_raw_logs(from_time, to_time):
    """Raw query 获取日志（100 条限制）"""
    query = 'class: "HuntMobi.BI4Sight.Architecture.Infrastructures.Middleware.GlobalExceptionHandlerMiddleware" and message: operation_api'
    
    data, err = query_sls("all-log", query, from_time, to_time, limit=100)
    if err:
        return None, err
    
    logs = data.get('data', [])
    meta = data.get('meta', {})
    total = meta.get('count', len(logs))
    
    tenant_counts = defaultdict(int)
    for log in logs:
        tenant_id = log.get('tenant_id', 'unknown')
        tenant_id = tenant_id.strip('"').strip()
        if tenant_id and tenant_id != 'unknown':
            tenant_counts[tenant_id] += 1
    
    return dict(tenant_counts), f"total={total}, fetched={len(logs)} (100条/次限制)"


def main():
    parser = argparse.ArgumentParser(description='查询客户运营数据上报情况')
    parser.add_argument('--from', dest='from_date', default=None, help='开始日期 (YYYY-MM-DD)，默认昨天')
    parser.add_argument('--to', dest='to_date', default=None, help='结束日期 (YYYY-MM-DD)，默认今天')
    parser.add_argument('--days', type=int, default=2, help='查询天数 (默认2天: 昨天+今天)')
    args = parser.parse_args()

    print("=" * 60)
    print("SLS 客户运营数据上报查询")
    print("GlobalExceptionHandlerMiddleware + operation_api")
    print("=" * 60)

    # 检查索引配置
    print("\n[1] 检查 tenant_id 索引配置...")
    has_doc_value, msg = check_tenant_id_index()
    print(f"    {msg}")
    
    # 解析日期
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    if args.from_date:
        from_date = datetime.strptime(args.from_date, '%Y-%m-%d')
    else:
        from_date = today - timedelta(days=args.days - 1)
    
    if args.to_date:
        to_date = datetime.strptime(args.to_date, '%Y-%m-%d') + timedelta(days=1)
    else:
        to_date = today + timedelta(days=1)
    
    from_ts = get_timestamp(from_date)
    to_ts = get_timestamp(to_date)
    
    print(f"\n[2] 查询时间范围: {from_date.strftime('%Y-%m-%d')} - {(to_date - timedelta(days=1)).strftime('%Y-%m-%d')}")
    
    # 执行查询
    print("\n[3] 执行查询...")
    
    if has_doc_value:
        # 使用 SQL 聚合
        print("    模式: SQL 聚合 (doc_value=true)")
        logs, err = query_with_sql_agg(from_ts, to_ts)
        if err:
            print(f"    ⚠️ SQL 聚合失败: {err}")
            print("    回退到 raw query...")
            logs = None
        
        if logs:
            print(f"    ✅ SQL 聚合成功")
            results = {log.get('tenant_id', 'unknown'): int(log.get('total', 0)) for log in logs}
        else:
            results = None
    else:
        results = None
    
    if not results:
        # 回退到 raw query
        print("    模式: Raw query (100条/次限制)")
        results, msg = query_raw_logs(from_ts, to_ts)
        print(f"    ⚠️ {msg}")
        if results:
            print(f"    获取到 {len(results)} 个 tenant_id 的日志")
    
    # 输出结果
    print("\n" + "=" * 60)
    print("查询结果")
    print("=" * 60)
    
    if not results:
        print("❌ 无法获取数据")
        return 1
    
    print(f"\n{'tenant_id':<20} | {'日志总数':>10}")
    print("-" * 35)
    for tenant_id, count in sorted(results.items(), key=lambda x: -x[1]):
        print(f"{tenant_id:<20} | {count:>10}")
    print("-" * 35)
    print(f"{'合计':<20} | {sum(results.values()):>10}")
    
    return 0


if __name__ == "__main__":
    exit(main())
