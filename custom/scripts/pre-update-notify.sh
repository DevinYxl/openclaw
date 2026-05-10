#!/bin/bash
# 更新前通知脚本 - 在手动更新 Gateway 前发送飞书通知
# 用法: bash ~/.openclaw/scripts/pre-update-notify.sh

GROUP_CHAT_ID="oc_5b6bf7f3c175d48d7a0459d9f29a29e9"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CURRENT_VERSION=$(openclaw --version 2>/dev/null || echo "unknown")

echo "[$TIMESTAMP] 🔄 即将执行 OpenClaw 更新..."
echo "当前版本: $CURRENT_VERSION"
echo "预计耗时: 2-5分钟"
echo ""

# 通过飞书 API 发送通知（使用 openclaw 内置的消息发送能力）
# 这里通过直接调用 message tool 的方式发送
# 由于这是独立脚本，我们通过写入通知文件的方式，由 watchdog 或 cron 读取发送

NOTICE_FILE="/tmp/openclaw-update-notice.txt"
cat > "$NOTICE_FILE" << EOF
🔄 OpenClaw 更新中 | $TIMESTAMP
当前版本: $CURRENT_VERSION
预计耗时: 2-5分钟
更新完成后自动恢复，请稍候...
EOF

echo "通知已写入: $NOTICE_FILE"
echo ""
echo "提示: 请手动发送通知到管理群，或使用以下命令:"
echo "  openclaw message send --target 'chat:$GROUP_CHAT_ID' --message '🔄 OpenClaw 正在更新，预计2-5分钟...'"
