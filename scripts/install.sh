#!/usr/bin/env bash
# =============================================================================
# FreeCDN 一键安装脚本 — 管理节点 (EdgeAdmin + EdgeAPI)
# 适用系统：Ubuntu 20.04 / 22.04 / Debian 11+
# 用法：curl -fsSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/scripts/install.sh | bash
# =============================================================================
set -euo pipefail

# ── 颜色 ──────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

# ── 配置 ──────────────────────────────────────────────────────────────────────
INSTALL_DIR="/usr/local/freecdn"
ADMIN_DIR="$INSTALL_DIR/edge-admin-service"
ADMIN_PORT="${ADMIN_PORT:-7788}"
RELEASE_BASE="https://github.com/TeaOSLab/EdgeAdmin/releases/latest/download"
# 如果环境变量未设置，使用默认版本（脚本维护者更新此处）
ADMIN_VERSION="${FREECDN_VERSION:-v1.3.9}"

# ── 检查 root ─────────────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || error "请以 root 用户运行，或使用 sudo bash install.sh"

# ── 检测架构 ──────────────────────────────────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  GO_ARCH="amd64" ;;
  aarch64) GO_ARCH="arm64" ;;
  *)       error "不支持的架构：$ARCH" ;;
esac
info "系统架构：$ARCH ($GO_ARCH)"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1: 安装依赖
# ═════════════════════════════════════════════════════════════════════════════
info "安装系统依赖..."
apt-get update -qq
apt-get install -y -qq curl wget tar sqlite3 jq 2>/dev/null || true
success "依赖安装完成"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2: 下载 EdgeAdmin（包含 EdgeAPI，官方打包在一起）
# ═════════════════════════════════════════════════════════════════════════════
info "下载 EdgeAdmin $ADMIN_VERSION ($GO_ARCH)..."
TARBALL="edge-admin-$GO_ARCH.tar.gz"
DOWNLOAD_URL="$RELEASE_BASE/$TARBALL"

mkdir -p "$ADMIN_DIR"
cd /tmp

if [[ ! -f "$TARBALL" ]]; then
  wget -q --show-progress -O "$TARBALL" "$DOWNLOAD_URL" \
    || error "下载失败：$DOWNLOAD_URL\n请检查网络或手动下载后放到 /tmp/$TARBALL"
fi

info "解压到 $ADMIN_DIR ..."
tar -xzf "$TARBALL" -C "$ADMIN_DIR" --strip-components=1
success "EdgeAdmin 解压完成"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3: 初始化数据库（SQLite，community 版本）
# ═════════════════════════════════════════════════════════════════════════════
info "初始化数据目录..."
mkdir -p "$ADMIN_DIR/data"

# community 版本使用 SQLite，无需额外配置
if [[ ! -f "$ADMIN_DIR/data/db.db" ]]; then
  info "首次启动，将自动初始化 SQLite 数据库"
fi

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4: 创建 systemd service（只创建 edge-admin，不单独创建 edge-api）
#
# 【关键说明 - 踩坑记录】
# EdgeAdmin 进程会自动以子进程方式启动 EdgeAPI（内嵌管理）。
# 如果额外创建独立的 edge-api.service，会导致端口 8001 冲突，
# edge-api 进程无限崩溃重启（本次安装故意不创建 edge-api.service）。
# ═════════════════════════════════════════════════════════════════════════════
info "创建 systemd service..."
cat > /etc/systemd/system/freecdn-admin.service << EOF
[Unit]
Description=FreeCDN Admin Service (EdgeAdmin + EdgeAPI)
After=network.target
# 注意：不要单独创建 edge-api.service，EdgeAPI 由 EdgeAdmin 作为子进程管理

[Service]
Type=simple
WorkingDirectory=$ADMIN_DIR
ExecStart=$ADMIN_DIR/bin/edge-admin
Restart=always
RestartSec=5
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 如果旧版本误创建了 edge-api.service，禁用它
if systemctl list-unit-files | grep -q "freecdn-api.service\|edge-api.service"; then
  warn "检测到独立 edge-api.service，正在禁用（避免端口冲突）..."
  systemctl stop freecdn-api.service edge-api.service 2>/dev/null || true
  systemctl disable freecdn-api.service edge-api.service 2>/dev/null || true
  success "已禁用独立 edge-api.service"
fi

systemctl daemon-reload
systemctl enable freecdn-admin.service
systemctl start freecdn-admin.service
success "freecdn-admin.service 已启动"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5: 等待服务就绪
# ═════════════════════════════════════════════════════════════════════════════
info "等待服务启动（最多 60 秒）..."
for i in $(seq 1 12); do
  if curl -sf "http://127.0.0.1:$ADMIN_PORT/" > /dev/null 2>&1; then
    success "管理界面已就绪"
    break
  fi
  sleep 5
  echo -n "."
done
echo ""

# ═════════════════════════════════════════════════════════════════════════════
# STEP 6: 输出安装结果
# ═════════════════════════════════════════════════════════════════════════════
SERVER_IP=$(curl -sf --max-time 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  FreeCDN 管理节点安装完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  管理界面：${BLUE}http://$SERVER_IP:$ADMIN_PORT${NC}"
echo -e "  默认账号：${YELLOW}admin${NC}"
echo -e "  默认密码：${YELLOW}请查看首次启动日志获取随机密码${NC}"
echo ""
echo -e "  查看密码：${BLUE}journalctl -u freecdn-admin --no-pager | grep -i password${NC}"
echo -e "  查看日志：${BLUE}journalctl -u freecdn-admin -f${NC}"
echo ""
echo -e "${YELLOW}  下一步：安装边缘节点${NC}"
echo -e "  在管理界面创建集群和节点后，在边缘服务器运行："
echo -e "  ${BLUE}bash <(curl -fsSL .../install-node.sh) --node-id=xxx --secret=xxx --api=http://$SERVER_IP:8001${NC}"
echo ""
