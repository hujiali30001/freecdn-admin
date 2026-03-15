#!/bin/bash
# ==============================================================
# FreeCDN Admin + API 容器入口脚本
#
# 负责：
#   1. 根据环境变量生成配置文件（configs/）
#   2. 等待 MySQL 就绪
#   3. 运行 edge-api upgrade 初始化数据库表
#   4. 自动插入初始数据（API 节点记录、管理员 Token、管理员账号）
#   5. 前台运行 edge-admin
#
# 环境变量：
#   MYSQL_HOST        MySQL 主机名（默认：mysql）
#   MYSQL_PORT        MySQL 端口（默认：3306）
#   MYSQL_USER        MySQL 用户（默认：freecdn）
#   MYSQL_PASSWORD    MySQL 密码（默认：freecdn_pass_2026）
#   MYSQL_DATABASE    MySQL 数据库（默认：freecdn）
#   ADMIN_HTTP_PORT   管理后台端口（默认：7788）
#   API_RPC_PORT      EdgeAPI RPC 端口（默认：8003）
#   ADMIN_USERNAME    初始管理员用户名（默认：admin）
#   ADMIN_PASSWORD    初始管理员密码（默认：FreeCDN2026!）
#   TZ                时区（默认：Asia/Shanghai）
# ==============================================================
set -e

WORKDIR=/app/edge-admin
API_DIR="${WORKDIR}/edge-api"

# ---- 颜色输出 ----
info()  { echo "[entrypoint] ✓ $*"; }
warn()  { echo "[entrypoint] ! $*" >&2; }
error() { echo "[entrypoint] ✗ $*" >&2; exit 1; }

# ---- 环境变量默认值 ----
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-freecdn}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-freecdn_pass_2026}"
MYSQL_DATABASE="${MYSQL_DATABASE:-freecdn}"
ADMIN_HTTP_PORT="${ADMIN_HTTP_PORT:-7788}"
API_RPC_PORT="${API_RPC_PORT:-8003}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-FreeCDN2026!}"

info "FreeCDN Admin 容器启动..."
info "MySQL: ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}"
info "Admin port: ${ADMIN_HTTP_PORT}, API RPC port: ${API_RPC_PORT}"

# ---- 生成 server.yaml（edge-admin HTTP 监听配置）----
cat > "${WORKDIR}/configs/server.yaml" << EOF
http:
  on: true
  listen:
    - "0.0.0.0:${ADMIN_HTTP_PORT}"
EOF
info "生成 configs/server.yaml"

# ---- 生成 edge-api/configs/db.yaml ----
cat > "${API_DIR}/configs/db.yaml" << EOF
user: ${MYSQL_USER}
password: ${MYSQL_PASSWORD}
host: ${MYSQL_HOST}:${MYSQL_PORT}
database: ${MYSQL_DATABASE}
EOF
info "生成 edge-api/configs/db.yaml"

# ---- 等待 MySQL 就绪 ----
info "等待 MySQL ${MYSQL_HOST}:${MYSQL_PORT} 就绪..."
MAX_WAIT=60
COUNT=0
until nc -z "${MYSQL_HOST}" "${MYSQL_PORT}" 2>/dev/null; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_WAIT ]; then
    warn "MySQL 等待超时（${MAX_WAIT}s），尝试继续启动..."
    break
  fi
  echo "[entrypoint] 等待 MySQL... (${COUNT}/${MAX_WAIT})"
  sleep 1
done
# 额外等待 2 秒让 MySQL 完全就绪
sleep 2
info "MySQL 连接就绪"

# ---- 运行 edge-api upgrade 初始化数据库表 ----
info "运行数据库迁移 (edge-api upgrade)..."
cd "${API_DIR}"
if ! ./bin/edge-api upgrade > /tmp/upgrade.log 2>&1; then
  warn "edge-api upgrade 返回非零，可能表已存在，继续..."
  tail -5 /tmp/upgrade.log >&2 || true
else
  info "数据库迁移完成"
  tail -3 /tmp/upgrade.log || true
fi
cd "${WORKDIR}"

# ---- 检查是否需要初始化数据（首次启动）----
# 判断依据：api_admin.yaml 里 nodeId 是否已填入
NEEDS_INIT="true"
if [ -f "${WORKDIR}/configs/api_admin.yaml" ]; then
  NODE_ID_VAL=$(grep "^nodeId:" "${WORKDIR}/configs/api_admin.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs || true)
  if [ -n "$NODE_ID_VAL" ] && [ "$NODE_ID_VAL" != '""' ] && [ "$NODE_ID_VAL" != "''" ]; then
    NEEDS_INIT="false"
    info "检测到已有配置（nodeId=${NODE_ID_VAL}），跳过初始化，保留现有数据"
  fi
fi

if [ "$NEEDS_INIT" = "true" ]; then
  info "首次启动，执行数据库初始化..."

  # 生成随机 ID 和 Secret
  # 容器内可能没有 /proc/sys/kernel/random/uuid，用 openssl 替代
  gen_uuid() {
    if [ -f /proc/sys/kernel/random/uuid ]; then
      cat /proc/sys/kernel/random/uuid | tr -d '-'
    elif command -v openssl &>/dev/null; then
      openssl rand -hex 16
    else
      # 终极备用：拼接时间戳和随机数
      echo "$(date +%s%N)$(head -c 8 /dev/urandom | xxd -p 2>/dev/null || echo $$)" | md5sum | cut -c1-32
    fi
  }

  API_NODE_ID=$(gen_uuid)
  API_NODE_SECRET=$(gen_uuid)
  ADMIN_TOKEN_NODE_ID=$(gen_uuid)
  ADMIN_TOKEN_SECRET=$(gen_uuid)

  # 获取容器/宿主机 IP（用于 accessAddrs）
  # host 网络模式下 hostname -I 可以拿到宿主机 IP
  SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
  [ -z "$SERVER_IP" ] && SERVER_IP="127.0.0.1"

  info "生成 API 节点 ID: ${API_NODE_ID:0:8}..."
  info "生成 Admin Token ID: ${ADMIN_TOKEN_NODE_ID:0:8}..."
  info "服务器 IP: ${SERVER_IP}"

  # MySQL 客户端连接参数（容器内通过 TCP 连接，不走 socket）
  MYSQL_CMD="mysql -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}"

  # 插入 edgeAPINodes 记录
  # 关键字段：
  #   uniqueId    = api.yaml 中的 nodeId（edge-api 启动时校验）
  #   http        = HTTPProtocolConfig JSON（protocol 必须是 "http"，不能是空字符串）
  #   accessAddrs = 外部访问地址（不能是空数组 []）
  info "写入 edgeAPINodes..."
  $MYSQL_CMD 2>/dev/null <<SQL || warn "edgeAPINodes 插入失败（可能已存在，跳过）"
INSERT IGNORE INTO edgeAPINodes (id, isOn, uniqueId, name, description, secret, clusterId, http, https, accessAddrs, state, createdAt, updatedAt)
VALUES (
  1,
  1,
  '${API_NODE_ID}',
  'Primary API Node',
  'Auto created by FreeCDN Docker',
  '${API_NODE_SECRET}',
  0,
  '{"isOn":true,"listen":[{"protocol":"http","host":"","portRange":"${API_RPC_PORT}","description":""}]}',
  '{}',
  '[{"protocol":"http","host":"${SERVER_IP}","portRange":"${API_RPC_PORT}","description":""}]',
  1,
  UNIX_TIMESTAMP(),
  UNIX_TIMESTAMP()
);
SQL

  # 插入 edgeAPITokens 记录（role=admin，供 edge-admin 认证用）
  info "写入 edgeAPITokens..."
  $MYSQL_CMD 2>/dev/null <<SQL || warn "edgeAPITokens 插入失败（可能已存在，跳过）"
INSERT IGNORE INTO edgeAPITokens (nodeId, secret, role, state)
VALUES (
  '${ADMIN_TOKEN_NODE_ID}',
  '${ADMIN_TOKEN_SECRET}',
  'admin',
  1
);
SQL

  # 生成管理员密码 MD5（GoEdge 使用 MD5，非 bcrypt）
  ADMIN_PASSWORD_MD5=$(echo -n "${ADMIN_PASSWORD}" | md5sum | cut -d' ' -f1)

  # 插入管理员账号
  info "写入 edgeAdmins（用户名: ${ADMIN_USERNAME}）..."
  $MYSQL_CMD 2>/dev/null <<SQL || warn "edgeAdmins 插入失败（可能已存在，跳过）"
INSERT IGNORE INTO edgeAdmins (id, isOn, username, password, isSuper, state, createdAt, updatedAt, canLogin)
VALUES (1, 1, '${ADMIN_USERNAME}', '${ADMIN_PASSWORD_MD5}', 1, 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 1);
SQL

  # 生成 edge-api/configs/api.yaml（API 节点自身认证）
  cat > "${API_DIR}/configs/api.yaml" << EOF
nodeId: "${API_NODE_ID}"
secret: "${API_NODE_SECRET}"
EOF
  info "生成 edge-api/configs/api.yaml"

  # 生成 edge-admin/configs/api_admin.yaml（admin 连接 api 的认证）
  # 注意：必须用点号写法 rpc.endpoints，不能用 YAML 嵌套的 rpc: endpoints:
  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc.endpoints: [ "http://127.0.0.1:${API_RPC_PORT}" ]
nodeId: "${ADMIN_TOKEN_NODE_ID}"
secret: "${ADMIN_TOKEN_SECRET}"
EOF
  info "生成 configs/api_admin.yaml"

  info "============================================"
  info "初始化完成！"
  info "  管理后台地址: http://<服务器IP>:${ADMIN_HTTP_PORT}"
  info "  用户名: ${ADMIN_USERNAME}"
  info "  密  码: ${ADMIN_PASSWORD}"
  info "============================================"

else
  # 非首次启动：只更新 api_admin.yaml 的端口（保留已有 nodeId/secret）
  EXIST_NODE_ID=$(grep "^nodeId:" "${WORKDIR}/configs/api_admin.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs || true)
  EXIST_SECRET=$(grep "^secret:" "${WORKDIR}/configs/api_admin.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs || true)
  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc.endpoints: [ "http://127.0.0.1:${API_RPC_PORT}" ]
nodeId: "${EXIST_NODE_ID}"
secret: "${EXIST_SECRET}"
EOF
  info "更新 configs/api_admin.yaml（保留原有 nodeId/secret）"
fi

# ---- 前台运行 edge-admin ----
# edge-admin 会自动检测 edge-api/ 子目录并 fork edge-api 子进程
info "启动 edge-admin（前台模式）..."
exec "${WORKDIR}/bin/edge-admin"
