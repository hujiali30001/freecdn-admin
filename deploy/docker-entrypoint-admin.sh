#!/bin/bash
# ==============================================================
# FreeCDN Admin + API 容器入口脚本
#
# 负责：
#   1. 根据环境变量生成配置文件（configs/）
#   2. 前台运行 edge-admin（它会自动 fork edge-api）
#
# 环境变量：
#   MYSQL_HOST      MySQL 主机名（默认：mysql）
#   MYSQL_PORT      MySQL 端口（默认：3306）
#   MYSQL_USER      MySQL 用户（默认：freecdn）
#   MYSQL_PASSWORD  MySQL 密码（默认：freecdn_pass_2026）
#   MYSQL_DATABASE  MySQL 数据库（默认：freecdn）
#   ADMIN_HTTP_PORT 管理后台端口（默认：7788）
#   API_RPC_PORT    EdgeAPI RPC 端口（默认：8003）
#   TZ              时区（默认：Asia/Shanghai）
# ==============================================================
set -e

WORKDIR=/app/edge-admin

# ---- 环境变量默认值 ----
MYSQL_HOST="${MYSQL_HOST:-mysql}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-freecdn}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-freecdn_pass_2026}"
MYSQL_DATABASE="${MYSQL_DATABASE:-freecdn}"
ADMIN_HTTP_PORT="${ADMIN_HTTP_PORT:-7788}"
API_RPC_PORT="${API_RPC_PORT:-8003}"

echo "[entrypoint] FreeCDN Admin starting..."
echo "[entrypoint] MySQL: ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}"
echo "[entrypoint] Admin port: ${ADMIN_HTTP_PORT}, API RPC port: ${API_RPC_PORT}"

# ---- 生成 server.yaml（edge-admin HTTP 监听配置）----
cat > ${WORKDIR}/configs/server.yaml << EOF
env: prod

http:
  "on": true
  listen: [ "0.0.0.0:${ADMIN_HTTP_PORT}" ]

https:
  "on": false
  listen: [ "0.0.0.0:443" ]
  cert: ""
  key: ""
EOF
echo "[entrypoint] Generated configs/server.yaml"

# ---- 生成 api_db.yaml（edge-admin 数据库连接，用于页面展示）----
cat > ${WORKDIR}/configs/api_db.yaml << EOF
default:
  db: "prod"
  prefix: ""

dbs:
  prod:
    driver: "mysql"
    dsn: "${MYSQL_USER}:${MYSQL_PASSWORD}@tcp(${MYSQL_HOST}:${MYSQL_PORT})/${MYSQL_DATABASE}?charset=utf8mb4&timeout=30s&multiStatements=true"
    prefix: "edge"
    models:
      package: internal/web/models
EOF
echo "[entrypoint] Generated configs/api_db.yaml"

# ---- 生成 api_admin.yaml（edge-admin 连接 edge-api 的 RPC 地址）----
# 首次启动时 nodeId/secret 为空，向导完成后会自动写入
if [ ! -f "${WORKDIR}/configs/api_admin.yaml" ] || ! grep -q "nodeId:" "${WORKDIR}/configs/api_admin.yaml" 2>/dev/null; then
  cat > ${WORKDIR}/configs/api_admin.yaml << EOF
rpc.endpoints: [ "http://127.0.0.1:${API_RPC_PORT}" ]
nodeId: ""
secret: ""
EOF
  echo "[entrypoint] Generated configs/api_admin.yaml (fresh install)"
else
  # 已安装过，只更新 RPC 端口，保留 nodeId 和 secret
  NODE_ID=$(grep "nodeId:" ${WORKDIR}/configs/api_admin.yaml | awk '{print $2}')
  SECRET=$(grep "secret:" ${WORKDIR}/configs/api_admin.yaml | awk '{print $2}')
  cat > ${WORKDIR}/configs/api_admin.yaml << EOF
rpc.endpoints: [ "http://127.0.0.1:${API_RPC_PORT}" ]
nodeId: ${NODE_ID}
secret: ${SECRET}
EOF
  echo "[entrypoint] Updated configs/api_admin.yaml (keeping nodeId/secret)"
fi

# ---- 生成 edge-api/configs/db.yaml ----
cat > ${WORKDIR}/edge-api/configs/db.yaml << EOF
user: ${MYSQL_USER}
password: ${MYSQL_PASSWORD}
host: ${MYSQL_HOST}:${MYSQL_PORT}
database: ${MYSQL_DATABASE}
EOF
echo "[entrypoint] Generated edge-api/configs/db.yaml"

# ---- 等待 MySQL 就绪（double-check，docker compose healthcheck 已保障大部分情况）----
echo "[entrypoint] Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT}..."
MAX_WAIT=30
COUNT=0
until curl -sf --connect-timeout 1 "telnet://${MYSQL_HOST}:${MYSQL_PORT}" > /dev/null 2>&1; do
  COUNT=$((COUNT+1))
  if [ $COUNT -ge $MAX_WAIT ]; then
    echo "[entrypoint] MySQL not responding after ${MAX_WAIT}s, starting anyway..."
    break
  fi
  echo "[entrypoint] Waiting for MySQL... (${COUNT}/${MAX_WAIT})"
  sleep 1
done
echo "[entrypoint] Proceeding to start edge-admin..."

# ---- 前台运行 edge-admin ----
# edge-admin 会自动检测 edge-api/ 子目录并 fork edge-api 子进程
echo "[entrypoint] Starting edge-admin..."
exec ${WORKDIR}/bin/edge-admin
