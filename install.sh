#!/bin/bash
# ==============================================================================
# FreeCDN 一键安装脚本
#
# 用法（管理节点）：
#   curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | bash
#
# 用法（边缘节点）：
#   curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | \
#     bash -s -- --node --api-endpoint http://YOUR_ADMIN_IP:8003 \
#                --node-id YOUR_NODE_ID --node-secret YOUR_NODE_SECRET
#
# 支持系统：Ubuntu 20.04+  Debian 11+  CentOS 7/8  Rocky Linux 8+  AlmaLinux 8+
# 支持架构：linux/amd64  linux/arm64
# ==============================================================================

set -euo pipefail
IFS=$'\n\t'

# ── 颜色 ───────────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }
step()  { echo -e "\n${CYAN}${BOLD}──── $* ────${NC}"; }
ask()   { echo -e "${YELLOW}[?]${NC} $*"; }

# ── 默认参数 ───────────────────────────────────────────────────────────────────
MODE="admin"                    # admin | node
INSTALL_DIR="/usr/local/freecdn"
DATA_DIR="/var/lib/freecdn"
LOG_DIR="/var/log/freecdn"

ADMIN_HTTP_PORT="7788"
API_RPC_PORT="8003"

MYSQL_HOST="127.0.0.1"
MYSQL_PORT="3306"
MYSQL_USER="freecdn"
MYSQL_DATABASE="freecdn"
MYSQL_PASSWORD=""               # 若空则自动生成

API_ENDPOINT=""                 # node 模式必填
NODE_ID=""                      # node 模式必填
NODE_SECRET=""                  # node 模式必填

GITHUB_ORG="hujiali30001"
VERSION="latest"
SKIP_MYSQL="false"
FORCE_REINSTALL="false"

# ── 参数解析 ───────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --node)            MODE="node" ;;
    --admin)           MODE="admin" ;;
    --api-endpoint)    API_ENDPOINT="$2"; shift ;;
    --node-id)         NODE_ID="$2"; shift ;;
    --node-secret)     NODE_SECRET="$2"; shift ;;
    --admin-port)      ADMIN_HTTP_PORT="$2"; shift ;;
    --api-port)        API_RPC_PORT="$2"; shift ;;
    --mysql-host)      MYSQL_HOST="$2"; shift ;;
    --mysql-port)      MYSQL_PORT="$2"; shift ;;
    --mysql-user)      MYSQL_USER="$2"; shift ;;
    --mysql-pass)      MYSQL_PASSWORD="$2"; shift ;;
    --mysql-db)        MYSQL_DATABASE="$2"; shift ;;
    --skip-mysql)      SKIP_MYSQL="true" ;;
    --version)         VERSION="$2"; shift ;;
    --reinstall)       FORCE_REINSTALL="true" ;;
    --help|-h)
      cat <<EOF
FreeCDN 一键安装脚本

用法:
  install.sh [选项]

模式:
  --admin          安装管理节点（默认）
  --node           安装边缘节点

边缘节点必填:
  --api-endpoint   管理节点 API 地址，如 http://1.2.3.4:8003
  --node-id        节点 ID（从管理后台获取）
  --node-secret    节点密钥（从管理后台获取）

可选参数:
  --admin-port     管理后台端口（默认 7788）
  --api-port       API RPC 端口（默认 8003）
  --mysql-host     MySQL 地址（默认 127.0.0.1）
  --mysql-pass     MySQL 密码（默认自动生成）
  --skip-mysql     跳过 MySQL 安装（自行管理数据库时使用）
  --version        指定版本，如 v1.0.0（默认 latest）
  --reinstall      强制重新安装（覆盖现有安装）
EOF
      exit 0
      ;;
    *) warn "未知参数: $1，忽略" ;;
  esac
  shift
done

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${CYAN}"
cat << 'BANNER'
  ___               ____ ____  _   _
 |  _|_ __ ___  ___|  _ \___ \| \ | |
 | |_| '__/ _ \/ _ \ |_) |__) |  \| |
 |  _| | |  __/  __/  __// __/| |\  |
 |_| |_|  \___|\___|_|  |_____|_| \_|
BANNER
echo -e "${NC}"
echo -e "  ${BOLD}FreeCDN 一键安装程序${NC}  |  模式: ${GREEN}${MODE}${NC}"
echo ""

# ── 环境检查 ──────────────────────────────────────────────────────────────────
step "检查运行环境"

[ "$(id -u)" -eq 0 ] || error "请使用 root 用户运行（sudo bash 或 sudo su -）"

# 架构检测
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  ARCH_TAG="amd64" ;;
  aarch64) ARCH_TAG="arm64" ;;
  *)       error "不支持的 CPU 架构: $ARCH（仅支持 x86_64 / aarch64）" ;;
esac
info "CPU 架构: $ARCH_TAG"

# 系统检测
if [ -f /etc/os-release ]; then
  . /etc/os-release
  OS_NAME="${NAME:-unknown}"
  OS_VERSION="${VERSION_ID:-0}"
else
  OS_NAME="unknown"
  OS_VERSION="0"
fi
info "操作系统: ${OS_NAME} ${OS_VERSION}"

# 包管理器
if command -v apt-get &>/dev/null; then
  PKG_MANAGER="apt"
elif command -v dnf &>/dev/null; then
  PKG_MANAGER="dnf"
elif command -v yum &>/dev/null; then
  PKG_MANAGER="yum"
else
  PKG_MANAGER="unknown"
  warn "未知包管理器，跳过依赖安装"
fi
info "包管理器: ${PKG_MANAGER}"

# node 模式必填参数校验
if [ "$MODE" = "node" ]; then
  [ -n "$API_ENDPOINT" ] || error "边缘节点安装必须指定 --api-endpoint，如：--api-endpoint http://1.2.3.4:8003"
  [ -n "$NODE_ID" ]      || error "边缘节点安装必须指定 --node-id"
  [ -n "$NODE_SECRET" ]  || error "边缘节点安装必须指定 --node-secret"
fi

# ── 安装依赖 ──────────────────────────────────────────────────────────────────
step "安装系统依赖"

install_pkg() {
  case "$PKG_MANAGER" in
    apt) apt-get install -y -qq "$@" ;;
    dnf) dnf install -y -q "$@" ;;
    yum) yum install -y -q "$@" ;;
    *)   warn "请手动安装: $*" ;;
  esac
}

case "$PKG_MANAGER" in
  apt) apt-get update -qq ;;
  dnf) dnf makecache -q ;;
  yum) yum makecache -q ;;
esac

install_pkg curl wget tar gzip
info "依赖安装完成"

# ── MySQL 安装（仅 admin 模式）────────────────────────────────────────────────
if [ "$MODE" = "admin" ] && [ "$SKIP_MYSQL" = "false" ]; then
  step "安装 MySQL"
  if command -v mysqladmin &>/dev/null; then
    info "MySQL 已安装（$(mysqladmin --version 2>/dev/null | head -1 || echo 'version unknown')），跳过"
  else
    info "正在安装 MySQL 8.0..."
    case "$PKG_MANAGER" in
      apt)
        DEBIAN_FRONTEND=noninteractive install_pkg mysql-server
        ;;
      dnf|yum)
        # CentOS/Rocky: 使用 MySQL 官方仓库
        if ! rpm -qa | grep -q mysql-community; then
          MYSQL_REPO_URL="https://dev.mysql.com/get/mysql80-community-release-el$(rpm -E '%{rhel}')-1.noarch.rpm"
          wget -q "$MYSQL_REPO_URL" -O /tmp/mysql-repo.rpm && rpm -ivh /tmp/mysql-repo.rpm 2>/dev/null || true
          $PKG_MANAGER install -y -q mysql-community-server
        fi
        ;;
    esac
    systemctl enable --now mysql 2>/dev/null || systemctl enable --now mysqld 2>/dev/null || true
    info "MySQL 安装完成"
  fi

  # 生成密码（若未指定）
  if [ -z "$MYSQL_PASSWORD" ]; then
    MYSQL_PASSWORD=$(tr -dc 'A-Za-z0-9@#%' < /dev/urandom | head -c 20)
    MYSQL_PASSWORD_GENERATED="true"
  else
    MYSQL_PASSWORD_GENERATED="false"
  fi

  # 创建数据库和用户
  info "创建数据库: ${MYSQL_DATABASE}"
  # Ubuntu MySQL 默认用 auth_socket，必须通过 sudo 调用
  MYSQL_EXEC="sudo mysql -u root"
  $MYSQL_EXEC 2>/dev/null <<SQL || warn "数据库/用户可能已存在，跳过创建"
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'${MYSQL_HOST}' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'${MYSQL_HOST}';
FLUSH PRIVILEGES;
SQL
  info "数据库配置完成（用户: ${MYSQL_USER}）"
fi

# ── 下载二进制 ────────────────────────────────────────────────────────────────
step "下载 FreeCDN 二进制"

# 构造下载 URL
# 优先从 GitHub Releases，fallback 到 GoEdge 官方
get_download_url() {
  local component="$1"  # admin | api | node
  local arch="$2"
  # GitHub Releases 格式（未来发布 Release 后生效）
  local repo
  case "$component" in
    admin) repo="${GITHUB_ORG}/freecdn-admin" ;;
    api)   repo="${GITHUB_ORG}/freecdn-api" ;;
    node)  repo="${GITHUB_ORG}/freecdn-node" ;;
  esac

  if [ "$VERSION" = "latest" ]; then
    local ver
    ver=$(curl -sf "https://api.github.com/repos/${repo}/releases/latest" \
          | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/')
    [ -n "$ver" ] && VERSION="$ver" || true
  fi

  if [ -n "$VERSION" ] && [ "$VERSION" != "latest" ]; then
    echo "https://github.com/${repo}/releases/download/${VERSION}/freecdn-${component}-linux-${arch}.tar.gz"
  else
    # Fallback: GoEdge 官方打包（编译版）
    case "$component" in
      admin) echo "https://dl.goedge.cloud/edge-admin/linux/${arch}/edge-admin.tar.gz" ;;
      api)   echo "https://dl.goedge.cloud/edge-api/linux/${arch}/edge-api.tar.gz" ;;
      node)  echo "https://dl.goedge.cloud/edge-node/linux/${arch}/edge-node.tar.gz" ;;
    esac
  fi
}

# 通用下载函数，优先 GitHub 失败则 GoEdge fallback
download_and_extract() {
  local component="$1"
  local dest_dir="$2"
  local url
  url=$(get_download_url "$component" "$ARCH_TAG")
  local tmp_file="/tmp/freecdn-${component}.tar.gz"

  info "下载 ${component}..."
  if wget -q --show-progress --timeout=60 "$url" -O "$tmp_file" 2>/dev/null; then
    info "从 GitHub Releases 下载成功"
  else
    warn "GitHub Releases 不可用，从 GoEdge 官方下载..."
    local fallback_url
    case "$component" in
      admin) fallback_url="https://dl.goedge.cloud/edge-admin/linux/${ARCH_TAG}/edge-admin.tar.gz" ;;
      api)   fallback_url="https://dl.goedge.cloud/edge-api/linux/${ARCH_TAG}/edge-api.tar.gz" ;;
      node)  fallback_url="https://dl.goedge.cloud/edge-node/linux/${ARCH_TAG}/edge-node.tar.gz" ;;
    esac
    wget -q --show-progress --timeout=60 "$fallback_url" -O "$tmp_file" \
      || error "下载 ${component} 失败，请检查网络"
    USING_GOEDGE_ORIGINAL="true"
  fi

  mkdir -p "$dest_dir"
  tar -xzf "$tmp_file" -C "$dest_dir" --strip-components=1 2>/dev/null \
    || tar -xzf "$tmp_file" -C "$dest_dir" 2>/dev/null \
    || error "解压 ${component} 失败"
  rm -f "$tmp_file"
  info "${component} 解压完成"
}

# ── 创建目录 ──────────────────────────────────────────────────────────────────
step "创建目录结构"

if [ "$MODE" = "admin" ]; then
  ADMIN_DIR="${INSTALL_DIR}/edge-admin"
  API_DIR="${ADMIN_DIR}/edge-api"
  mkdir -p "${ADMIN_DIR}/bin" "${ADMIN_DIR}/configs" "${ADMIN_DIR}/web" "${ADMIN_DIR}/logs"
  mkdir -p "${API_DIR}/bin" "${API_DIR}/configs" "${API_DIR}/logs" "${API_DIR}/data"
  mkdir -p "${DATA_DIR}" "${LOG_DIR}"
  info "目录创建: ${ADMIN_DIR}"
else
  NODE_DIR="${INSTALL_DIR}/edge-node"
  mkdir -p "${NODE_DIR}/bin" "${NODE_DIR}/configs" "${NODE_DIR}/logs"
  mkdir -p "${DATA_DIR}/node/caches"
  info "目录创建: ${NODE_DIR}"
fi

USING_GOEDGE_ORIGINAL="false"

# ── 下载并安装 ────────────────────────────────────────────────────────────────
if [ "$MODE" = "admin" ]; then
  download_and_extract "admin" "/tmp/freecdn-admin-src"
  download_and_extract "api"   "/tmp/freecdn-api-src"

  # 复制 admin 二进制和 web 资源
  find /tmp/freecdn-admin-src -name "edge-admin" -type f -exec cp {} "${ADMIN_DIR}/bin/edge-admin" \; 2>/dev/null || true
  [ ! -f "${ADMIN_DIR}/bin/edge-admin" ] && cp /tmp/freecdn-admin-src/edge-admin "${ADMIN_DIR}/bin/edge-admin" 2>/dev/null || true
  chmod +x "${ADMIN_DIR}/bin/edge-admin"

  # 复制 web 静态资源
  if [ -d /tmp/freecdn-admin-src/web ]; then
    cp -r /tmp/freecdn-admin-src/web/. "${ADMIN_DIR}/web/"
  fi

  # 复制 api 二进制
  find /tmp/freecdn-api-src -name "edge-api" -type f -exec cp {} "${API_DIR}/bin/edge-api" \; 2>/dev/null || true
  [ ! -f "${API_DIR}/bin/edge-api" ] && cp /tmp/freecdn-api-src/edge-api "${API_DIR}/bin/edge-api" 2>/dev/null || true
  chmod +x "${API_DIR}/bin/edge-api"

  rm -rf /tmp/freecdn-admin-src /tmp/freecdn-api-src
  info "二进制安装完成"

else
  download_and_extract "node" "/tmp/freecdn-node-src"
  find /tmp/freecdn-node-src -name "edge-node" -type f -exec cp {} "${NODE_DIR}/bin/edge-node" \; 2>/dev/null || true
  [ ! -f "${NODE_DIR}/bin/edge-node" ] && cp /tmp/freecdn-node-src/edge-node "${NODE_DIR}/bin/edge-node" 2>/dev/null || true
  chmod +x "${NODE_DIR}/bin/edge-node"
  rm -rf /tmp/freecdn-node-src
  info "边缘节点二进制安装完成"
fi

# ── 写配置文件（admin 模式）──────────────────────────────────────────────────
if [ "$MODE" = "admin" ]; then
  step "生成配置文件"

  # edge-admin: server.yaml
  cat > "${ADMIN_DIR}/configs/server.yaml" <<YAML
# FreeCDN 管理后台配置
http:
  listen:
    - ${ADMIN_HTTP_PORT}
YAML

  # edge-admin: api_admin.yaml（连接 edge-api）
  cat > "${ADMIN_DIR}/configs/api_admin.yaml" <<YAML
# FreeCDN API 连接配置
endpoints:
  - "127.0.0.1:${API_RPC_PORT}"
secret: ""
YAML

  # edge-api: db.yaml（数据库连接）
  cat > "${API_DIR}/configs/db.yaml" <<YAML
# FreeCDN 数据库配置
dbs:
  - driver: mysql
    dsn: "${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_PORT})/${MYSQL_DATABASE}?charset=utf8mb4&parseTime=true&loc=Local"
    prefix: "edge"
    tablePrefix: "edge_"
YAML

  info "配置文件生成完成"
fi

# ── 写配置文件（node 模式）───────────────────────────────────────────────────
if [ "$MODE" = "node" ]; then
  step "生成节点配置文件"

  cat > "${NODE_DIR}/configs/api_node.yaml" <<YAML
# FreeCDN 节点配置
endpoints:
  - "${API_ENDPOINT}"
nodeId: "${NODE_ID}"
secret: "${NODE_SECRET}"
YAML

  info "节点配置文件生成完成"
fi

# ── 创建 systemd 服务 ─────────────────────────────────────────────────────────
step "注册系统服务"

if [ "$MODE" = "admin" ]; then
  # edge-api 服务
  cat > /etc/systemd/system/freecdn-api.service <<SERVICE
[Unit]
Description=FreeCDN API Service
Documentation=https://github.com/hujiali30001/freecdn-api
After=network.target mysql.service mysqld.service
Wants=mysql.service mysqld.service

[Service]
Type=simple
WorkingDirectory=${API_DIR}
ExecStart=${API_DIR}/bin/edge-api
Restart=always
RestartSec=5
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal
SyslogIdentifier=freecdn-api

[Install]
WantedBy=multi-user.target
SERVICE

  # edge-admin 服务（依赖 edge-api）
  cat > /etc/systemd/system/freecdn-admin.service <<SERVICE
[Unit]
Description=FreeCDN Admin Service
Documentation=https://github.com/hujiali30001/freecdn-admin
After=network.target freecdn-api.service
Requires=freecdn-api.service

[Service]
Type=simple
WorkingDirectory=${ADMIN_DIR}
ExecStart=${ADMIN_DIR}/bin/edge-admin
Restart=always
RestartSec=5
LimitNOFILE=65535
StandardOutput=journal
StandardError=journal
SyslogIdentifier=freecdn-admin

[Install]
WantedBy=multi-user.target
SERVICE

  systemctl daemon-reload
  systemctl enable freecdn-api freecdn-admin
  info "服务注册完成: freecdn-api, freecdn-admin"

else
  cat > /etc/systemd/system/freecdn-node.service <<SERVICE
[Unit]
Description=FreeCDN Edge Node
Documentation=https://github.com/hujiali30001/freecdn-node
After=network.target

[Service]
Type=simple
WorkingDirectory=${NODE_DIR}
ExecStart=${NODE_DIR}/bin/edge-node
Restart=always
RestartSec=5
LimitNOFILE=1000000
AmbientCapabilities=CAP_NET_BIND_SERVICE
StandardOutput=journal
StandardError=journal
SyslogIdentifier=freecdn-node

[Install]
WantedBy=multi-user.target
SERVICE

  systemctl daemon-reload
  systemctl enable freecdn-node
  info "服务注册完成: freecdn-node"
fi

# ── 启动服务 ──────────────────────────────────────────────────────────────────
step "启动服务"

if [ "$MODE" = "admin" ]; then
  systemctl start freecdn-api
  sleep 2
  systemctl start freecdn-admin
  sleep 2

  # 健康检查
  if systemctl is-active --quiet freecdn-api && systemctl is-active --quiet freecdn-admin; then
    info "服务启动成功"
  else
    warn "服务可能未完全启动，请检查日志："
    warn "  journalctl -u freecdn-api -n 20"
    warn "  journalctl -u freecdn-admin -n 20"
  fi
else
  systemctl start freecdn-node
  sleep 2
  if systemctl is-active --quiet freecdn-node; then
    info "边缘节点启动成功"
  else
    warn "边缘节点可能未启动，请检查日志：journalctl -u freecdn-node -n 20"
  fi
fi

# ── 获取服务器 IP ─────────────────────────────────────────────────────────────
SERVER_IP=$(curl -4sf --connect-timeout 5 https://api.ipify.org 2>/dev/null \
         || curl -4sf --connect-timeout 5 https://ifconfig.me 2>/dev/null \
         || hostname -I | awk '{print $1}' \
         || echo "YOUR_SERVER_IP")

# ── 完成提示 ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
if [ "$MODE" = "admin" ]; then
  echo -e "${GREEN}${BOLD}  FreeCDN 管理节点安装完成！${NC}"
  echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
  echo ""
  echo -e "  管理后台地址:  ${CYAN}http://${SERVER_IP}:${ADMIN_HTTP_PORT}${NC}"
  echo -e "  API RPC 端口:  ${CYAN}${SERVER_IP}:${API_RPC_PORT}${NC}（边缘节点连接用）"
  echo ""
  echo -e "  ${BOLD}下一步：${NC}"
  echo "  1. 在浏览器访问管理后台，完成安装向导"
  echo "  2. 向导中填入数据库信息："
  echo -e "     主机: ${MYSQL_HOST}  端口: ${MYSQL_PORT}"
  echo -e "     数据库: ${MYSQL_DATABASE}  用户: ${MYSQL_USER}"
  if [ "${MYSQL_PASSWORD_GENERATED:-false}" = "true" ]; then
    echo -e "     密码: ${YELLOW}${MYSQL_PASSWORD}${NC}  ← 请记录此密码"
  fi
  echo "  3. 向导完成后，在「节点管理」中添加边缘节点"
  echo "  4. 在边缘节点服务器上运行节点安装命令（管理后台会生成）"
  echo ""
  echo -e "  ${BOLD}常用命令：${NC}"
  echo "  查看状态:  systemctl status freecdn-admin freecdn-api"
  echo "  查看日志:  journalctl -u freecdn-admin -f"
  echo "  重启服务:  systemctl restart freecdn-api freecdn-admin"
  echo "  停止服务:  systemctl stop freecdn-admin freecdn-api"

  if [ "$USING_GOEDGE_ORIGINAL" = "true" ]; then
    echo ""
    warn "注意：本次使用了 GoEdge 原版二进制（FreeCDN Release 尚未发布）"
    warn "功能完全一致，品牌文字可能显示 GoEdge。"
  fi
else
  echo -e "${GREEN}${BOLD}  FreeCDN 边缘节点安装完成！${NC}"
  echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
  echo ""
  echo -e "  节点 ID:    ${CYAN}${NODE_ID}${NC}"
  echo -e "  API 端点:   ${CYAN}${API_ENDPOINT}${NC}"
  echo ""
  echo -e "  ${BOLD}常用命令：${NC}"
  echo "  查看状态:  systemctl status freecdn-node"
  echo "  查看日志:  journalctl -u freecdn-node -f"
  echo "  重启节点:  systemctl restart freecdn-node"
fi

echo ""
echo -e "  ${BOLD}安装路径:${NC} ${INSTALL_DIR}"
echo -e "  ${BOLD}文档:${NC}     https://github.com/hujiali30001/freecdn-admin"
echo ""
