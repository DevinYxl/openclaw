#!/bin/bash
# Gateway 探活守护脚本 - 每2分钟检查一次
# 功能：
# 1. 检查 Gateway 是否在运行且可达
# 2. 如果异常，自动重启
# 3. 如果检测到更新通知，发送到管理群

PORT=18789
LAUNCH_PLIST="ai.openclaw.gateway"
LOG_FILE="/Users/devin/.openclaw/logs/gateway-watchdog.log"
NOTICE_FILE="/tmp/openclaw-update-notice.txt"
NOTICE_SENT_FLAG="/tmp/openclaw-update-notice-sent"
MAX_RETRIES=3

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查进程是否在运行
check_process() {
    launchctl list "$LAUNCH_PLIST" 2>/dev/null | grep -q "$LAUNCH_PLIST"
}

# 检查端口是否可达
check_port() {
    curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 "http://localhost:$PORT/health" 2>/dev/null | grep -q "200"
}

# 发送飞书通知（通过 OpenClaw cron wake）
send_feishu_notice() {
    local message="$1"
    # 通过 openclaw cron wake 发送通知到 Beta Agent
    # Beta Agent 收到后会转发到管理群
    openclaw cron wake --text "GATEWAY_WATCHDOG_NOTICE: $message" 2>/dev/null
}

# 检查是否有更新通知需要发送
check_update_notice() {
    if [ -f "$NOTICE_FILE" ] && [ ! -f "$NOTICE_SENT_FLAG" ]; then
        local notice=$(cat "$NOTICE_FILE")
        log "📤 发送更新通知: $notice"
        send_feishu_notice "$notice"
        touch "$NOTICE_SENT_FLAG"
    fi
    
    # 如果 Gateway 恢复了，清理通知
    if [ -f "$NOTICE_SENT_FLAG" ] && check_process && check_port; then
        log "✅ Gateway 已恢复，清理通知标志"
        rm -f "$NOTICE_FILE" "$NOTICE_SENT_FLAG"
    fi
}

# 重启 Gateway
restart_gateway() {
    log "尝试重启 Gateway (第 $1/$MAX_RETRIES 次)..."
    launchctl kickstart -k "$LAUNCH_PLIST" 2>/dev/null || launchctl start "$LAUNCH_PLIST" 2>/dev/null
    sleep 5
}

# 主逻辑
check_update_notice

if check_process && check_port; then
    # 正常，无需记录
    exit 0
fi

log "⚠️ Gateway 异常！进程状态: $(check_process && echo 'running' || echo 'stopped'), 端口状态: $(check_port && echo 'reachable' || echo 'unreachable')"

# 尝试重启
for i in $(seq 1 $MAX_RETRIES); do
    restart_gateway $i
    if check_process && check_port; then
        log "✅ Gateway 重启成功"
        exit 0
    fi
    sleep 5
done

log "❌ Gateway 重启失败，已尝试 $MAX_RETRIES 次"
send_feishu_notice "🔴 Gateway 异常且重启失败，请人工检查！"
