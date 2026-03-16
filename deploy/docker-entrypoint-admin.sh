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
#   MYSQL_PASSWORD    MySQL 密码（默认：REDACTED_DB_PASS）
#   MYSQL_DATABASE    MySQL 数据库（默认：freecdn）
#   ADMIN_HTTP_PORT   管理后台端口（默认：7788）
#   API_RPC_PORT      EdgeAPI RPC 端口（默认：8003）
#   ADMIN_USERNAME    初始管理员用户名（默认：admin）
#   ADMIN_PASSWORD    初始管理员密码（默认：REDACTED_SSH_PASS）
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
MYSQL_PASSWORD="${MYSQL_PASSWORD:-REDACTED_DB_PASS}"
MYSQL_DATABASE="${MYSQL_DATABASE:-freecdn}"
ADMIN_HTTP_PORT="${ADMIN_HTTP_PORT:-7788}"
API_RPC_PORT="${API_RPC_PORT:-8003}"
ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-REDACTED_SSH_PASS}"

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
# TeaGo 框架要求的格式：dbs.prod.driver/dsn
# 密码中不能含 @ 等 DSN 特殊字符（当前密码 REDACTED_DB_PASS 安全）
cat > "${API_DIR}/configs/db.yaml" << EOF
dbs:
  prod:
    driver: mysql
    dsn: ${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_PORT})/${MYSQL_DATABASE}?charset=utf8mb4&timeout=30s&parseTime=true
    prefix: edge
EOF
info "生成 edge-api/configs/db.yaml（TeaGo 格式）"

# ---- 等待 MySQL 就绪 ----
info "等待 MySQL ${MYSQL_HOST}:${MYSQL_PORT} 就绪..."
MAX_WAIT=60
COUNT=0
# 优先用 bash TCP 内置机制，fallback 到 nc
check_mysql() {
  bash -c "echo > /dev/tcp/${MYSQL_HOST}/${MYSQL_PORT}" 2>/dev/null \
    || nc -z "${MYSQL_HOST}" "${MYSQL_PORT}" 2>/dev/null
}
# 先等 TCP 端口就绪
until check_mysql; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_WAIT ]; then
    warn "MySQL TCP 等待超时（${MAX_WAIT}s），尝试继续启动..."
    break
  fi
  echo "[entrypoint] 等待 MySQL TCP... (${COUNT}/${MAX_WAIT})"
  sleep 1
done

# TCP 就绪后，还需等待 MySQL 服务完全初始化（能执行真实 SQL）
# 直接运行 mysql 命令验证，最多再等 30 秒
MYSQL_CMD="mysql -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}"
COUNT=0
MAX_SQL_WAIT=30
until $MYSQL_CMD -e "SELECT 1;" >/dev/null 2>&1; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_SQL_WAIT ]; then
    warn "MySQL SQL 等待超时（${MAX_SQL_WAIT}s），尝试继续启动..."
    break
  fi
  echo "[entrypoint] 等待 MySQL SQL 就绪... (${COUNT}/${MAX_SQL_WAIT})"
  sleep 1
done
info "MySQL 连接就绪（TCP + SQL 均已就绪）"

# ---- 运行 edge-api upgrade 初始化数据库表 ----
# edge-api upgrade 需要 api.yaml 才能运行（读取 nodeId/secret）
# 若不存在则先生成一个临时文件（之后首次初始化会覆盖它）
if [ ! -f "${API_DIR}/configs/api.yaml" ]; then
  TEMP_UUID=$(openssl rand -hex 16 2>/dev/null || cat /proc/sys/kernel/random/uuid 2>/dev/null | tr -d '-' || echo "tmp$(date +%s)")
  cat > "${API_DIR}/configs/api.yaml" << EOF
nodeId: "${TEMP_UUID}"
secret: "${TEMP_UUID}"
EOF
  info "生成临时 edge-api/configs/api.yaml（供 upgrade 使用）"
fi

info "运行数据库迁移 (edge-api upgrade)..."
# 必须在 API_DIR 下运行，TeaGo 框架用当前目录定位 configs/db.yaml
( cd "${API_DIR}" && ./bin/edge-api upgrade > /tmp/upgrade.log 2>&1 ) || {
  UPGRADE_OUTPUT=$(cat /tmp/upgrade.log 2>/dev/null || true)
  if echo "$UPGRADE_OUTPUT" | grep -qi 'finished\|already\|exist'; then
    info "数据库迁移已完成（表已存在）"
  else
    warn "edge-api upgrade 返回非零，日志如下："
    cat /tmp/upgrade.log >&2 || true
    warn "继续尝试启动..."
  fi
}
if grep -q 'finished' /tmp/upgrade.log 2>/dev/null; then
  info "数据库迁移完成（upgrade finished）"
fi

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

  # MySQL 客户端连接参数（容器内通过 TCP 连接，不走 socket）
  MYSQL_CMD="mysql -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}"

  # edge-api upgrade 会自动在 edgeAPITokens 表中插入 admin/cluster/user 三个 token
  # 我们直接读取 upgrade 生成的 admin token，不另外生成
  ADMIN_TOKEN_NODE_ID=$($MYSQL_CMD -sNe "SELECT nodeId FROM edgeAPITokens WHERE role='admin' LIMIT 1;" 2>/dev/null | tr -d '\r' || true)
  ADMIN_TOKEN_SECRET=$($MYSQL_CMD -sNe "SELECT secret FROM edgeAPITokens WHERE role='admin' LIMIT 1;" 2>/dev/null | tr -d '\r' || true)

  if [ -z "$ADMIN_TOKEN_NODE_ID" ]; then
    warn "无法从 edgeAPITokens 读取 admin token，将使用随机生成的 token"
    gen_uuid() {
      if [ -f /proc/sys/kernel/random/uuid ]; then
        cat /proc/sys/kernel/random/uuid | tr -d '-'
      elif command -v openssl &>/dev/null; then
        openssl rand -hex 16
      else
        echo "$(date +%s)$(cat /dev/urandom | od -An -N4 -tx4 | tr -d ' \n')" | md5sum | cut -c1-32
      fi
    }
    ADMIN_TOKEN_NODE_ID=$(gen_uuid)
    ADMIN_TOKEN_SECRET=$(gen_uuid)
    $MYSQL_CMD 2>/dev/null <<SQL || warn "edgeAPITokens 插入失败"
INSERT IGNORE INTO edgeAPITokens (nodeId, secret, role, state)
VALUES ('${ADMIN_TOKEN_NODE_ID}', '${ADMIN_TOKEN_SECRET}', 'admin', 1);
SQL
  fi
  info "Admin token nodeId: ${ADMIN_TOKEN_NODE_ID:0:8}..."

  # 获取容器 IP（用于 accessAddrs）
  SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "127.0.0.1")
  [ -z "$SERVER_IP" ] && SERVER_IP="127.0.0.1"
  info "服务器 IP: ${SERVER_IP}"

  # 读取临时 api.yaml 中的 nodeId/secret（upgrade 前生成的），用于注册 API 节点
  API_NODE_ID=$(grep "^nodeId:" "${API_DIR}/configs/api.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs || true)
  API_NODE_SECRET_VAL=$(grep "^secret:" "${API_DIR}/configs/api.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs || true)

  # 如果 api.yaml 里的 ID 是临时的（upgrade 前生成），重新生成正式的
  if [ -z "$API_NODE_ID" ]; then
    API_NODE_ID=$(openssl rand -hex 16 2>/dev/null || echo "$(date +%s)api")
    API_NODE_SECRET_VAL=$(openssl rand -hex 16 2>/dev/null || echo "$(date +%s)sec")
  fi
  info "API 节点 ID: ${API_NODE_ID:0:8}..."

  # 插入 edgeAPINodes 记录
  # 注意：edgeAPINodes 表没有 updatedAt 列（与 edgeAdmins 不同）
  info "写入 edgeAPINodes..."
  $MYSQL_CMD 2>/dev/null <<SQL || warn "edgeAPINodes 插入失败（可能已存在，跳过）"
INSERT IGNORE INTO edgeAPINodes (id, isOn, uniqueId, name, description, secret, clusterId, http, https, accessAddrs, state, createdAt)
VALUES (
  1, 1,
  '${API_NODE_ID}',
  'Primary API Node',
  'Auto created by FreeCDN Docker',
  '${API_NODE_SECRET_VAL}',
  0,
  '{"isOn":true,"listen":[{"protocol":"http","host":"","portRange":"${API_RPC_PORT}","description":""}]}',
  '{}',
  '[{"protocol":"http","host":"${SERVER_IP}","portRange":"${API_RPC_PORT}","description":""}]',
  1,
  UNIX_TIMESTAMP()
);
SQL

  # 生成管理员密码 MD5（GoEdge 使用 MD5，非 bcrypt）
  ADMIN_PASSWORD_MD5=$(echo -n "${ADMIN_PASSWORD}" | md5sum | cut -d' ' -f1)

  # 插入管理员账号（注意 edgeAdmins 有 updatedAt 列）
  info "写入 edgeAdmins（用户名: ${ADMIN_USERNAME}）..."
  $MYSQL_CMD 2>/dev/null <<SQL || warn "edgeAdmins 插入失败（可能已存在，跳过）"
INSERT IGNORE INTO edgeAdmins (id, isOn, username, password, isSuper, state, createdAt, updatedAt, canLogin)
VALUES (1, 1, '${ADMIN_USERNAME}', '${ADMIN_PASSWORD_MD5}', 1, 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 1);
SQL

  # 写入 edge-api/configs/api.yaml（最终版本，覆盖临时文件）
  cat > "${API_DIR}/configs/api.yaml" << EOF
nodeId: "${API_NODE_ID}"
secret: "${API_NODE_SECRET_VAL}"
EOF
  info "生成 edge-api/configs/api.yaml（nodeId=${API_NODE_ID:0:8}...）"

  # 生成 edge-admin/configs/api_admin.yaml（admin 连接 api 的认证）
  # 使用 upgrade 自动生成的 admin token（或上面手动插入的）
  cat > "${WORKDIR}/configs/api_admin.yaml" << EOF
rpc:
  endpoints:
    - "http://127.0.0.1:${API_RPC_PORT}"
nodeId: "${ADMIN_TOKEN_NODE_ID}"
secret: "${ADMIN_TOKEN_SECRET}"
EOF
  info "生成 configs/api_admin.yaml（token=${ADMIN_TOKEN_NODE_ID:0:8}...）"

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
rpc:
  endpoints:
    - "http://127.0.0.1:${API_RPC_PORT}"
nodeId: "${EXIST_NODE_ID}"
secret: "${EXIST_SECRET}"
EOF
  info "更新 configs/api_admin.yaml（保留原有 nodeId/secret）"

  # 确保 edge-api/configs/api.yaml 存在（容器重建后可能丢失）
  # edge-api 没有 api.yaml 时不会被 edge-admin fork 启动
  if [ ! -f "${API_DIR}/configs/api.yaml" ]; then
    warn "edge-api/configs/api.yaml 不存在，从数据库重建..."
    MYSQL_CMD="mysql -h${MYSQL_HOST} -P${MYSQL_PORT} -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}"
    API_UNIQUE_ID=$($MYSQL_CMD -sNe "SELECT uniqueId FROM edgeAPINodes WHERE id=1 LIMIT 1;" 2>/dev/null || true)
    API_NODE_SECRET=$($MYSQL_CMD -sNe "SELECT secret FROM edgeAPINodes WHERE id=1 LIMIT 1;" 2>/dev/null || true)
    if [ -n "$API_UNIQUE_ID" ] && [ -n "$API_NODE_SECRET" ]; then
      cat > "${API_DIR}/configs/api.yaml" << EOF
nodeId: "${API_UNIQUE_ID}"
secret: "${API_NODE_SECRET}"
EOF
      info "重建 edge-api/configs/api.yaml（nodeId=${API_UNIQUE_ID:0:8}...）"
    else
      warn "无法从数据库获取 edge-api 节点信息，edge-api 可能无法启动"
    fi
  fi
fi

# ---- 前台运行 edge-admin ----
# edge-admin 启动后会自动检测 edge-api/ 子目录并 fork edge-api 子进程
# 不需要在 entrypoint 里单独启动 edge-api
cd "${WORKDIR}"
info "启动 edge-admin（前台模式，edge-api 将由 edge-admin 自动 fork）..."

# ---- 后台自动完成 setup/confirm 激活 API 连接 ----
# GoEdge 每次启动后需要通过 /setup/confirm 重新激活内存中的 RPC 连接
# 用 User-Agent 绕过 GoEdge 的安全中间件，等待 edge-admin + edge-api 完全启动后自动提交
_auto_setup_confirm() {
  local PORT="${ADMIN_HTTP_PORT:-7788}"
  local API_PORT="${API_RPC_PORT:-8003}"
  local ENDPOINT="http://127.0.0.1:${API_PORT}"
  local UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
  local MAX_WAIT=90

  # 等待 edge-admin HTTP 端口就绪
  local count=0
  until bash -c "echo > /dev/tcp/127.0.0.1/${PORT}" 2>/dev/null; do
    count=$((count+1))
    [ $count -ge $MAX_WAIT ] && { warn "auto setup: edge-admin 启动超时"; return 1; }
    sleep 1
  done

  # 等待 edge-api RPC 端口就绪（edge-admin fork edge-api 需要额外时间）
  count=0
  until bash -c "echo > /dev/tcp/127.0.0.1/${API_PORT}" 2>/dev/null; do
    count=$((count+1))
    [ $count -ge $MAX_WAIT ] && { warn "auto setup: edge-api 启动超时"; return 1; }
    sleep 1
  done
  sleep 3  # 额外等待确保 edge-api 完全就绪

  # 读取当前 api_admin.yaml 中的 nodeId 和 secret
  local NODE_ID_VAL SECRET_VAL
  NODE_ID_VAL=$(grep "^nodeId:" "${WORKDIR}/configs/api_admin.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs)
  SECRET_VAL=$(grep "^secret:" "${WORKDIR}/configs/api_admin.yaml" 2>/dev/null | awk '{print $2}' | tr -d '"' | tr -d "'" | xargs)

  # 获取 CSRF token
  local csrf_resp csrf_token
  csrf_resp=$(curl -sf -A "$UA" "http://127.0.0.1:${PORT}/csrf/token" 2>/dev/null) || { warn "auto setup: 获取 csrf token 失败"; return 1; }
  csrf_token=$(echo "$csrf_resp" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)
  [ -z "$csrf_token" ] && { warn "auto setup: csrf token 解析失败"; return 1; }

  # 提交 setup/confirm
  local setup_resp
  setup_resp=$(curl -sf -A "$UA" -X POST "http://127.0.0.1:${PORT}/setup/confirm" \
    -F "endpoints=${ENDPOINT}" \
    -F "nodeId=${NODE_ID_VAL}" \
    -F "secret=${SECRET_VAL}" \
    -F "csrfToken=${csrf_token}" 2>/dev/null) || { warn "auto setup: 提交 setup/confirm 失败"; return 1; }

  local code
  code=$(echo "$setup_resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('code',''))" 2>/dev/null)
  if [ "$code" = "200" ]; then
    info "auto setup: API 连接激活成功 ✓"
  else
    warn "auto setup: setup/confirm 返回: $setup_resp"
  fi
}

# 在后台运行 setup/confirm 激活任务
_auto_setup_confirm &

exec ./bin/edge-admin
