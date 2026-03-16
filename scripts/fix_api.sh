#!/bin/bash
# ==============================================================================
# FreeCDN edge-api 修复脚本
# 解决：rpc error code=Unavailable / dial tcp 127.0.0.1:8003 connection refused
#
# 用法：bash fix_api.sh
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
error() { echo -e "${RED}[✗]${NC} $*" >&2; exit 1; }
step()  { echo -e "\n${CYAN}${BOLD}──── $* ────${NC}"; }

INSTALL_DIR="/usr/local/freecdn"
ADMIN_DIR="${INSTALL_DIR}/edge-admin"
API_DIR="${ADMIN_DIR}/edge-api"

[ "$(id -u)" -eq 0 ] || error "请用 root 运行"

# ─────────────────────────────────────────────────────────────────────────────
step "第 1 步：诊断"

echo ""
echo "--- 进程状态 ---"
ps aux | grep 'edge-' | grep -v grep || echo "（没有 edge-* 进程运行）"

echo ""
echo "--- 端口监听 ---"
ss -tlnp | grep -E '7788|8003' || echo "（7788/8003 均未监听）"

echo ""
echo "--- run.log（最后 20 行）---"
cat "${ADMIN_DIR}/logs/run.log" 2>/dev/null | tail -20 || echo "（run.log 不存在）"

echo ""
echo "--- edge-api run.log（最后 20 行）---"
cat "${API_DIR}/logs/run.log" 2>/dev/null | tail -20 || echo "（edge-api run.log 不存在）"

echo ""
echo "--- db.yaml ---"
cat "${API_DIR}/configs/db.yaml" 2>/dev/null || echo "（db.yaml 不存在）"

echo ""
echo "--- api.yaml ---"
cat "${API_DIR}/configs/api.yaml" 2>/dev/null || echo "（api.yaml 不存在）"

# ─────────────────────────────────────────────────────────────────────────────
step "第 2 步：测试数据库连接"

# 从 db.yaml 提取 DSN
DB_YAML="${API_DIR}/configs/db.yaml"
if [ ! -f "$DB_YAML" ]; then
  error "db.yaml 不存在，无法继续"
fi

# 解析 DSN：格式 user:pass@tcp(host:port)/db
DSN=$(grep 'dsn:' "$DB_YAML" | sed 's/.*dsn:[[:space:]]*//' | tr -d '"')
echo "DSN: $DSN"

DB_USER=$(echo "$DSN" | sed 's/:.*$//')
DB_PASS=$(echo "$DSN" | sed 's/^[^:]*://' | sed 's/@.*$//')
DB_HOST=$(echo "$DSN" | sed 's/.*tcp(//' | sed 's/).*//' | cut -d: -f1)
DB_PORT=$(echo "$DSN" | sed 's/.*tcp(//' | sed 's/).*//' | cut -d: -f2)
DB_NAME=$(echo "$DSN" | sed 's/.*\///' | sed 's/?.*//')

echo "  用户: $DB_USER"
echo "  主机: $DB_HOST:$DB_PORT"
echo "  库名: $DB_NAME"
echo ""

# 测试连接（TCP）
echo "--- 测试 TCP 连接（$DB_HOST:$DB_PORT）---"
if mysql -u "$DB_USER" -p"$DB_PASS" -h "$DB_HOST" -P "$DB_PORT" "$DB_NAME" -e "SELECT 1;" 2>&1; then
  info "TCP 连接成功 ✓"
  TCP_OK=true
else
  warn "TCP 连接失败"
  TCP_OK=false
fi

# 测试 socket 连接
echo ""
echo "--- 测试 socket 连接（localhost）---"
if mysql -u "$DB_USER" -p"$DB_PASS" -h localhost "$DB_NAME" -e "SELECT 1;" 2>&1; then
  info "socket 连接成功 ✓"
  SOCK_OK=true
else
  warn "socket 连接失败"
  SOCK_OK=false
fi

# ─────────────────────────────────────────────────────────────────────────────
step "第 3 步：修复数据库用户权限"

echo "检查 MySQL freecdn 用户权限..."
mysql -u root -e "SELECT user, host, plugin FROM mysql.user WHERE user='$DB_USER';" 2>/dev/null || warn "root 无密码登录失败"

echo ""
echo "修复：同时授权 localhost 和 127.0.0.1..."
mysql -u root 2>/dev/null <<SQL || warn "权限修复有警告（可能正常）"
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
CREATE USER IF NOT EXISTS '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASS}';
ALTER USER '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
ALTER USER '${DB_USER}'@'127.0.0.1' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'localhost';
GRANT ALL PRIVILEGES ON \`${DB_NAME}\`.* TO '${DB_USER}'@'127.0.0.1';
FLUSH PRIVILEGES;
SQL
info "数据库用户权限修复完成"

# ─────────────────────────────────────────────────────────────────────────────
step "第 4 步：运行 edge-api upgrade（建表）"

echo "手动运行 edge-api upgrade..."
cd "${API_DIR}"
UPGRADE_OUT="/tmp/fix_upgrade_$$.log"
if ! ./bin/edge-api upgrade > "$UPGRADE_OUT" 2>&1; then
  warn "edge-api upgrade 有警告或错误，输出如下："
  cat "$UPGRADE_OUT"
else
  info "edge-api upgrade 成功"
  tail -5 "$UPGRADE_OUT"
fi
rm -f "$UPGRADE_OUT"
cd - > /dev/null

# ─────────────────────────────────────────────────────────────────────────────
step "第 5 步：检查并修复数据库初始化数据"

echo "检查 edgeAPINodes 表..."
ROW_COUNT=$(mysql -u root "$DB_NAME" -se "SELECT COUNT(*) FROM edgeAPINodes;" 2>/dev/null || echo "0")
echo "  edgeAPINodes 行数: $ROW_COUNT"

echo "检查 edgeAPITokens 表..."
TOK_COUNT=$(mysql -u root "$DB_NAME" -se "SELECT COUNT(*) FROM edgeAPITokens;" 2>/dev/null || echo "0")
echo "  edgeAPITokens 行数: $TOK_COUNT"

echo "检查 edgeAdmins 表..."
ADM_COUNT=$(mysql -u root "$DB_NAME" -se "SELECT COUNT(*) FROM edgeAdmins;" 2>/dev/null || echo "0")
echo "  edgeAdmins 行数: $ADM_COUNT"

# 读取 api.yaml 中的 nodeId/secret
API_YAML="${API_DIR}/configs/api.yaml"
API_ADMIN_YAML="${ADMIN_DIR}/configs/api_admin.yaml"

if [ -f "$API_YAML" ]; then
  API_NODE_ID=$(grep 'nodeId:' "$API_YAML" | awk '{print $2}' | tr -d '"')
  API_SECRET=$(grep 'secret:' "$API_YAML" | awk '{print $2}' | tr -d '"')
  echo ""
  echo "api.yaml: nodeId=$API_NODE_ID"
else
  warn "api.yaml 不存在，将生成新的"
  API_NODE_ID=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
  API_SECRET=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
  cat > "$API_YAML" <<YAML
nodeId: "${API_NODE_ID}"
secret: "${API_SECRET}"
YAML
  info "api.yaml 已生成"
fi

# 确保 edgeAPINodes 有记录
if [ "$ROW_COUNT" = "0" ]; then
  warn "edgeAPINodes 为空，插入初始记录..."
  SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
  mysql -u root "$DB_NAME" 2>&1 <<SQL || warn "插入失败"
INSERT IGNORE INTO edgeAPINodes (id, isOn, uniqueId, name, description, secret, clusterId, http, https, accessAddrs, state, createdAt, updatedAt)
VALUES (
  1,
  1,
  '${API_NODE_ID}',
  'Primary API Node',
  'Auto created by fix script',
  '${API_SECRET}',
  0,
  '{"isOn":true,"listen":[{"protocol":"http","host":"","portRange":"8003","description":""}]}',
  '{}',
  '[{"protocol":"http","host":"${SERVER_IP}","portRange":"8003","description":""}]',
  1,
  UNIX_TIMESTAMP(),
  UNIX_TIMESTAMP()
);
SQL
  info "edgeAPINodes 记录插入完成"
else
  info "edgeAPINodes 已有数据（$ROW_COUNT 行）"
  # 修复 http 字段（protocol 必须为 "http"，不能是空字符串）
  mysql -u root "$DB_NAME" 2>/dev/null <<SQL || true
UPDATE edgeAPINodes
SET http='{"isOn":true,"listen":[{"protocol":"http","host":"","portRange":"8003","description":""}]}'
WHERE JSON_UNQUOTE(JSON_EXTRACT(http, '$.listen[0].protocol')) = '' OR http IS NULL OR http='{}' OR http='';
SQL
fi

# 确保 edgeAPITokens 有 admin token
if [ "$TOK_COUNT" = "0" ] || ! mysql -u root "$DB_NAME" -se "SELECT COUNT(*) FROM edgeAPITokens WHERE role='admin';" 2>/dev/null | grep -q "^[1-9]"; then
  warn "edgeAPITokens 缺少 admin token，插入..."

  # 读取 api_admin.yaml 中的已有 token（如果有）
  if [ -f "$API_ADMIN_YAML" ]; then
    ADM_NODE_ID=$(grep 'nodeId:' "$API_ADMIN_YAML" | awk '{print $2}' | tr -d '"')
    ADM_SECRET=$(grep 'secret:' "$API_ADMIN_YAML" | awk '{print $2}' | tr -d '"')
    echo "  从 api_admin.yaml 读取 token: nodeId=$ADM_NODE_ID"
  else
    ADM_NODE_ID=$(cat /proc/sys/kernel/random/uuid | tr -d '-')
    set +o pipefail
    ADM_SECRET=$(tr -dc 'A-Za-z0-9' < /dev/urandom | head -c 32)
    set -o pipefail
    warn "api_admin.yaml 不存在，生成新 token"
  fi

  mysql -u root "$DB_NAME" 2>&1 <<SQL || warn "插入 admin token 失败"
INSERT IGNORE INTO edgeAPITokens (nodeId, secret, role, state)
VALUES ('${ADM_NODE_ID}', '${ADM_SECRET}', 'admin', 1);
SQL

  # 写 api_admin.yaml
  cat > "$API_ADMIN_YAML" <<YAML
rpc:
  endpoints:
    - "http://127.0.0.1:8003"
nodeId: "${ADM_NODE_ID}"
secret: "${ADM_SECRET}"
YAML
  info "api_admin.yaml 已更新"
else
  info "edgeAPITokens admin token 已存在（$TOK_COUNT 行）"
  # 检查 api_admin.yaml 与数据库是否一致
  if [ -f "$API_ADMIN_YAML" ]; then
    ADM_NODE_ID=$(grep 'nodeId:' "$API_ADMIN_YAML" | awk '{print $2}' | tr -d '"')
    DB_MATCH=$(mysql -u root "$DB_NAME" -se "SELECT COUNT(*) FROM edgeAPITokens WHERE nodeId='${ADM_NODE_ID}' AND role='admin';" 2>/dev/null || echo "0")
    if [ "$DB_MATCH" = "0" ]; then
      warn "api_admin.yaml 中的 nodeId 与数据库不匹配，修复..."
      # 取数据库中的实际 admin token
      ADM_NODE_ID=$(mysql -u root "$DB_NAME" -se "SELECT nodeId FROM edgeAPITokens WHERE role='admin' LIMIT 1;" 2>/dev/null || echo "")
      ADM_SECRET=$(mysql -u root "$DB_NAME" -se "SELECT secret FROM edgeAPITokens WHERE role='admin' LIMIT 1;" 2>/dev/null || echo "")
      if [ -n "$ADM_NODE_ID" ]; then
        cat > "$API_ADMIN_YAML" <<YAML
rpc:
  endpoints:
    - "http://127.0.0.1:8003"
nodeId: "${ADM_NODE_ID}"
secret: "${ADM_SECRET}"
YAML
        info "api_admin.yaml 已与数据库同步"
      fi
    else
      info "api_admin.yaml 与数据库一致 ✓"
    fi
  fi
fi

# 确保 edgeAdmins 有管理员
if [ "$ADM_COUNT" = "0" ]; then
  warn "edgeAdmins 为空，创建管理员账号..."
  ADMIN_PASSWORD="FreeCDN2026!"
  ADMIN_MD5=$(echo -n "$ADMIN_PASSWORD" | md5sum | cut -d' ' -f1)
  mysql -u root "$DB_NAME" 2>&1 <<SQL || warn "插入管理员失败"
INSERT IGNORE INTO edgeAdmins (id, isOn, username, password, isSuper, state, createdAt, updatedAt, canLogin)
VALUES (1, 1, 'admin', '${ADMIN_MD5}', 1, 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 1);
SQL
  info "管理员账号: admin / ${ADMIN_PASSWORD}"
else
  info "edgeAdmins 已有账号（$ADM_COUNT 行）"
fi

# ─────────────────────────────────────────────────────────────────────────────
step "第 6 步：验证配置文件"

echo "--- server.yaml ---"
cat "${ADMIN_DIR}/configs/server.yaml" 2>/dev/null || warn "server.yaml 不存在"

echo ""
echo "--- api_admin.yaml ---"
cat "${ADMIN_DIR}/configs/api_admin.yaml" 2>/dev/null || warn "api_admin.yaml 不存在"

echo ""
echo "--- db.yaml ---"
cat "${API_DIR}/configs/db.yaml" 2>/dev/null || warn "db.yaml 不存在"

echo ""
echo "--- api.yaml ---"
cat "${API_DIR}/configs/api.yaml" 2>/dev/null || warn "api.yaml 不存在"

# ─────────────────────────────────────────────────────────────────────────────
step "第 7 步：重启服务"

echo "停止 freecdn-admin..."
systemctl stop freecdn-admin 2>/dev/null || true
sleep 2

# 确认没有残留进程
pkill -f 'edge-admin' 2>/dev/null || true
pkill -f 'edge-api' 2>/dev/null || true
sleep 1

echo "启动 freecdn-admin..."
systemctl start freecdn-admin
sleep 5

echo ""
echo "--- 服务状态 ---"
systemctl status freecdn-admin --no-pager -l | head -20

echo ""
echo "--- 端口监听 ---"
ss -tlnp | grep -E '7788|8003' || echo "端口未监听，服务可能还在启动中"

echo ""
echo "--- 等待就绪（最多 30 秒）---"
for i in $(seq 1 10); do
  if curl -sf --connect-timeout 2 "http://127.0.0.1:7788/" > /dev/null 2>&1; then
    info "✓ 管理后台 7788 端口已就绪！"
    break
  fi
  if ss -tlnp | grep -q ':8003'; then
    info "✓ edge-api 8003 端口已监听"
  fi
  echo "  等待中... ($i/10)"
  sleep 3
done

echo ""
echo "--- 最新日志 ---"
journalctl -u freecdn-admin -n 20 --no-pager 2>/dev/null || \
  cat "${ADMIN_DIR}/logs/run.log" 2>/dev/null | tail -20 || true

echo ""
echo -e "${GREEN}${BOLD}══════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  修复脚本执行完成${NC}"
echo -e "${GREEN}${BOLD}══════════════════════════════════════${NC}"
echo ""
echo "如果仍有问题，请提供以上输出内容排查。"
echo ""
echo "快速验证命令："
echo "  curl -I http://127.0.0.1:7788/"
echo "  ss -tlnp | grep -E '7788|8003'"
echo "  journalctl -u freecdn-admin -f"
