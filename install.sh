#!/bin/bash
# ==============================================================================
# FreeCDN 一键安装脚本
#
# 用法（管理节点）：
#   curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | bash
#
# 用法（边缘节点）：
#   curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | \
#     bash -s -- --node --api-endpoint http://YOUR_ADMIN_IP:8003 \
#                --node-id YOUR_NODE_ID --node-secret YOUR_NODE_SECRET
#
# 如果镜像站不可用，改用 GitHub 直连：
#   curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | bash
#
# 支持系统：Ubuntu 20.04+  Debian 11+  CentOS 7/8  Rocky Linux 8+  AlmaLinux 8+
# 支持架构：linux/amd64  linux/arm64
# ==============================================================================

# ── CRLF 自检（镜像站可能注入 \r，导致 bash 解析失败）──────────────────────────
# 如果当前脚本含有 \r，说明被 CRLF 污染，自动用 tr 清理后重新执行
if cat "$0" 2>/dev/null | grep -qP '\r'; then
  CLEAN=$(mktemp /tmp/freecdn_install_XXXX.sh)
  tr -d '\r' < "$0" > "$CLEAN"
  chmod +x "$CLEAN"
  exec bash "$CLEAN" "$@"
fi

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
MYSQL_PASSWORD_GENERATED="false"
SKIP_MYSQL="false"              # 必须在这里初始化，避免 set -u 报错

API_ENDPOINT=""                 # node 模式必填
NODE_ID=""                      # node 模式必填
NODE_SECRET=""                  # node 模式必填

FREECDN_VERSION="v0.9.0"        # FreeCDN 自己的 Release 版本
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
    --version|--freecdn-version) FREECDN_VERSION="$2"; shift ;;
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
  --node-id        节点 uniqueId（在管理后台「集群 → 节点 → 添加节点」后获取）
  --node-secret    节点 secret（同上，添加节点时生成）

可选参数:
  --admin-port     管理后台端口（默认 7788）
  --api-port       API RPC 端口（默认 8003）
  --mysql-host     MySQL 地址（默认 127.0.0.1）
  --mysql-pass     MySQL 密码（默认自动生成）
  --skip-mysql     跳过 MySQL 安装（自行管理数据库时使用）
  --version        指定 FreeCDN Release 版本（默认 v0.2.0）
  --freecdn-version 同 --version
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

[ "$(id -u)" -eq 0 ] || error "请使用 root 用户运行（sudo bash 或 sudo -i）"

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
    apt) DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "$@" ;;
    dnf) dnf install -y -q "$@" ;;
    yum) yum install -y -q "$@" ;;
    *)   warn "请手动安装: $*" ;;
  esac
}

case "$PKG_MANAGER" in
  apt) apt-get update -qq ;;
  dnf) dnf makecache -q 2>/dev/null || true ;;
  yum) yum makecache -q 2>/dev/null || true ;;
esac

install_pkg curl wget tar gzip unzip
info "依赖安装完成"

# ── MySQL 安装（仅 admin 模式）────────────────────────────────────────────────
if [ "$MODE" = "admin" ] && [ "$SKIP_MYSQL" = "false" ]; then
  step "安装 MySQL"
  MYSQL_ROOT_OPT=""   # 默认无密码（Ubuntu auth_socket）
  if command -v mysqladmin &>/dev/null && mysqladmin ping --silent 2>/dev/null; then
    info "MySQL 已安装且正在运行，跳过"
  else
    info "正在安装 MySQL 8.0..."
    case "$PKG_MANAGER" in
      apt)
        DEBIAN_FRONTEND=noninteractive install_pkg mysql-server
        ;;
      dnf|yum)
        # CentOS/Rocky：使用 MySQL 官方仓库
        if ! rpm -qa 2>/dev/null | grep -q mysql-community; then
          RHEL_VER=$(rpm -E '%{rhel}' 2>/dev/null || echo "8")
          MYSQL_REPO_URL="https://dev.mysql.com/get/mysql80-community-release-el${RHEL_VER}-1.noarch.rpm"
          wget -q "$MYSQL_REPO_URL" -O /tmp/mysql-repo.rpm \
            && rpm -ivh /tmp/mysql-repo.rpm 2>/dev/null || true
          $PKG_MANAGER install -y -q mysql-community-server
        fi
        ;;
    esac
    # 兼容 Ubuntu（mysql）和 CentOS（mysqld）
    systemctl enable --now mysql 2>/dev/null \
      || systemctl enable --now mysqld 2>/dev/null \
      || true
    info "MySQL 安装完成"

    # CentOS/Rocky 的 MySQL 8 首次启动会在日志里生成临时 root 密码。
    # 必须用临时密码登录并重置后才能无密码操作，否则后续 `mysql -u root` 会失败。
    if [ "$PKG_MANAGER" != "apt" ]; then
      MYSQL_TMP_PWD=$(grep -oP '(?<=temporary password is: )\S+' \
        /var/log/mysqld.log 2>/dev/null | tail -1 || true)
      if [ -n "$MYSQL_TMP_PWD" ]; then
        info "检测到 MySQL 临时密码，正在重置为随机密码..."
        set +o pipefail
        ROOT_TMP=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 20)
        set -o pipefail
        mysql -u root -p"${MYSQL_TMP_PWD}" --connect-expired-password 2>/dev/null <<SQL || true
ALTER USER 'root'@'localhost' IDENTIFIED BY '${ROOT_TMP}';
SQL
        MYSQL_ROOT_OPT="-p${ROOT_TMP}"
        info "MySQL root 密码已重置"
      fi
    fi
  fi

  # 生成密码（若未指定）
  if [ -z "$MYSQL_PASSWORD" ]; then
    # 注意：tr | head 组合在 pipefail 模式下会因 SIGPIPE 退出
    # 需要临时关闭 pipefail
    set +o pipefail
    MYSQL_PASSWORD=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 20)
    set -o pipefail
    MYSQL_PASSWORD_GENERATED="true"
  fi

  # 创建数据库和用户
  # 脚本以 root 运行，Ubuntu MySQL 默认允许 root 无密码本地登录
  #
  # 注意：同时创建 'freecdn'@'localhost' 和 'freecdn'@'127.0.0.1' 两个用户。
  # 原因：MySQL 中 'localhost' 走 Unix socket，'127.0.0.1' 走 TCP，
  #       edge-api upgrade 使用 DSN tcp(127.0.0.1:3306) 走 TCP，
  #       但某些工具或 MySQL 版本可能仍然通过 socket 连接匹配 'localhost'。
  #       同时授权两个 host 可以完全规避此问题。
  info "创建数据库: ${MYSQL_DATABASE}"
  MYSQL_CREATE_ERR=$(mysql -u root ${MYSQL_ROOT_OPT} 2>&1 <<SQL
CREATE DATABASE IF NOT EXISTS \`${MYSQL_DATABASE}\`
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'127.0.0.1' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'localhost';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL
) || true
  if [ -n "$MYSQL_CREATE_ERR" ]; then
    # 过滤已存在的警告（正常情况），只显示真正的错误
    REAL_ERR=$(echo "$MYSQL_CREATE_ERR" | grep -v "^$" | grep -vi "already exists" | grep -vi "Warning" || true)
    if [ -n "$REAL_ERR" ]; then
      warn "数据库初始化有警告: $REAL_ERR"
    else
      info "数据库/用户已存在，继续（密码已更新）"
    fi
  fi
  # 确保密码一致（即使用户已存在）
  mysql -u root ${MYSQL_ROOT_OPT} 2>/dev/null <<SQL || true
ALTER USER '${MYSQL_USER}'@'localhost' IDENTIFIED BY '${MYSQL_PASSWORD}';
ALTER USER '${MYSQL_USER}'@'127.0.0.1' IDENTIFIED BY '${MYSQL_PASSWORD}';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'localhost';
GRANT ALL PRIVILEGES ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL
  info "数据库配置完成（用户: ${MYSQL_USER}）"
fi

# ── 下载 URL 函数 ─────────────────────────────────────────────────────────────
# 下载优先级（仅 FreeCDN 官方 Release，不再依赖 GoEdge）：
#   1. 快速探测各镜像站速度，选最快的下载
#   2. 若探测均失败，依次逐一尝试所有镜像
#   3. 若全部失败，提示用户手动下载
#
# FreeCDN Release 包命名规则：
#   freecdn-v0.6.0-linux-amd64.tar.gz

GITHUB_REPO="hujiali30001/freecdn-admin"
RELEASE_FILE="freecdn-${FREECDN_VERSION}-linux-${ARCH_TAG}.tar.gz"
GITHUB_RELEASE_PATH="releases/download/${FREECDN_VERSION}/${RELEASE_FILE}"

# GitHub 镜像站列表（国内常用，实测优先级排序）
# gh-proxy.com 实测腾讯云广州约 1.6MB/s，排第一；ghfast.top 约 150KB/s 排第二兜底
GITHUB_MIRRORS=(
  "https://gh-proxy.com/https://github.com/${GITHUB_REPO}/${GITHUB_RELEASE_PATH}"
  "https://ghfast.top/https://github.com/${GITHUB_REPO}/${GITHUB_RELEASE_PATH}"
  "https://hub.gitmirror.com/https://github.com/${GITHUB_REPO}/${GITHUB_RELEASE_PATH}"
  "https://mirror.ghproxy.com/https://github.com/${GITHUB_REPO}/${GITHUB_RELEASE_PATH}"
  "https://github.com/${GITHUB_REPO}/${GITHUB_RELEASE_PATH}"
)

# 探测最快的镜像站：
# 策略：下载前 128KB 计算实际速度（bytes/s），选速度最快的；
# 若全部探测失败则返回空串，调用方将按列表顺序逐一尝试。
pick_fastest_mirror() {
  local best_url="" best_speed=0
  for url in "${GITHUB_MIRRORS[@]}"; do
    # 下载最多 128KB，限时 8 秒，取实际下载速度
    local speed
    speed=$(curl -L -o /dev/null -sS --max-time 8 --max-filesize 131072 \
      -w "%{speed_download}" "$url" 2>/dev/null || echo "0")
    # 去掉小数点（bash 不支持浮点比较）
    local sp_int=${speed%%.*}
    sp_int=$((${sp_int:-0}))
    if [ "$sp_int" -gt "$best_speed" ]; then
      best_speed=$sp_int
      best_url=$url
    fi
  done
  # 速度太低（<10KB/s）视为无效
  if [ "$best_speed" -lt 10240 ]; then
    echo ""
  else
    echo "$best_url"
  fi
}

# ── 创建目录 ──────────────────────────────────────────────────────────────────
step "创建目录结构"

if [ "$MODE" = "admin" ]; then
  ADMIN_DIR="${INSTALL_DIR}/edge-admin"
  API_DIR="${ADMIN_DIR}/edge-api"
  mkdir -p "${ADMIN_DIR}/bin" "${ADMIN_DIR}/configs" "${ADMIN_DIR}/web" "${ADMIN_DIR}/logs"
  mkdir -p "${API_DIR}/bin" "${API_DIR}/configs" "${API_DIR}/logs" "${API_DIR}/data"
  mkdir -p "${DATA_DIR}" "${LOG_DIR}"
  info "目录创建完成: ${ADMIN_DIR}"
else
  NODE_DIR="${INSTALL_DIR}/edge-node"
  mkdir -p "${NODE_DIR}/bin" "${NODE_DIR}/configs" "${NODE_DIR}/logs"
  mkdir -p "${DATA_DIR}/node/caches"
  info "目录创建完成: ${NODE_DIR}"
fi

# ── 下载并安装二进制 ──────────────────────────────────────────────────────────
step "下载 FreeCDN 二进制"

# FreeCDN Release tar.gz 包结构：
#   freecdn-v0.1.0-linux-amd64/
#     edge-admin          ← 主程序
#     web/                ← 前端资源
#     edge-api/bin/edge-api
#     edge-api/deploy/edge-node-linux-amd64-*.zip
#
# 降级：GoEdge zip 包结构：
#   edge-admin/
#     bin/edge-admin
#     web/
#     edge-api/bin/edge-api
#     edge-api/deploy/edge-node-linux-amd64-*.zip

DOWNLOAD_FILE="/tmp/freecdn-pkg"
DOWNLOAD_OK="false"
DOWNLOAD_TYPE="tar"   # tar | zip

# 0. 本地缓存检测：如果已有完整的 tar.gz，直接使用，跳过所有网络下载
if [ -f "${DOWNLOAD_FILE}.tar.gz" ] && tar -tzf "${DOWNLOAD_FILE}.tar.gz" >/dev/null 2>&1; then
  info "检测到本地缓存包，跳过下载"
  DOWNLOAD_OK="true"
  DOWNLOAD_TYPE="tar"
  DOWNLOAD_FILE="${DOWNLOAD_FILE}.tar.gz"
fi

# 1. 优先尝试 FreeCDN Release（经镜像站加速）
if [ "$DOWNLOAD_OK" = "false" ]; then
info "探测最快下载镜像，请稍候..."
BEST_URL=$(pick_fastest_mirror)
if [ -n "$BEST_URL" ]; then
  info "最快镜像: $BEST_URL"
  # 把最快的镜像放到队列头，再加上其余镜像作为后备
  ORDERED_MIRRORS=("$BEST_URL")
  for u in "${GITHUB_MIRRORS[@]}"; do
    [ "$u" = "$BEST_URL" ] && continue
    ORDERED_MIRRORS+=("$u")
  done
else
  warn "镜像探测失败，依次尝试所有镜像..."
  ORDERED_MIRRORS=("${GITHUB_MIRRORS[@]}")
fi

for FREECDN_URL in "${ORDERED_MIRRORS[@]}"; do
  info "尝试下载: $FREECDN_URL"
  if wget -q --show-progress --timeout=300 --tries=1 "$FREECDN_URL" \
       -O "${DOWNLOAD_FILE}.tar.gz" 2>/dev/null; then
    # 校验包完整性
    if tar -tzf "${DOWNLOAD_FILE}.tar.gz" >/dev/null 2>&1; then
      DOWNLOAD_OK="true"
      DOWNLOAD_TYPE="tar"
      DOWNLOAD_FILE="${DOWNLOAD_FILE}.tar.gz"
      info "下载成功"
      break
    else
      warn "包校验失败（文件损坏），尝试下一个镜像..."
      rm -f "${DOWNLOAD_FILE}.tar.gz"
    fi
  else
    warn "下载失败，尝试下一个镜像..."
    rm -f "${DOWNLOAD_FILE}.tar.gz"
  fi
done
fi  # end: if DOWNLOAD_OK = false (skip download block)

[ "$DOWNLOAD_OK" = "true" ] || error "所有下载源均失败。请手动下载：
  https://github.com/hujiali30001/freecdn-admin/releases/download/${FREECDN_VERSION}/${RELEASE_FILE}
  上传到服务器 /tmp/freecdn-pkg.tar.gz 后重新运行安装脚本"
info "下载完成，解压中..."

TMP_SRC="/tmp/freecdn-admin-src"
rm -rf "$TMP_SRC"
mkdir -p "$TMP_SRC"

tar xzf "$DOWNLOAD_FILE" -C "$TMP_SRC" --strip-components=1
rm -f "$DOWNLOAD_FILE" 2>/dev/null || true
# FreeCDN Release 包解压后结构：直接包含 edge-admin、web/、edge-api/
SRC_ROOT="$TMP_SRC"

if [ "$MODE" = "admin" ]; then
  # 安装 edge-admin 二进制
  ADMIN_BIN="${SRC_ROOT}/edge-admin"
  API_BIN="${SRC_ROOT}/edge-api/bin/edge-api"
  NODE_DEPLOY_DIR="${SRC_ROOT}/edge-api/deploy"
  WEB_DIR="${SRC_ROOT}/web"

  [ -f "$ADMIN_BIN" ] || error "未找到 edge-admin 二进制，包结构异常（期望路径: $ADMIN_BIN）"
  cp "$ADMIN_BIN" "${ADMIN_DIR}/bin/edge-admin"
  chmod +x "${ADMIN_DIR}/bin/edge-admin"
  info "edge-admin 安装完成"

  # 安装 web 静态资源
  if [ -d "$WEB_DIR" ]; then
    cp -r "${WEB_DIR}/." "${ADMIN_DIR}/web/"
    info "web 静态资源安装完成"
  fi

  # 保存 VERSION 文件
  if [ -f "${SRC_ROOT}/VERSION" ]; then
    cp "${SRC_ROOT}/VERSION" "${ADMIN_DIR}/VERSION"
  fi

  # 安装 edge-api 二进制（包里没有时保留已有版本）
  if [ -f "$API_BIN" ]; then
    cp "$API_BIN" "${API_DIR}/bin/edge-api"
    chmod +x "${API_DIR}/bin/edge-api"
    info "edge-api 安装完成"
  elif [ -f "${API_DIR}/bin/edge-api" ]; then
    info "包中无 edge-api，保留现有版本（$(${API_DIR}/bin/edge-api -version 2>/dev/null || echo unknown)）"
  else
    error "未找到 edge-api 二进制，请检查下载包（期望路径: $API_BIN）"
  fi

  # 安装 freecdn-init 二进制（数据库初始化工具）
  INIT_BIN="${SRC_ROOT}/freecdn-init"
  if [ -f "$INIT_BIN" ]; then
    cp "$INIT_BIN" "${ADMIN_DIR}/bin/freecdn-init"
    chmod +x "${ADMIN_DIR}/bin/freecdn-init"
    info "freecdn-init 安装完成"
  fi

  # 保存 edge-node zip 供后续节点使用
  NODE_ZIP_FOUND=$(find "$NODE_DEPLOY_DIR" -name "edge-node-linux-${ARCH_TAG}-*.zip" 2>/dev/null | head -1 || true)
  if [ -n "$NODE_ZIP_FOUND" ]; then
    cp "$NODE_ZIP_FOUND" "${DATA_DIR}/edge-node.zip"
    info "edge-node 安装包已保存至: ${DATA_DIR}/edge-node.zip（供节点服务器使用）"
  fi

else
  # 节点模式：从全家桶中提取 edge-node
  NODE_ZIP_FOUND=$(find "$NODE_DEPLOY_DIR" -name "edge-node-linux-${ARCH_TAG}-*.zip" 2>/dev/null | head -1 || true)
  [ -n "$NODE_ZIP_FOUND" ] || error "未在下载包中找到 edge-node，请检查版本"

  # 停止正在运行的 freecdn-node 服务（如有），避免覆盖运行中二进制时报 "Text file busy"
  if systemctl is-active --quiet freecdn-node 2>/dev/null; then
    info "停止旧的 freecdn-node 服务以允许二进制更新..."
    systemctl stop freecdn-node 2>/dev/null || true
    sleep 1
  fi

  TMP_NODE="/tmp/freecdn-node-extract"
  rm -rf "$TMP_NODE"; mkdir -p "$TMP_NODE"
  unzip -q "$NODE_ZIP_FOUND" -d "$TMP_NODE"

  # 找 edge-node 二进制（可能在子目录）
  NODE_BIN=$(find "$TMP_NODE" -name "edge-node" -type f | head -1)
  [ -n "$NODE_BIN" ] || error "未找到 edge-node 二进制"
  cp "$NODE_BIN" "${NODE_DIR}/bin/edge-node"
  chmod +x "${NODE_DIR}/bin/edge-node"

  # 复制 web 静态资源（节点不需要，跳过）
  rm -rf "$TMP_NODE"
  info "edge-node 安装完成"
fi

rm -rf "$TMP_SRC"
info "二进制安装完成"

# ── 写配置文件（admin 模式）──────────────────────────────────────────────────
if [ "$MODE" = "admin" ]; then
  step "生成配置文件"

  # ① edge-admin: server.yaml
  # 注意：必须有 on: true，否则 HTTP server 不会启动
  cat > "${ADMIN_DIR}/configs/server.yaml" <<YAML
http:
  on: true
  listen:
    - "0.0.0.0:${ADMIN_HTTP_PORT}"
YAML
  info "server.yaml 生成完成"

  # ② edge-api: db.yaml（数据库连接）
  # TeaGo dbs 标准格式：default.db 指向 dbs 下的 key，dsn 使用 Go MySQL DSN 格式
  cat > "${API_DIR}/configs/db.yaml" <<YAML
default:
  db: prod

dbs:
  prod:
    driver: mysql
    dsn: "${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_PORT})/${MYSQL_DATABASE}?charset=utf8mb4&parseTime=true"
YAML
  info "db.yaml 生成完成"

  # api_admin.yaml 暂不生成，等数据库初始化后由程序自动生成或手动填入
  # （api_admin.yaml 需要数据库中的 nodeId/secret，需要先跑 edge-api upgrade 才能拿到）
  info "配置文件生成完成"
fi

# ── 写配置文件（node 模式）───────────────────────────────────────────────────
if [ "$MODE" = "node" ]; then
  step "生成节点配置文件"

  # edge-node: api_node.yaml
  # 正确格式（来自 edge-node 官方模板）：rpc.endpoints 点号写法 + nodeId + secret
  cat > "${NODE_DIR}/configs/api_node.yaml" <<YAML
rpc.endpoints: [ "${API_ENDPOINT}" ]
nodeId: "${NODE_ID}"
secret: "${NODE_SECRET}"
YAML
  info "api_node.yaml 生成完成"
fi

# ── 数据库初始化（admin 模式）────────────────────────────────────────────────
if [ "$MODE" = "admin" ]; then
  step "初始化数据库"

  # 生成管理员密码（若未预先设置）
  ADMIN_PASSWORD="FreeCDN$(date +%Y)!"

  # 获取服务器内网 IP（用于 accessAddrs）
  set +o pipefail
  SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' \
    || ip route get 1 2>/dev/null | awk '{print $NF;exit}' \
    || echo "127.0.0.1")
  set -o pipefail
  [ -z "$SERVER_IP" ] && SERVER_IP="127.0.0.1"
  info "检测到服务器 IP: ${SERVER_IP}"

  # 使用 freecdn-init 一键完成所有数据库初始化步骤：
  #   1. edge-api upgrade（建表/迁移）
  #   2. edge-api setup（创建 APINode + Token + SysSettings）
  #   3. 写 api_admin.yaml（嵌套格式，0600）
  #   4. 同步 api.yaml
  #   5. 创建管理员账号（bcrypt password）
  #   6. 写品牌设置
  MYSQL_DSN="${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_PORT})/${MYSQL_DATABASE}?charset=utf8mb4&parseTime=true"

  FREECDN_INIT_BIN="${ADMIN_DIR}/bin/freecdn-init"
  if [ -f "$FREECDN_INIT_BIN" ]; then
    info "运行 freecdn-init 初始化数据库..."
    INIT_OUT=$("$FREECDN_INIT_BIN" \
      --api-dir    "${API_DIR}" \
      --admin-dir  "${ADMIN_DIR}" \
      --mysql-dsn  "${MYSQL_DSN}" \
      --api-host   "${SERVER_IP}" \
      --api-port   "${API_RPC_PORT}" \
      --admin-user "admin" \
      --admin-pass "${ADMIN_PASSWORD}" \
      2>&1) || {
      error "freecdn-init 失败，请检查上方日志：
  mysql-dsn: ${MYSQL_USER}:***@tcp(${MYSQL_HOST}:${MYSQL_PORT})/${MYSQL_DATABASE}
  api-dir:   ${API_DIR}
  提示：1. MySQL 连接是否正常？ 2. edge-api 是否已正确安装？"
    }
    info "数据库初始化完成"
  else
    # 兼容旧包（freecdn-init 不存在时退化为 bash 路径）
    warn "未找到 freecdn-init，使用传统 bash 初始化方式..."
    _bash_init_db
  fi
fi

# ── _bash_init_db：传统 bash 初始化（freecdn-init 不可用时的后备）──────────
_bash_init_db() {
  # Step 1：edge-api upgrade
  info "运行数据库迁移（edge-api upgrade）..."
  UPGRADE_OUT="/tmp/freecdn_upgrade_$$.log"
  cd "${API_DIR}"
  UPGRADE_OK=false
  for _retry in 1 2 3; do
    if ./bin/edge-api upgrade > "$UPGRADE_OUT" 2>&1; then
      UPGRADE_OK=true; tail -3 "$UPGRADE_OUT" || true; break
    fi
    grep -q "panic" "$UPGRADE_OUT" 2>/dev/null && {
      warn "edge-api upgrade panic（第 ${_retry} 次），1秒后重试..."; sleep 1; continue
    }
    UPGRADE_OK=true
    warn "edge-api upgrade 返回非零（可能是表已存在，继续）："
    cat "$UPGRADE_OUT" >&2 || true; break
  done
  rm -f "$UPGRADE_OUT"
  cd - > /dev/null
  [ "$UPGRADE_OK" = "true" ] || error "edge-api upgrade 连续 3 次 panic"
  info "数据库迁移完成"

  # Step 2：edge-api setup
  info "运行 edge-api setup..."
  SETUP_OUT="/tmp/freecdn_setup_$$.json"
  cd "${API_DIR}"
  SETUP_OK=false
  for _retry in 1 2 3; do
    if ./bin/edge-api setup \
        -api-node-protocol=http \
        -api-node-host="${SERVER_IP}" \
        -api-node-port="${API_RPC_PORT}" \
        > "$SETUP_OUT" 2>&1; then
      SETUP_OK=true; break
    fi
    warn "edge-api setup 第 ${_retry} 次失败，1秒后重试..."; sleep 1
  done
  cd - > /dev/null

  ADMIN_TOKEN_NODE_ID=""
  ADMIN_TOKEN_SECRET=""
  if [ -f "$SETUP_OUT" ]; then
    if command -v python3 &>/dev/null; then
      ADMIN_TOKEN_NODE_ID=$(python3 -c "
import sys,json
try:
    d=json.load(open('${SETUP_OUT}'))
    print(d.get('adminNodeId',''))
except: pass
" 2>/dev/null || true)
      ADMIN_TOKEN_SECRET=$(python3 -c "
import sys,json
try:
    d=json.load(open('${SETUP_OUT}'))
    print(d.get('adminNodeSecret',''))
except: pass
" 2>/dev/null || true)
    fi
    rm -f "$SETUP_OUT"
  fi

  if [ -z "$ADMIN_TOKEN_NODE_ID" ] || [ -z "$ADMIN_TOKEN_SECRET" ]; then
    warn "无法从 setup 输出解析 token，从数据库读取..."
    ADMIN_TOKEN_NODE_ID=$(mysql -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
      -sNe "SELECT nodeId FROM edgeAPITokens WHERE role='admin' LIMIT 1;" 2>/dev/null | tr -d '\r' || true)
    ADMIN_TOKEN_SECRET=$(mysql -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
      -sNe "SELECT secret FROM edgeAPITokens WHERE role='admin' LIMIT 1;" 2>/dev/null | tr -d '\r' || true)
  fi

  [ -n "$ADMIN_TOKEN_NODE_ID" ] && [ -n "$ADMIN_TOKEN_SECRET" ] || \
    error "无法获取 admin token，请检查 MySQL 连接和 edge-api upgrade"

  # api_admin.yaml
  cat > "${ADMIN_DIR}/configs/api_admin.yaml" <<YAML
rpc:
  endpoints:
    - "http://127.0.0.1:${API_RPC_PORT}"
nodeId: "${ADMIN_TOKEN_NODE_ID}"
secret: "${ADMIN_TOKEN_SECRET}"
YAML
  chmod 600 "${ADMIN_DIR}/configs/api_admin.yaml"
  info "api_admin.yaml 生成完成"

  # api.yaml
  DB_API_UNIQUE_ID=$(mysql -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    -sNe "SELECT uniqueId FROM edgeAPINodes WHERE id=1 LIMIT 1;" 2>/dev/null | tr -d '\r' || true)
  DB_API_SECRET=$(mysql -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" \
    -sNe "SELECT secret FROM edgeAPINodes WHERE id=1 LIMIT 1;" 2>/dev/null | tr -d '\r' || true)
  if [ -n "$DB_API_UNIQUE_ID" ] && [ -n "$DB_API_SECRET" ]; then
    cat > "${API_DIR}/configs/api.yaml" <<YAML
nodeId: "${DB_API_UNIQUE_ID}"
secret: "${DB_API_SECRET}"
YAML
    info "api.yaml 已与数据库同步"
  fi

  # 管理员账号
  ADMIN_PASSWORD_MD5=$(echo -n "$ADMIN_PASSWORD" | md5sum | cut -d' ' -f1)
  mysql -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null <<SQL || \
    warn "管理员账号写入失败（可能已存在，继续）"
INSERT IGNORE INTO edgeAdmins (id, isOn, username, password, isSuper, state, createdAt, updatedAt, canLogin)
VALUES (1, 1, 'admin', '${ADMIN_PASSWORD_MD5}', 1, 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 1);
SQL
  info "管理员账号创建完成"

  mysql -h 127.0.0.1 -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" 2>/dev/null <<'SQL' || \
    warn "品牌设置写入失败（可能已存在，继续）"
INSERT INTO edgeSysSettings (userId, code, value)
VALUES
  (0, 'product.name', '"FreeCDN"'),
  (0, 'admin.name',   '"FreeCDN管理员系统"')
ON DUPLICATE KEY UPDATE value = VALUES(value);
SQL
  info "品牌设置写入完成"
}

# ── 注册 systemd 服务 ─────────────────────────────────────────────────────────
step "注册系统服务"

if [ "$MODE" = "admin" ]; then
  # edge-api 和 edge-admin 是两个独立进程，需要分别注册 service。
  # edge-admin 通过 api_admin.yaml 中的 rpc.endpoints 连接 edge-api（8003 端口）。
  # 启动顺序：freecdn-api 先于 freecdn-admin。

  # 注册 freecdn-api.service
  cat > /etc/systemd/system/freecdn-api.service <<SERVICE
[Unit]
Description=FreeCDN API Service
Documentation=https://github.com/hujiali30001/freecdn-admin
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

  # 注册 freecdn-admin.service（依赖 freecdn-api 先就绪）
  cat > /etc/systemd/system/freecdn-admin.service <<SERVICE
[Unit]
Description=FreeCDN Admin Service
Documentation=https://github.com/hujiali30001/freecdn-admin
After=network.target mysql.service mysqld.service freecdn-api.service
Wants=mysql.service mysqld.service
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
  info "服务注册完成: freecdn-api + freecdn-admin"

else
  cat > /etc/systemd/system/freecdn-node.service <<SERVICE
[Unit]
Description=FreeCDN Edge Node
Documentation=https://github.com/hujiali30001/freecdn-admin
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
  # 先启 edge-api，等 8003 就绪后再启 edge-admin
  systemctl start freecdn-api
  info "等待 edge-api 就绪 (${API_RPC_PORT} 端口)，最长 30 秒..."
  _port_open() {
    if command -v nc &>/dev/null; then
      nc -z -w2 127.0.0.1 "$1" &>/dev/null
    else
      (echo >/dev/tcp/127.0.0.1/"$1") &>/dev/null
    fi
  }
  for i in $(seq 1 30); do
    if _port_open "${API_RPC_PORT}"; then
      info "edge-api 已就绪 (${API_RPC_PORT} 端口，耗时 ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      warn "edge-api 等待超时（30s），请检查: journalctl -u freecdn-api -n 30"
    fi
    sleep 1
  done

  systemctl start freecdn-admin
  info "等待管理后台就绪 (${ADMIN_HTTP_PORT} 端口)，最长 30 秒..."
  for i in $(seq 1 30); do
    if _port_open "${ADMIN_HTTP_PORT}"; then
      info "管理后台已就绪 (${ADMIN_HTTP_PORT} 端口，耗时 ${i}s)"
      break
    fi
    if [ "$i" -eq 30 ]; then
      warn "等待超时（30s），服务可能仍在启动。请用以下命令检查："
      warn "  systemctl status freecdn-admin freecdn-api"
      warn "  journalctl -u freecdn-admin -n 30"
    fi
    sleep 1
  done

else
  systemctl start freecdn-node
  sleep 3
  if systemctl is-active --quiet freecdn-node; then
    info "边缘节点启动成功"
  else
    warn "边缘节点可能未启动，请检查日志：journalctl -u freecdn-node -n 30"
  fi
fi

# ── 获取服务器公网 IP ─────────────────────────────────────────────────────────
# 临时关闭 pipefail，curl | grep 等可能触发 SIGPIPE
set +o pipefail
SERVER_IP=$(curl -4sf --connect-timeout 5 https://api.ipify.org 2>/dev/null \
         || curl -4sf --connect-timeout 5 https://ifconfig.me 2>/dev/null \
         || hostname -I 2>/dev/null | awk '{print $1}' \
         || echo "YOUR_SERVER_IP")
set -o pipefail

# ── 完成提示 ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
if [ "$MODE" = "admin" ]; then
  echo -e "${GREEN}${BOLD}  FreeCDN 管理节点安装完成！${NC}"
  echo -e "${GREEN}${BOLD}════════════════════════════════════════${NC}"
  echo ""
  echo -e "  管理后台地址:  ${CYAN}http://${SERVER_IP}:${ADMIN_HTTP_PORT}${NC}"
  echo -e "  API RPC 地址:  ${CYAN}http://${SERVER_IP}:${API_RPC_PORT}${NC}  ← 边缘节点安装时填入"
  echo ""
  echo -e "  ${BOLD}管理员账号：${NC}"
  echo -e "    用户名: ${CYAN}admin${NC}"
  echo -e "    密 码:  ${CYAN}${ADMIN_PASSWORD}${NC}"
  echo ""
  if [ "${MYSQL_PASSWORD_GENERATED}" = "true" ]; then
    echo -e "  ${BOLD}数据库密码（自动生成，请记录）：${NC}"
    echo -e "    ${YELLOW}${MYSQL_PASSWORD}${NC}"
    echo ""
  fi
  echo -e "  ${BOLD}下一步：${NC}"
  echo "  1. 在浏览器访问管理后台并登录"
  echo "  2. 在「集群管理 → 节点」中添加边缘节点，获取节点 ID 和密钥"
  echo "  3. 在边缘节点服务器上运行："
  echo -e "     ${CYAN}curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | \\"
  echo -e "       bash -s -- --node --api-endpoint http://${SERVER_IP}:${API_RPC_PORT} \\"
  echo -e "                  --node-id YOUR_NODE_ID --node-secret YOUR_NODE_SECRET${NC}"
  echo ""
  echo -e "  ${BOLD}常用命令：${NC}"
  echo "  查看状态:  systemctl status freecdn-admin"
  echo "  查看日志:  journalctl -u freecdn-admin -f"
  echo "  重启服务:  systemctl restart freecdn-admin"
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
