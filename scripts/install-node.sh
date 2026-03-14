#!/usr/bin/env bash
# =============================================================================
# FreeCDN 一键安装脚本 — 边缘节点 (EdgeNode)
# 用法：
#   bash install-node.sh --api=http://ADMIN_IP:8001 --node-id=xxx --secret=xxx
#
# 参数从管理界面获取：集群 → 节点 → 详情
# =============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERR]${NC}  $*"; exit 1; }

# ── 解析参数 ──────────────────────────────────────────────────────────────────
API_ENDPOINT=""
NODE_ID=""
SECRET=""

for arg in "$@"; do
  case $arg in
    --api=*)        API_ENDPOINT="${arg#*=}" ;;
    --node-id=*)    NODE_ID="${arg#*=}" ;;
    --secret=*)     SECRET="${arg#*=}" ;;
    --help|-h)
      echo "用法: bash install-node.sh --api=http://IP:8001 --node-id=xxx --secret=xxx"
      echo ""
      echo "参数说明："
      echo "  --api       管理节点 API 地址（EdgeAPI gRPC 端口 8001）"
      echo "  --node-id   节点的 uniqueId（在管理界面：集群 → 节点详情中获取）"
      echo "  --secret    节点密钥（同上）"
      exit 0
      ;;
  esac
done

# ── 参数校验 ──────────────────────────────────────────────────────────────────
[[ $EUID -eq 0 ]] || error "请以 root 用户运行"
[[ -n "$API_ENDPOINT" ]] || error "缺少 --api 参数\n用法: bash install-node.sh --api=http://IP:8001 --node-id=xxx --secret=xxx"
[[ -n "$NODE_ID" ]]      || error "缺少 --node-id 参数（在管理界面集群→节点详情中获取 uniqueId）"
[[ -n "$SECRET" ]]       || error "缺少 --secret 参数"

# ── 配置 ──────────────────────────────────────────────────────────────────────
INSTALL_DIR="/usr/local/freecdn/edge-node-service"
RELEASE_BASE="https://github.com/TeaOSLab/EdgeNode/releases/latest/download"

ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  GO_ARCH="amd64" ;;
  aarch64) GO_ARCH="arm64" ;;
  *)       error "不支持的架构：$ARCH" ;;
esac

# ═════════════════════════════════════════════════════════════════════════════
# STEP 1: 下载 EdgeNode
# ═════════════════════════════════════════════════════════════════════════════
info "下载 EdgeNode ($GO_ARCH)..."
TARBALL="edge-node-$GO_ARCH.tar.gz"
mkdir -p "$INSTALL_DIR"
cd /tmp

if [[ ! -f "$TARBALL" ]]; then
  wget -q --show-progress -O "$TARBALL" "$RELEASE_BASE/$TARBALL" \
    || error "下载失败，请检查网络"
fi

info "解压到 $INSTALL_DIR ..."
tar -xzf "$TARBALL" -C "$INSTALL_DIR" --strip-components=1
mkdir -p "$INSTALL_DIR/configs"
success "EdgeNode 解压完成"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 2: 写入节点配置
#
# 【关键说明 - 踩坑记录】
# api_node.yaml 必须包含三个字段：
#   1. rpc.endpoints  - API 地址（http 协议，端口 8001）
#   2. nodeId         - 节点的 uniqueId（不是数字 id，是 32 位 hex 字符串）
#   3. secret         - 节点密钥
#
# 如果缺少 nodeId，edge-node 启动会报 "'nodeId' required" 并退出。
# nodeId 必须先在管理界面创建节点记录后才能获取。
# ═════════════════════════════════════════════════════════════════════════════
info "写入节点配置 api_node.yaml ..."
cat > "$INSTALL_DIR/configs/api_node.yaml" << EOF
# FreeCDN 边缘节点配置
# 由 install-node.sh 自动生成
rpc.endpoints: [ "$API_ENDPOINT" ]
nodeId: "$NODE_ID"
secret: "$SECRET"
EOF
success "配置文件已写入"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 3: 创建 systemd service
# ═════════════════════════════════════════════════════════════════════════════
info "创建 systemd service..."
cat > /etc/systemd/system/freecdn-node.service << EOF
[Unit]
Description=FreeCDN Edge Node Service
After=network.target

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/bin/edge-node
Restart=always
RestartSec=5
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable freecdn-node.service
systemctl start freecdn-node.service
success "freecdn-node.service 已启动"

# ═════════════════════════════════════════════════════════════════════════════
# STEP 4: 验证连接
# ═════════════════════════════════════════════════════════════════════════════
info "等待节点连接管理端（最多 30 秒）..."
for i in $(seq 1 6); do
  sleep 5
  STATUS=$(journalctl -u freecdn-node --no-pager -n 20 2>/dev/null || true)
  if echo "$STATUS" | grep -q "connected\|LISTENER_MANAGER"; then
    success "节点已连接！"
    break
  fi
  echo -n "."
done
echo ""

# ═════════════════════════════════════════════════════════════════════════════
# STEP 5: 输出结果
# ═════════════════════════════════════════════════════════════════════════════
SERVER_IP=$(curl -sf --max-time 5 https://api.ipify.org 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}  FreeCDN 边缘节点安装完成！${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  节点 IP：  ${BLUE}$SERVER_IP${NC}"
echo -e "  连接 API： ${BLUE}$API_ENDPOINT${NC}"
echo -e "  节点 ID：  ${YELLOW}$NODE_ID${NC}"
echo ""
echo -e "  查看日志：${BLUE}journalctl -u freecdn-node -f${NC}"
echo -e "  查看状态：${BLUE}systemctl status freecdn-node${NC}"
echo ""
echo -e "${YELLOW}  请在管理界面确认节点状态变为 isOnline=true${NC}"
echo ""
