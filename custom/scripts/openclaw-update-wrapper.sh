#!/bin/bash
# OpenClaw 更新通知脚本 - 自动在更新前发送飞书通知到管理群
# 用法: 通过 alias 替换 openclaw update，或手动调用

GROUP_CHAT_ID="oc_5b6bf7f3c175d48d7a0459d9f29a29e9"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CURRENT_VERSION=$(/opt/homebrew/bin/openclaw --version 2>/dev/null | head -1 || echo "unknown")
LOG_FILE="/Users/devin/.openclaw/logs/update-notify.log"

log() {
    echo "[$TIMESTAMP] $1" >> "$LOG_FILE"
}

# 发送通知到管理群
send_notice() {
    local message="$1"
    # 使用 openclaw message 命令发送（如果 gateway 还在运行）
    /opt/homebrew/bin/openclaw message send \
        --target "chat:$GROUP_CHAT_ID" \
        --message "$message" \
        2>/dev/null
    
    if [ $? -eq 0 ]; then
        log "✅ 通知已发送: $message"
    else
        log "⚠️ 通知发送失败（Gateway可能已停止），写入本地文件"
        # 写入本地文件，由 watchdog 在 Gateway 恢复后补发
        echo "$message" > /tmp/openclaw-update-notice.txt
    fi
}

# 主流程
echo "🔄 准备更新 OpenClaw..."
echo "当前版本: $CURRENT_VERSION"
echo ""

# 1. 发送更新前通知（必须在 Gateway 停止前发送）
log "发送更新前通知..."
/opt/homebrew/bin/openclaw message send \
    --target "chat:$GROUP_CHAT_ID" \
    --message "🔄 OpenClaw 更新中 | $TIMESTAMP
当前版本: $CURRENT_VERSION
预计耗时: 2-5分钟
更新期间服务短暂中断，请稍候..." \
    2>/dev/null

if [ $? -ne 0 ]; then
    log "⚠️ 通知发送失败，写入本地文件由 watchdog 补发"
    echo "🔄 OpenClaw 更新中 | $TIMESTAMP\n当前版本: $CURRENT_VERSION\n预计耗时: 2-5分钟" > /tmp/openclaw-update-notice.txt
fi

# 2. 执行真正的更新（传递所有参数）
log "开始执行 openclaw update..."
/opt/homebrew/bin/openclaw update "$@"
UPDATE_EXIT_CODE=$?

# 3. 发送更新完成通知
NEW_VERSION=$(/opt/homebrew/bin/openclaw --version 2>/dev/null | head -1 || echo "unknown")
if [ $UPDATE_EXIT_CODE -eq 0 ]; then
    send_notice "✅ OpenClaw 更新完成 | $(date '+%Y-%m-%d %H:%M:%S')
旧版本: $CURRENT_VERSION
新版本: $NEW_VERSION
服务已恢复，可以正常使用。"
else
    send_notice "❌ OpenClaw 更新失败 | $(date '+%Y-%m-%d %H:%M:%S')
旧版本: $CURRENT_VERSION
错误码: $UPDATE_EXIT_CODE
请检查日志或手动处理。"
fi

exit $UPDATE_EXIT_CODE
