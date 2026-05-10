#!/bin/bash
#
# BI4Sight Skill Hub Setup Script
# 多渠道技能发现系统集成脚本
#
# 功能:
#   1. 配置 skills.volces.com 私有技能仓库
#   2. 安装 bi4sight-skill-discovery 多渠道搜索技能
#   3. 可选：安装 find-skills 技能
#   4. 可选：配置阿里云 agentexplorer (如果已安装 aliyun CLI)
#
# 用法:
#   ./bi4sight-skill-hub-setup.sh [--install-discover] [--install-find] [--install-aliyun] [--dry-run] [--backup]
#
# 选项:
#   --install-discover   安装 bi4sight-skill-discovery (推荐)
#   --install-find       安装 find-skills 技能
#   --install-aliyun     配置阿里云 agentexplorer (需要 aliyun CLI)
#   --dry-run            仅显示将要执行的操作，不实际执行
#   --backup             执行前备份 openclaw.json
#   --all                安装所有组件
#   --help               显示帮助
#
# 作者: BI4Sight Beta
# 日期: 2026-05-07

# ============== 配置 ==============
SKILLS_API_URL="${SKILLS_API_URL:-https://skills.volces.com/v1}"
OPENCLAW_DIR="${OPENCLAW_DIR:-$HOME/.openclaw}"
WORKSPACE_SKILLS_DIR="$OPENCLAW_DIR/workspace/skills"
BACKUP_DIR="$OPENCLAW_DIR/backups"
LOG_FILE="$OPENCLAW_DIR/logs/skill-hub-setup.log"

# ============== 网络配置 ==============
CURL_TIMEOUT="${CURL_TIMEOUT:-15}"
WGET_TIMEOUT="${WGET_TIMEOUT:-15}"

# ============== 颜色 ==============
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# ============== 状态标志 ==============
HAS_ERRORS=0
HAS_WARNINGS=0

# ============== 日志 ==============
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    mkdir -p "$(dirname "$LOG_FILE" 2>/dev/null)" || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE" 2>/dev/null || true
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1" >> "$LOG_FILE" 2>/dev/null || true
}

log_warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ $1" >> "$LOG_FILE" 2>/dev/null || true
    HAS_WARNINGS=1
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1" >> "$LOG_FILE" 2>/dev/null || true
    HAS_ERRORS=1
}

# ============== 帮助 ==============
show_help() {
    cat << EOF
BI4Sight Skill Hub Setup Script
================================

用法: $0 [选项]

选项:
  --install-discover    安装 bi4sight-skill-discovery 多渠道搜索技能 (推荐)
  --install-find        安装 find-skills 技能
  --install-aliyun      配置阿里云 agentexplorer (需要 aliyun CLI)
  --all                 安装所有组件
  --dry-run             仅显示将要执行的操作，不实际执行
  --backup              执行前备份 openclaw.json
  --help                显示此帮助

示例:
  $0 --install-discover --backup         # 安装多渠道搜索并备份
  $0 --all --dry-run                     # 查看将安装的所有内容
  $0 --install-aliyun                    # 仅配置阿里云技能源

多渠道说明:
  安装后将支持从以下渠道搜索技能:
  1. volcengine (私有) - skills.volces.com
  2. local (本地)      - ~/.openclaw/workspace/skills/
  3. aliyun (阿里云)    - aliyun agentexplorer (如果安装)
EOF
}

# ============== 参数解析 ==============
INSTALL_DISCOVER=false
INSTALL_FIND=false
INSTALL_ALIYUN=false
DRY_RUN=false
DO_BACKUP=false
INSTALL_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --install-discover)
            INSTALL_DISCOVER=true
            shift
            ;;
        --install-find)
            INSTALL_FIND=true
            shift
            ;;
        --install-aliyun)
            INSTALL_ALIYUN=true
            shift
            ;;
        --all)
            INSTALL_ALL=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --backup)
            DO_BACKUP=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 如果指定 --all
if [ "$INSTALL_ALL" = true ]; then
    INSTALL_DISCOVER=true
    INSTALL_FIND=true
    INSTALL_ALIYUN=true
fi

# 如果没有指定任何安装选项，默认安装 discover
if [ "$INSTALL_DISCOVER" = false ] && [ "$INSTALL_FIND" = false ] && [ "$INSTALL_ALIYUN" = false ]; then
    INSTALL_DISCOVER=true
    log_warn "未指定安装选项，默认安装 bi4sight-skill-discovery (--install-discover)"
fi

# ============== 前置检查 ==============
preflight_check() {
    log "执行前置检查..."
    
    # 检查 OpenClaw 目录
    if [ ! -d "$OPENCLAW_DIR" ]; then
        log_error "OpenClaw 目录不存在: $OPENCLAW_DIR"
        return 1
    fi
    
    # 检查 jq (用于 JSON 操作)
    if ! command -v jq &> /dev/null; then
        log_error "jq 未安装，请先安装: brew install jq"
        return 1
    fi
    
    # 检查 curl
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        return 1
    fi
    
    # 检查网络连接
    log "检查网络连接..."
    if ! curl -s --max-time 5 "$SKILLS_API_URL/skills?page_size=1" > /dev/null 2>&1; then
        log_warn "无法连接到 $SKILLS_API_URL，网络可能不稳定"
    else
        log_success "网络连接正常"
    fi
    
    log_success "前置检查完成"
    return 0
}

# ============== 备份 ==============
backup_openclaw() {
    if [ "$DO_BACKUP" = false ]; then
        return 0
    fi
    
    mkdir -p "$BACKUP_DIR" || {
        log_error "无法创建备份目录: $BACKUP_DIR"
        return 1
    }
    
    BACKUP_FILE="$BACKUP_DIR/openclaw.json.bak.$(date +%Y%m%d%H%M%S)"
    log "备份 openclaw.json 到: $BACKUP_FILE"
    
    if ! cp "$OPENCLAW_DIR/openclaw.json" "$BACKUP_FILE" 2>/dev/null; then
        log_error "备份失败"
        return 1
    fi
    
    log_success "备份完成"
    return 0
}

# ============== Step 1: 配置环境变量 ==============
config_environment() {
    log "Step 1: 配置环境变量 (SKILLS_API_URL)"
    
    ENV_FILE="/etc/profile"
    ENV_EXPORT="export SKILLS_API_URL=\"$SKILLS_API_URL\""
    ENV_TRACK="export DO_NOT_TRACK=1"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY-RUN] 将在 $ENV_FILE 添加:"
        log "  $ENV_EXPORT"
        log "  $ENV_TRACK"
        return 0
    fi
    
    # 检查写入权限
    if [ ! -w "$ENV_FILE" ]; then
        log_warn "无写入权限到 $ENV_FILE，跳过环境变量配置"
        log "提示: 可手动添加以下内容到 $ENV_FILE"
        log "  $ENV_EXPORT"
        log "  $ENV_TRACK"
        return 0
    fi
    
    # 备份原文件
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" "${ENV_FILE}.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
    fi
    
    # 移除旧配置
    if grep -q "export SKILLS_API_URL=" "$ENV_FILE" 2>/dev/null; then
        log_warn "移除旧 SKILLS_API_URL 配置"
        if ! grep -v "export SKILLS_API_URL=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null; then
            log_error "无法修改 $ENV_FILE"
            return 1
        fi
        mv "${ENV_FILE}.tmp" "$ENV_FILE" || {
            log_error "无法更新 $ENV_FILE"
            return 1
        }
    fi
    
    # 移除旧 DO_NOT_TRACK 配置
    if grep -q "export DO_NOT_TRACK=" "$ENV_FILE" 2>/dev/null; then
        if ! grep -v "export DO_NOT_TRACK=" "$ENV_FILE" > "${ENV_FILE}.tmp" 2>/dev/null; then
            log_error "无法修改 $ENV_FILE"
            return 1
        fi
        mv "${ENV_FILE}.tmp" "$ENV_FILE" || {
            log_error "无法更新 $ENV_FILE"
            return 1
        }
    fi
    
    # 添加新配置
    echo "" >> "$ENV_FILE"
    echo "# BI4Sight Skill Hub" >> "$ENV_FILE"
    echo "$ENV_EXPORT" >> "$ENV_FILE"
    echo "$ENV_TRACK" >> "$ENV_FILE"
    
    log_success "环境变量已配置"
    return 0
}

# ============== Step 2: 配置 openclaw-gateway systemd ==============
config_gateway_service() {
    log "Step 2: 配置 openclaw-gateway 服务环境"
    
    SYSTEMD_DIR="$HOME/.config/systemd/user/openclaw-gateway.service.d"
    SYSTEMD_FILE="$SYSTEMD_DIR/env.conf"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY-RUN] 将创建 $SYSTEMD_FILE"
        log "  Environment=\"SKILLS_API_URL=$SKILLS_API_URL\""
        log "  Environment=\"DO_NOT_TRACK=1\""
        return 0
    fi
    
    # 创建目录
    if ! mkdir -p "$SYSTEMD_DIR" 2>/dev/null; then
        log_error "无法创建 systemd 目录: $SYSTEMD_DIR"
        return 1
    fi
    
    # 备份旧配置
    if [ -f "$SYSTEMD_FILE" ]; then
        cp "$SYSTEMD_FILE" "${SYSTEMD_FILE}.bak" 2>/dev/null || true
    fi
    
    cat > "$SYSTEMD_FILE" << EOF
# BI4Sight Skill Hub Configuration
# Generated by bi4sight-skill-hub-setup.sh
# Date: $(date '+%Y-%m-%d %H:%M:%S')
[Service]
Environment="SKILLS_API_URL=${SKILLS_API_URL}"
Environment="DO_NOT_TRACK=1"
EOF
    
    if [ $? -ne 0 ]; then
        log_error "无法写入 $SYSTEMD_FILE"
        return 1
    fi
    
    log_success "Gateway 服务环境已配置"
    return 0
}

# ============== Step 3: 安装 bi4sight-skill-discovery ==============
install_bi4sight_skill_discovery() {
    log "Step 3: 安装 bi4sight-skill-discovery 多渠道搜索技能"
    
    SKILL_DIR="$WORKSPACE_SKILLS_DIR/bi4sight-skill-discovery"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY-RUN] 将在 $SKILL_DIR 安装 bi4sight-skill-discovery"
        return 0
    fi
    
    # 创建目录
    if ! mkdir -p "$SKILL_DIR/scripts" "$SKILL_DIR/references" 2>/dev/null; then
        log_error "无法创建技能目录: $SKILL_DIR"
        return 1
    fi
    
    # 检查 SKILL.md 是否存在
    if [ -f "$SKILL_DIR/SKILL.md" ]; then
        log_success "bi4sight-skill-discovery 已安装 (SKILL.md 存在)"
    else
        log_error "bi4sight-skill-discovery 未找到，请先创建 SKILL.md"
        return 1
    fi
    
    # 验证 API 连接 (带超时)
    API_TEST=$(curl -s --max-time "$CURL_TIMEOUT" -o /dev/null -w "%{http_code}" "${SKILLS_API_URL}/skills?page_size=1" 2>/dev/null || echo "000")
    if [ "$API_TEST" = "200" ]; then
        log_success "volcengine skills API 连接正常 (HTTP $API_TEST)"
    else
        log_warn "volcengine skills API 连接异常 (HTTP $API_TEST)，但技能仍可使用"
    fi
    
    return 0
}

# ============== Step 4: 安装 find-skills ==============
install_find_skills() {
    log "Step 4: 安装 find-skills 技能"
    
    SKILL_DIR="$WORKSPACE_SKILLS_DIR/find-skills"
    FIND_SKILLS_URL="https://zzl.tos-cn-beijing.volces.com/SKILL.md"
    TEMP_FILE="/tmp/find-skills-SKILL.md.$$"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY-RUN] 将从 $FIND_SKILLS_URL 安装 find-skills 到 $SKILL_DIR"
        return 0
    fi
    
    # 下载到临时文件
    log "下载 find-skills SKILL.md..."
    local download_failed=false
    
    if command -v wget &> /dev/null; then
        wget --timeout="$WGET_TIMEOUT" -q "$FIND_SKILLS_URL" -O "$TEMP_FILE" 2>/dev/null || download_failed=true
    elif command -v curl &> /dev/null; then
        curl -s --max-time "$CURL_TIMEOUT" "$FIND_SKILLS_URL" -o "$TEMP_FILE" 2>/dev/null || download_failed=true
    else
        log_error "需要 wget 或 curl 来下载 find-skills"
        return 1
    fi
    
    if [ "$download_failed" = true ] || [ ! -f "$TEMP_FILE" ] || [ ! -s "$TEMP_FILE" ]; then
        log_error "find-skills 下载失败"
        rm -f "$TEMP_FILE" 2>/dev/null
        return 1
    fi
    
    # 验证文件内容
    if ! head -c 100 "$TEMP_FILE" | grep -q "name:" 2>/dev/null; then
        log_error "下载的文件不是有效的 SKILL.md"
        rm -f "$TEMP_FILE" 2>/dev/null
        return 1
    fi
    
    # 创建目录并移动文件
    if ! mkdir -p "$SKILL_DIR" 2>/dev/null; then
        log_error "无法创建 find-skills 目录"
        rm -f "$TEMP_FILE" 2>/dev/null
        return 1
    fi
    
    # 安全移动：先备份再替换
    if [ -f "$SKILL_DIR/SKILL.md" ]; then
        cp "$SKILL_DIR/SKILL.md" "${SKILL_DIR}/SKILL.md.bak" 2>/dev/null || true
    fi
    
    mv "$TEMP_FILE" "$SKILL_DIR/SKILL.md" 2>/dev/null
    if [ $? -ne 0 ]; then
        log_error "无法安装 find-skills"
        return 1
    fi
    
    log_success "find-skills 安装完成"
    return 0
}

# ============== Step 5: 配置阿里云 agentexplorer ==============
install_aliyun_agentexplorer() {
    log "Step 5: 配置阿里云 agentexplorer"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY-RUN] 将配置阿里云 agentexplorer"
        return 0
    fi
    
    # 检查 aliyun CLI
    if ! command -v aliyun &> /dev/null; then
        log_warn "aliyun CLI 未安装，跳过阿里云配置"
        log "提示: 如需安装阿里云 CLI，请访问 https://help.aliyun.com/document_detail/121941.html"
        return 0  # 不算错误，继续执行
    fi
    
    # 检查 aliyun 版本
    ALIYUN_VERSION=$(aliyun version 2>/dev/null || echo "unknown")
    log "检测到 aliyun CLI v${ALIYUN_VERSION}"
    
    # 安装 agentexplorer 插件
    log "检查 agentexplorer 插件..."
    if aliyun plugin list 2>/dev/null | grep -q "agentexplorer"; then
        log_success "agentexplorer 插件已安装"
    else
        log "安装 agentexplorer 插件..."
        if aliyun plugin install --names agentexplorer 2>/dev/null; then
            log_success "agentexplorer 插件安装完成"
        else
            log_warn "agentexplorer 插件安装失败，尝试单独安装..."
            if aliyun plugin install --names aliyun-cli-agentexplorer 2>/dev/null; then
                log_success "agentexplorer 插件安装完成"
            else
                log_warn "agentexplorer 插件安装失败，可稍后手动安装: aliyun plugin install --names agentexplorer"
            fi
        fi
    fi
    
    # 配置 AI-Mode (不强制)
    aliyun configure ai-mode enable 2>/dev/null || true
    aliyun configure ai-mode set-user-agent --user-agent "BI4Sight/bi4sight-skill-discovery" 2>/dev/null || true
    
    log_success "阿里云 agentexplorer 配置检查完成"
    return 0
}

# ============== Step 6: 重启服务 ==============
restart_services() {
    log "Step 6: 重启 openclaw-gateway 服务"
    
    if [ "$DRY_RUN" = true ]; then
        log "[DRY-RUN] 将执行 systemctl --user daemon-reload && restart openclaw-gateway"
        return 0
    fi
    
    # 检查 systemctl 是否可用
    if ! command -v systemctl &> /dev/null; then
        log_warn "systemctl 不可用，无法自动重启服务"
        log "提示: 请手动执行以下命令重启 openclaw-gateway:"
        log "  systemctl --user daemon-reload"
        log "  systemctl --user restart openclaw-gateway"
        return 0
    fi
    
    # 尝试重启服务
    if systemctl --user daemon-reload 2>/dev/null; then
        log "服务配置已重载"
    else
        log_warn "无法执行 daemon-reload，可能不在 systemd 用户会话中"
        log "提示: 如在桌面环境，可忽略此警告"
    fi
    
    if systemctl --user restart openclaw-gateway 2>/dev/null; then
        log_success "openclaw-gateway 已重启"
    else
        log_warn "无法通过 systemctl 重启服务"
        log "提示: 请手动执行: systemctl --user restart openclaw-gateway"
    fi
    
    return 0
}

# ============== 主流程 ==============
main() {
    echo ""
    log "========================================"
    log "  BI4Sight Skill Hub Setup"
    log "========================================"
    echo ""
    
    if [ "$DRY_RUN" = true ]; then
        log "⚠️  DRY-RUN 模式：仅显示操作，不实际执行"
        echo ""
    fi
    
    # 执行前置检查
    if ! preflight_check; then
        log_error "前置检查失败，退出"
        exit 1
    fi
    echo ""
    
    # 备份
    if [ "$DO_BACKUP" = true ] && [ "$DRY_RUN" = false ]; then
        backup_openclaw
        echo ""
    fi
    
    # 执行各步骤
    config_environment
    echo ""
    
    config_gateway_service
    echo ""
    
    if [ "$INSTALL_DISCOVER" = true ]; then
        install_bi4sight_skill_discovery
        echo ""
    fi
    
    if [ "$INSTALL_FIND" = true ]; then
        install_find_skills
        echo ""
    fi
    
    if [ "$INSTALL_ALIYUN" = true ]; then
        install_aliyun_agentexplorer
        echo ""
    fi
    
    restart_services
    echo ""
    
    # 总结
    log "========================================"
    if [ "$DRY_RUN" = true ]; then
        log "  DRY-RUN 完成!"
    else
        log "  安装完成!"
    fi
    log "========================================"
    echo ""
    echo -e "${GREEN}已安装:${NC}"
    [ "$INSTALL_DISCOVER" = true ] && echo "  ✅ bi4sight-skill-discovery (多渠道搜索)"
    [ "$INSTALL_FIND" = true ] && echo "  ✅ find-skills (火山引擎仓库)"
    [ "$INSTALL_ALIYUN" = true ] && echo "  ✅ 阿里云 agentexplorer"
    echo ""
    echo -e "${GREEN}技能搜索渠道:${NC}"
    echo "  1. volcengine (私有) - https://skills.volces.com"
    echo "  2. local (本地)      - ~/.openclaw/workspace/skills/"
    echo "  3. aliyun (阿里云)    - aliyun agentexplorer"
    echo ""
    
    if [ "$HAS_ERRORS" -gt 0 ]; then
        echo -e "${RED}❌ 有 $HAS_ERRORS 个错误，请检查上述日志${NC}"
        exit 1
    elif [ "$HAS_WARNINGS" -gt 0 ]; then
        echo -e "${YELLOW}⚠️  有 $HAS_WARNINGS 个警告，但安装已完成${NC}"
    else
        echo -e "${GREEN}✅ 所有步骤成功完成!${NC}"
    fi
    
    if [ "$DRY_RUN" = false ]; then
        echo -e "${YELLOW}提示:${NC} 重启服务可能需要 30 秒生效"
    else
        echo -e "${YELLOW}提示:${NC} 这是 dry-run 模式，未执行实际安装"
    fi
}

main
