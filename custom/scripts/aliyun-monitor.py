#!/usr/bin/env python3
"""
Aliyun ECS Monitor Agent - BI4Sight 专用
每10分钟检查一次ECS状态，记录完整指标，异常时通知Main Agent
"""

import json
import sqlite3
import logging
from datetime import datetime, timedelta
from aliyunsdkcore.client import AcsClient
from aliyunsdkcms.request.v20190101.DescribeMetricLastRequest import DescribeMetricLastRequest

# ============== 配置 ==============
CONFIG = {
    "aliyun_config": "/root/.aliyun/config.json",
    "db_path": "/root/.openclaw/data/aliyun-metrics.db",
    "log_path": "/root/.openclaw/logs/aliyun-monitor.log",
    "project": "BI4Sight",
}

# 完整监控指标列表
METRICS_TO_COLLECT = [
    # 核心指标
    ("CPUUtilization", "cpu", "%", "cpu_total"),
    ("memory_usedutilization", "memory", "%", "memory_used"),
    ("diskusage_utilization", "disk", "%", "disk_usage"),
    ("LoadAverage", "load_avg", "", "load_average"),
    
    # 网络指标
    ("IntranetInRate", "net_in", "bps", "network_in"),
    ("IntranetOutRate", "net_out", "bps", "network_out"),
    ("net_tcpconnection", "tcp_conn", "count", "tcp_connections"),
    ("networkin_rate", "net_in_pkt", "pps", "network_in_packets"),
    ("networkout_rate", "net_out_pkt", "pps", "network_out_packets"),
    
    # 磁盘指标
    ("DiskReadBPS", "disk_read", "B/s", "disk_read_bps"),
    ("DiskWriteBPS", "disk_write", "B/s", "disk_write_bps"),
    ("DiskReadIOPS", "disk_read_iops", "iops", "disk_read_iops"),
    ("DiskWriteIOPS", "disk_write_iops", "iops", "disk_write_iops"),
    ("DiskIOQueueSize", "disk_queue", "count", "disk_io_queue"),
    
    # 系统指标
    ("cpu_system", "cpu_sys", "%", "cpu_system"),
    ("cpu_user", "cpu_user", "%", "cpu_user"),
    ("cpu_wait", "cpu_wait", "%", "cpu_wait"),
    ("load_1m", "load_1", "", "load_1m"),
    ("load_5m", "load_5", "", "load_5m"),
    ("load_15m", "load_15", "", "load_15m"),
    ("vm.ProcessCount", "process_count", "count", "process_count"),
    
    # 连接指标
    ("concurrentConnections", "conn_curr", "count", "concurrent_connections"),
    ("InternetInRate", "pub_in", "bps", "public_in"),
    ("InternetOutRate", "pub_out", "bps", "public_out"),
]

# 告警阈值配置 (分层)
THRESHOLDS = {
    # 默认阈值
    "default": {
        "cpu": {"warning": 70, "serious": 85, "critical": 95},
        "memory": {"warning": 80, "serious": 90, "critical": 95},
        "disk": {"warning": 75, "serious": 85, "critical": 95},
        "tcp_conn": {"warning": 8000, "serious": 10000, "critical": 15000},
        "disk_io": {"warning": 70, "serious": 85, "critical": 95},
        "load": {"warning": 4, "serious": 6, "critical": 8},
    },
    # 数据库层 (SQLDB*) - 更严格的阈值
    "database": {
        "cpu": {"warning": 70, "serious": 80, "critical": 90},
        "memory": {"warning": 85, "serious": 90, "critical": 95},
        "disk": {"warning": 80, "serious": 90, "critical": 95},
        "tcp_conn": {"warning": 3000, "serious": 5000, "critical": 8000},
        "disk_io": {"warning": 70, "serious": 85, "critical": 95},
        "load": {"warning": 8, "serious": 12, "critical": 16},
    },
    # 后端服务层 (BG-SERVICE*) - 标准阈值
    "backend": {
        "cpu": {"warning": 75, "serious": 85, "critical": 95},
        "memory": {"warning": 80, "serious": 90, "critical": 95},
        "disk": {"warning": 70, "serious": 85, "critical": 90},
        "tcp_conn": {"warning": 5000, "serious": 8000, "critical": 12000},
        "disk_io": {"warning": 60, "serious": 80, "critical": 90},
        "load": {"warning": 6, "serious": 10, "critical": 14},
    },
    # 中间件层 (MID-*) - 稍宽松
    "middleware": {
        "cpu": {"warning": 70, "serious": 80, "critical": 90},
        "memory": {"warning": 75, "serious": 85, "critical": 90},
        "disk": {"warning": 70, "serious": 80, "critical": 90},
        "tcp_conn": {"warning": 5000, "serious": 8000, "critical": 10000},
        "disk_io": {"warning": 60, "serious": 75, "critical": 85},
        "load": {"warning": 6, "serious": 10, "critical": 14},
    },
}

# 实例名称映射
INSTANCE_NAMES = {
    "i-t4n7qsqmw3au7e4vbrzw": "BI4SIGHT-BG-SERVICE-2",
    "i-t4n1m12422xrnlh80unv": "BI4SIGHT-BG-SERVICE-3",
    "i-t4n76c1gre31ol5rym5f": "BI4SIGHT-BG-SERVICE-4",
    "i-t4nfcmih18b0pu27hwvu": "BI4SIGHT-BG-SERVICE-MAIN",
    "i-t4n9ktm2n1lhp7sj4i4l": "BI4SIGHT-JUMPSERVER",
    "i-t4neohg706a1ms4p0pwb": "BI4SIGHT-MID-GATEWAY",
    "i-t4nagisyz6bkv8t6lke2": "BI4SIGHT-MID-GATEWAY2",
    "i-t4n7qryy9qm5o82x8v52": "BI4SIGHT-MID-NGINX",
    "i-t4nb0l0flenhq7utgkut": "BI4SIGHT-MID-REDIS-1",
    "i-t4ncx4lrinqccs04msf4": "BI4SIGHT-SQLDB1-1",
    "i-t4nhhkxxvnt8tq8ctxki": "BI4SIGHT-SQLDB1-2",
    "i-t4n1y5y1jezsgpov23gw": "BI4SIGHT-SQLDB2-1",
    "i-t4nhj96vxjg61si37qqt": "BI4SIGHT-SQLDB2-2",
    "i-t4nc7qr0xsn2797noxy7": "BI4SIGHT-SQLDB3-1",
    "i-t4n6xjvwmyz0v8oipbbn": "BI4SIGHT-SQLDB3-2",
    "i-t4ndf2e41u69s3onlux3": "BI4SIGHT-SQLDB4-1",
    "i-t4nb1ra8pbxants7edln": "BI4SIGHT-SQLDB4-2",
    "i-t4ndaqjvsmxfz3ges4eh": "BI4SIGHT-SQLDBHmt-1",
    "i-t4n9of5gidh0949juj3d": "BI4SIGHT-WEB2APP",
    "i-t4nancpp121hc11pilbb": "BI4SIGHT-WEB2APP-2",
    "i-t4n1pd4a18q0cx61nvuo": "BI4SIGHT-WEBAPI-2",
    "i-t4nhzulskqs9lv2blybr": "BI4SIGHT-WEBAPI-MAIN",
    "i-t4n6rcgdumk2ktz8kkoq": "BI4Sight-AI-Service-01"
}

# 监控分组
MONITOR_GROUPS = {
    '243272156': 'APIs',
    '243272160': 'Mids',
    '243272165': 'BackServices',
    '243272172': 'Databases',
    '243437034': 'Nginx',
    '243786945': 'Web2app'
}

# ============== 日志设置 ==============
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_path"]),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============== 辅助函数 ==============
def get_instance_tier(name):
    """获取实例所属层级"""
    name_upper = name.upper()
    if 'SQLDB' in name_upper:
        return "database"
    elif 'BG-SERVICE' in name_upper:
        return "backend"
    elif 'MID-' in name_upper or 'NGINX' in name_upper or 'REDIS' in name_upper:
        return "middleware"
    return "default"


def get_threshold_key(metric_name):
    """获取指标对应的阈值键"""
    if 'cpu' in metric_name.lower():
        return "cpu"
    elif 'memory' in metric_name.lower():
        return "memory"
    elif 'disk' in metric_name.lower() or 'io' in metric_name.lower():
        return "disk"
    elif 'tcp' in metric_name.lower() or 'conn' in metric_name.lower():
        return "tcp_conn"
    elif 'load' in metric_name.lower():
        return "load"
    return None


# ============== 数据库 ==============
def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()
    
    # 指标记录表 - 完整版
    c.execute('''CREATE TABLE IF NOT EXISTS ecs_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        instance_id TEXT,
        instance_name TEXT,
        tier TEXT,
        cpu_utilization REAL,
        memory_utilization REAL,
        disk_utilization REAL,
        disk_total_gb REAL,
        disk_used_gb REAL,
        disk_avail_gb REAL,
        load_average REAL,
        net_in_rate REAL,
        net_out_rate REAL,
        tcp_connections INTEGER,
        disk_read_bps REAL,
        disk_write_bps REAL,
        disk_read_iops REAL,
        disk_write_iops REAL,
        disk_io_queue REAL,
        cpu_system REAL,
        cpu_user REAL,
        cpu_wait REAL,
        load_1m REAL,
        load_5m REAL,
        load_15m REAL,
        process_count INTEGER,
        public_in_rate REAL,
        public_out_rate REAL
    )''')
    
    # 告警表
    c.execute('''CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        instance_id TEXT,
        instance_name TEXT,
        tier TEXT,
        metric_name TEXT,
        metric_value REAL,
        threshold REAL,
        severity TEXT,
        growth_rate REAL,
        days_remaining REAL,
        reason TEXT,
        acknowledged INTEGER DEFAULT 0,
        notified INTEGER DEFAULT 0
    )''')
    
    # 每日汇总表
    c.execute('''CREATE TABLE IF NOT EXISTS alert_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE,
        total_alerts INTEGER,
        critical_count INTEGER,
        serious_count INTEGER,
        warning_count INTEGER,
        acknowledged INTEGER,
        notified INTEGER
    )''')
    
    # 创建索引
    c.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON ecs_metrics(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_metrics_instance ON ecs_metrics(instance_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_alerts_instance ON alerts(instance_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity)')
    
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")


def save_metrics_full(instance_id, instance_name, tier, metrics_data):
    """保存完整指标数据"""
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()
    
    columns = ['instance_id', 'instance_name', 'tier']
    values = [instance_id, instance_name, tier]
    
    col_mapping = {
        'cpu': 'cpu_utilization', 'memory': 'memory_utilization',
        'disk': 'disk_utilization', 
        'disk_total': 'disk_total_gb',
        'disk_used': 'disk_used_gb', 
        'disk_avail': 'disk_avail_gb',
        'load': 'load_average', 'net_in': 'net_in_rate', 'net_out': 'net_out_rate',
        'tcp_conn': 'tcp_connections', 'disk_read': 'disk_read_bps',
        'disk_write': 'disk_write_bps', 'disk_read_iops': 'disk_read_iops',
        'disk_write_iops': 'disk_write_iops', 'disk_queue': 'disk_io_queue',
        'cpu_sys': 'cpu_system', 'cpu_user': 'cpu_user',
        'cpu_wait': 'cpu_wait', 'load_1': 'load_1m', 'load_5': 'load_5m',
        'load_15': 'load_15m', 'process_count': 'process_count',
        'pub_in': 'public_in_rate', 'pub_out': 'public_out_rate'
    }
    
    for key, col_name in col_mapping.items():
        if key in metrics_data and metrics_data[key] is not None:
            val = metrics_data[key]
            # 磁盘空间指标从字节转换为GB
            if key in ['disk_total', 'disk_used', 'disk_avail']:
                val = val / (1024**3)  # 字节 -> GB
            columns.append(col_name)
            values.append(val)
    
    placeholders = ','.join(['?'] * len(values))
    c.execute(f'''INSERT INTO ecs_metrics ({','.join(columns)}) VALUES ({placeholders})''', values)
    
    conn.commit()
    conn.close()


def save_alert(instance_id, instance_name, tier, metric_name, value, threshold, severity,
                growth_rate=None, days_remaining=None, reason=None):
    """保存告警"""
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()
    c.execute('''INSERT INTO alerts 
        (instance_id, instance_name, tier, metric_name, metric_value, threshold, severity,
         growth_rate, days_remaining, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (instance_id, instance_name, tier, metric_name, value, threshold, severity,
         growth_rate, days_remaining, reason))
    alert_id = c.lastrowid
    conn.commit()
    conn.close()
    return alert_id


def check_recent_alerts(instance_id, metric_name, minutes=60):
    """检查最近告警"""
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()
    since = datetime.now() - timedelta(minutes=minutes)
    c.execute('''SELECT COUNT(*) FROM alerts 
        WHERE instance_id=? AND metric_name=? AND timestamp>?''',
        (instance_id, metric_name, since))
    count = c.fetchone()[0]
    conn.close()
    return count


def should_notify(alert_id, severity):
    """判断是否需要通知 (合并策略)"""
    if severity == "critical":
        return True
    
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()
    
    window = 30 if severity == "serious" else 120
    since = datetime.now() - timedelta(minutes=window)
    
    c.execute('''SELECT COUNT(*) FROM alerts 
        WHERE severity=? AND notified=1 AND timestamp>?''',
        (severity, since))
    notified_count = c.fetchone()[0]
    
    if notified_count == 0:
        c.execute('UPDATE alerts SET notified=1 WHERE id=?', (alert_id,))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False


# ============== 阿里云 API ==============
def get_aliyun_client():
    """获取阿里云客户端"""
    with open(CONFIG["aliyun_config"]) as f:
        cred = json.load(f)['profiles'][0]
    return AcsClient(cred['access_key_id'], cred['access_key_secret'], cred['region_id'])


def get_metric(client, group_id, metric_name):
    """获取分组指标"""
    request = DescribeMetricLastRequest()
    request.set_accept_format('json')
    request.add_query_param('MetricName', metric_name)
    request.add_query_param('Namespace', 'acs_ecs_dashboard')
    request.add_query_param('Period', '60')
    request.add_query_param('GroupId', group_id)
    
    try:
        response = client.do_action_with_exception(request)
        data = json.loads(response)
        if data.get('Code') == '200' and data.get('Datapoints'):
            return json.loads(data['Datapoints'])
    except Exception as e:
        pass
    return []


def get_severity(tier, metric_key, value):
    """判断告警级别 (考虑层级)"""
    tier_config = THRESHOLDS.get(tier, THRESHOLDS["default"])
    thresholds = tier_config.get(metric_key)
    
    if thresholds is None:
        # 对于未定义的指标，使用百分比判断
        if metric_key in ['cpu', 'memory', 'disk']:
            if value >= 95:
                return "critical"
            elif value >= 85:
                return "serious"
            elif value >= 70:
                return "warning"
        return None
    
    if value >= thresholds["critical"]:
        return "critical"
    elif value >= thresholds["serious"]:
        return "serious"
    elif value >= thresholds["warning"]:
        return "warning"
    return None


def calculate_disk_trend(instance_id, hours=72):
    """分析磁盘使用趋势，返回增长率(GB/小时)和预计剩余天数"""
    conn = sqlite3.connect(CONFIG["db_path"])
    c = conn.cursor()
    
    since = datetime.now() - timedelta(hours=hours)
    
    # 优先使用实际剩余空间计算趋势
    c.execute('''SELECT timestamp, disk_avail_gb, disk_used_gb, disk_total_gb FROM ecs_metrics 
        WHERE instance_id=? AND (disk_avail_gb IS NOT NULL OR disk_used_gb IS NOT NULL) AND timestamp>?
        ORDER BY timestamp ASC''',
        (instance_id, since))
    
    rows = c.fetchall()
    conn.close()
    
    if len(rows) < 2:
        return None, None, None  # 数据不足
    
    try:
        # 尝试使用剩余空间计算
        avail_data = [(datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S'), r[1]) for r in rows if r[1] is not None]
        
        if len(avail_data) >= 2:
            first_ts, first_avail = avail_data[0]
            last_ts, last_avail = avail_data[-1]
            time_diff_hours = (last_ts - first_ts).total_seconds() / 3600
            
            if time_diff_hours >= 1:
                # 计算减少速度 (GB/小时)
                used_growth_gb_per_hour = (first_avail - last_avail) / time_diff_hours
                
                if used_growth_gb_per_hour > 0.01:  # 至少0.01 GB/小时
                    days_remaining = last_avail / used_growth_gb_per_hour / 24
                else:
                    days_remaining = 999
                
                return round(used_growth_gb_per_hour, 4), round(days_remaining, 1), last_avail
        
        # 备用: 使用已用空间计算
        used_data = [(datetime.strptime(r[0], '%Y-%m-%d %H:%M:%S'), r[2]) for r in rows if r[2] is not None]
        
        if len(used_data) >= 2:
            first_ts, first_used = used_data[0]
            last_ts, last_used = used_data[-1]
            time_diff_hours = (last_ts - first_ts).total_seconds() / 3600
            
            if time_diff_hours >= 1:
                used_growth_gb_per_hour = (last_used - first_used) / time_diff_hours
                total_gb = rows[-1][3]  # disk_total_gb
                
                if used_growth_gb_per_hour > 0.01 and total_gb:
                    remaining = total_gb - last_used
                    days_remaining = remaining / used_growth_gb_per_hour / 24
                else:
                    days_remaining = 999
                    remaining = total_gb - last_used if total_gb else None
                
                return round(used_growth_gb_per_hour, 4), round(days_remaining, 1), remaining
        
        return None, None, None
    except Exception as e:
        return None, None, None


def get_disk_severity_with_trend(tier, current_usage, instance_id, instance_name, current_avail_gb=None):
    """结合增长趋势和实际剩余空间判断磁盘告警级别"""
    growth_rate_gb_h, days_remaining, avail_gb = calculate_disk_trend(instance_id)
    
    # 如果有传入实际剩余空间，优先使用
    if current_avail_gb is not None:
        avail_gb = current_avail_gb
    
    tier_config = THRESHOLDS.get(tier, THRESHOLDS["default"])
    thresholds = tier_config.get("disk", THRESHOLDS["default"]["disk"])
    
    # 基础阈值 (百分比)
    base_warning = thresholds["warning"]
    base_serious = thresholds["serious"]
    base_critical = thresholds["critical"]
    
    # 紧急空间阈值 (GB) - 低于此值立即告警
    CRITICAL_AVAIL_GB = 5  # 剩余 < 5GB 紧急
    WARNING_AVAIL_GB = 20  # 剩余 < 20GB 警告
    SERIOUS_AVAIL_GB = 10  # 剩余 < 10GB 严重
    
    # 紧急天数阈值
    CRITICAL_DAYS = 1
    SERIOUS_DAYS = 3
    WARNING_DAYS = 7
    
    # 1. 先检查绝对剩余空间 (只对数据盘有效，系统盘<1GB跳过)
    if avail_gb is not None and avail_gb > 1:
        # 这是一个有效的数据盘 (剩余>1GB)
        if avail_gb <= CRITICAL_AVAIL_GB:
            return "critical", growth_rate_gb_h, days_remaining, avail_gb, f"剩余{avail_gb:.1f}GB (紧急)"
        elif avail_gb <= SERIOUS_AVAIL_GB:
            return "serious", growth_rate_gb_h, days_remaining, avail_gb, f"剩余{avail_gb:.1f}GB (严重)"
        elif avail_gb <= WARNING_AVAIL_GB:
            return "warning", growth_rate_gb_h, days_remaining, avail_gb, f"剩余{avail_gb:.1f}GB (警告)"
    
    # 2. 再检查增长趋势
    if growth_rate_gb_h is not None and days_remaining is not None and days_remaining < 999:
        if days_remaining <= CRITICAL_DAYS:
            return "critical", growth_rate_gb_h, days_remaining, avail_gb, f"剩余{avail_gb:.1f}GB,预计{days_remaining:.1f}天满"
        elif days_remaining <= SERIOUS_DAYS:
            return "serious", growth_rate_gb_h, days_remaining, avail_gb, f"剩余{avail_gb:.1f}GB,预计{days_remaining:.1f}天满"
        elif days_remaining <= WARNING_DAYS:
            return "warning", growth_rate_gb_h, days_remaining, avail_gb, f"剩余{avail_gb:.1f}GB,预计{days_remaining:.1f}天满"
    
    # 3. 备用百分比判断
    if current_usage >= base_critical:
        return "critical", growth_rate_gb_h, days_remaining, avail_gb, f"磁盘{current_usage}%"
    elif current_usage >= base_serious:
        return "serious", growth_rate_gb_h, days_remaining, avail_gb, f"磁盘{current_usage}%"
    elif current_usage >= base_warning:
        return "warning", growth_rate_gb_h, days_remaining, avail_gb, f"磁盘{current_usage}%"
    
    return None, growth_rate_gb_h, days_remaining, avail_gb, None


# ============== 通知 Main Agent ==============
def notify_main_agent(alerts):
    """通知 Main Agent - 通过写入通知文件"""
    if not alerts:
        return
    
    notify_file = "/root/.openclaw/workspace/ALIYUN-ALERTS.json"
    
    existing = []
    try:
        with open(notify_file, 'r') as f:
            existing = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    # 添加新告警
    existing.extend(alerts)
    
    with open(notify_file, 'w') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    
    logger.info(f"已写入 {len(alerts)} 条告警到 {notify_file}")


# ============== 主监控流程 ==============
def monitor():
    """主监控流程"""
    logger.info("=" * 60)
    logger.info(f"开始 ECS 监控... [BI4Sight 项目]")
    
    client = get_aliyun_client()
    pending_alerts = []
    
    # 获取所有分组的所有指标 (去重)
    all_metrics = {}
    processed_instances = set()
    
    # 指标名称映射
    metric_map = {
        'CPUUtilization': 'cpu',
        'memory_usedutilization': 'memory',
        'diskusage_utilization': 'disk',
        'diskusage_total': 'disk_total',      # 磁盘总容量 (GB)
        'diskusage_used': 'disk_used',        # 已用空间 (GB)
        'diskusage_avail': 'disk_avail',     # 剩余空间 (GB)
        'LoadAverage': 'load',
        'IntranetInRate': 'net_in',
        'IntranetOutRate': 'net_out',
        'net_tcpconnection': 'tcp_conn',
        'DiskReadBPS': 'disk_read',
        'DiskWriteBPS': 'disk_write',
        'DiskReadIOPS': 'disk_read_iops',
        'DiskWriteIOPS': 'disk_write_iops',
        'DiskIOQueueSize': 'disk_queue',
        'cpu_system': 'cpu_sys',
        'cpu_user': 'cpu_user',
        'cpu_wait': 'cpu_wait',
        'load_1m': 'load_1',
        'load_5m': 'load_5',
        'load_15m': 'load_15',
        'vm.ProcessCount': 'process_count',
        'InternetInRate': 'pub_in',
        'InternetOutRate': 'pub_out',
    }
    
    for group_id, group_name in MONITOR_GROUPS.items():
        logger.info(f"检查分组: {group_name}")
        
        # 获取各项指标
        for aliyun_metric, local_key in metric_map.items():
            data = get_metric(client, group_id, aliyun_metric)
            
            for point in data:
                inst_id = point.get('instanceId')
                if inst_id in processed_instances:
                    continue
                if inst_id not in all_metrics:
                    all_metrics[inst_id] = {'instance_id': inst_id}
                all_metrics[inst_id][local_key] = point.get('Average')
    
    # 标记已处理的实例
    for inst_id in all_metrics.keys():
        processed_instances.add(inst_id)
    
    # 处理每个实例
    for inst_id, metrics in all_metrics.items():
        if inst_id not in INSTANCE_NAMES:
            continue
        
        name = INSTANCE_NAMES[inst_id]
        tier = get_instance_tier(name)
        
        # 保存指标
        save_metrics_full(inst_id, name, tier, metrics)
        
        # 检查告警
        alerts = []
        
        # 定义需要检查的指标
        check_items = [
            ('cpu', 'CPU使用率', 100),
            ('memory', '内存使用率', 100),
            ('disk', '磁盘使用率', 100),
            ('load', '系统负载', 100),
            ('tcp_conn', 'TCP连接数', 20000),
            ('disk_queue', 'IO队列', 200),
        ]
        
        for metric_key, metric_label, max_val in check_items:
            value = metrics.get(metric_key)
            if value is None:
                continue
            
            # 磁盘使用特殊处理：基于增长趋势和实际剩余空间
            if metric_key == 'disk':
                # 获取实际剩余空间 (API返回字节，需转换为GB)
                avail_raw = metrics.get('disk_avail')
                avail_gb = avail_raw / (1024**3) if avail_raw else None
                
                severity, growth_rate, days_remaining, avail, reason = get_disk_severity_with_trend(
                    tier, value, inst_id, name, avail_gb
                )
                
                if severity:
                    thresholds = THRESHOLDS.get(tier, THRESHOLDS["default"]).get("disk", {})
                    threshold = thresholds.get(severity, 0)
                    
                    alert_id = save_alert(inst_id, name, tier, metric_label, value, threshold, severity,
                                        growth_rate, days_remaining, reason)
                    
                    # 特殊记录增长趋势信息
                    recent_count = check_recent_alerts(inst_id, metric_label)
                    
                    if recent_count >= 3:
                        logger.warning(f"实例 {name} 磁盘告警3次+，立即通知")
                        alerts.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'instance_name': name,
                            'tier': tier,
                            'severity': 'critical',
                            'metric_name': '磁盘使用率+趋势',
                            'value': round(value, 2),
                            'threshold': threshold,
                            'growth_rate': growth_rate,
                            'days_remaining': days_remaining,
                            'avail_gb': avail,
                            'reason': reason
                        })
                    elif should_notify(alert_id, severity):
                        alerts.append({
                            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'instance_name': name,
                            'tier': tier,
                            'severity': severity,
                            'metric_name': '磁盘使用率+趋势',
                            'value': round(value, 2),
                            'threshold': threshold,
                            'growth_rate': growth_rate,
                            'days_remaining': days_remaining,
                            'avail_gb': avail,
                            'reason': reason
                        })
                continue
            
            # 百分比指标归一化
            if metric_key in ['cpu', 'memory', 'load']:
                check_value = value
            else:
                # 非百分比指标按比例计算
                check_value = (value / max_val) * 100 if max_val > 0 else 0
            
            severity = get_severity(tier, metric_key, check_value)
            
            if severity:
                threshold_key = metric_key
                thresholds = THRESHOLDS.get(tier, THRESHOLDS["default"]).get(threshold_key, {})
                threshold = thresholds.get(severity, 0)
                
                alert_id = save_alert(inst_id, name, tier, metric_label, value, threshold, severity)
                
                # 检查重复告警
                recent_count = check_recent_alerts(inst_id, metric_label)
                
                if recent_count >= 3:
                    logger.warning(f"实例 {name} {metric_label} 告警3次+，立即通知")
                    alerts.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'instance_name': name,
                        'tier': tier,
                        'severity': 'critical',
                        'metric_name': metric_label,
                        'value': round(value, 2),
                        'threshold': threshold
                    })
                elif should_notify(alert_id, severity):
                    alerts.append({
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M'),
                        'instance_name': name,
                        'tier': tier,
                        'severity': severity,
                        'metric_name': metric_label,
                        'value': round(value, 2),
                        'threshold': threshold
                    })
        
        # 记录日志
        if alerts:
            for a in alerts:
                tier_emoji = {"database": "🗄️", "backend": "⚙️", "middleware": "🔄"}.get(tier, "📦")
                logger.warning(f"{tier_emoji} {name} {a['metric_name']}={a['value']}% ({a['severity']})")
            pending_alerts.extend(alerts)
    
    # 通知 Main Agent
    if pending_alerts:
        notify_main_agent(pending_alerts)
    
    # 统计
    critical_count = len([a for a in pending_alerts if a['severity'] == 'critical'])
    serious_count = len([a for a in pending_alerts if a['severity'] == 'serious'])
    warning_count = len([a for a in pending_alerts if a['severity'] == 'warning'])
    
    logger.info(f"监控完成: 共 {len(pending_alerts)} 条告警 (🔴{critical_count} 🟠{serious_count} 🟡{warning_count})")


# ============== 入口 ==============
if __name__ == "__main__":
    init_db()
    monitor()
