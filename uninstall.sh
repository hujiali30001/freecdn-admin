#!/bin/bash
# ==============================================================================
# FreeCDN 卸载脚本
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || error "请使用 root 用户运行"

MODE="${1:-all}"  # all | admin | node

echo -e "${RED}警告：此操作将卸载 FreeCDN 服务，数据库数据不会被删除。${NC}"
read -r -p "确认继续？[y/N] " confirm
[[ "$confirm" =~ ^[Yy]$ ]] || { info "已取消"; exit 0; }

uninstall_admin() {
  info "停止服务..."
  systemctl stop freecdn-admin freecdn-api 2>/dev/null || true
  systemctl disable freecdn-admin freecdn-api 2>/dev/null || true
  rm -f /etc/systemd/system/freecdn-admin.service
  rm -f /etc/systemd/system/freecdn-api.service
  systemctl daemon-reload
  rm -rf /usr/local/freecdn/edge-admin
  info "管理节点卸载完成"
}

uninstall_node() {
  info "停止节点服务..."
  systemctl stop freecdn-node 2>/dev/null || true
  systemctl disable freecdn-node 2>/dev/null || true
  rm -f /etc/systemd/system/freecdn-node.service
  systemctl daemon-reload
  rm -rf /usr/local/freecdn/edge-node
  info "边缘节点卸载完成"
}

case "$MODE" in
  all)   uninstall_admin; uninstall_node ;;
  admin) uninstall_admin ;;
  node)  uninstall_node ;;
  *)     error "用法: uninstall.sh [all|admin|node]" ;;
esac

warn "注意：/var/lib/freecdn 数据目录未删除，如需清理请手动执行："
warn "  rm -rf /var/lib/freecdn"
