#!/bin/bash
# ============================================================
# FreeCDN 完整启动脚本（WSL2 本地环境）
# 适用于：首次启动 或 WSL 重启后手动恢复服务
#
# 用法:
#   wsl -u root bash /mnt/c/Users/Administrator/.workbuddy/FreeCDN/deploy/start.sh
#
# 自动完成：
#   1. 启动 Docker 服务
#   2. 启动 MySQL 容器 (freecdn-mysql)
#   3. 启动测试源站 Python HTTP 服务 (:8080)
#   4. 启动 GoEdge edge-api (:8003)
#   5. 启动 GoEdge edge-node (:8888)
#   6. 启动 GoEdge edge-admin (:7800/:7802)
# ============================================================

set -e

LOG="/tmp/freecdn-start.log"
exec >> "$LOG" 2>&1

log() {
    echo "[$(date '+%F %T')] $*"
}

log "=== FreeCDN Starting ==="

# 1. 启动 Docker
if ! service docker status >/dev/null 2>&1; then
    log "Starting Docker service..."
    service docker start
    sleep 5
fi
log "Docker OK"

# 2. 启动 MySQL 容器
if ! docker ps --format "{{.Names}}" 2>/dev/null | grep -q "freecdn-mysql"; then
    log "Starting MySQL container..."
    docker start freecdn-mysql
    sleep 8
else
    log "MySQL already running"
fi

# 3. 启动测试源站 (8080)
if ! ss -tlnp 2>/dev/null | grep -q ":8080"; then
    log "Starting test origin on :8080..."
    mkdir -p /home/huhuhu/freecdn/origin
    touch /home/huhuhu/freecdn/origin/access.log
    if [ ! -f /home/huhuhu/freecdn/origin/index.html ]; then
        cat > /home/huhuhu/freecdn/origin/index.html << 'HTML'
<!DOCTYPE html>
<html>
<head><title>GoEdge Test Origin</title></head>
<body>
<h1>Hello from GoEdge Origin!</h1>
<p>This is the origin server. If you see this through CDN, the proxy is working!</p>
</body>
</html>
HTML
    fi
    setsid python3 -m http.server 8080 \
        --directory /home/huhuhu/freecdn/origin \
        >> /home/huhuhu/freecdn/origin/access.log 2>&1 &
    disown $!
    log "Test origin PID=$!"
else
    log "Test origin already running"
fi

GOEDGE="/home/huhuhu/freecdn/goedge"

# 4. 启动 edge-api
if ! pgrep -x edge-api >/dev/null; then
    log "Starting edge-api..."
    su -s /bin/bash huhuhu -c "cd $GOEDGE/edge-api && ./bin/edge-api start"
    sleep 5
else
    log "edge-api already running"
fi

# 5. 启动 edge-node
if ! pgrep -x edge-node >/dev/null; then
    log "Starting edge-node..."
    su -s /bin/bash huhuhu -c "cd $GOEDGE/edge-node && ./bin/edge-node start"
    sleep 3
else
    log "edge-node already running"
fi

# 6. 启动 edge-admin
if ! pgrep -x edge-admin >/dev/null; then
    log "Starting edge-admin..."
    su -s /bin/bash huhuhu -c "cd $GOEDGE/edge-admin && ./bin/edge-admin start"
else
    log "edge-admin already running"
fi

log "=== FreeCDN Started ==="

# 最终状态汇报
sleep 3
log "--- Service Status ---"
pgrep -a edge 2>/dev/null || true
ss -tlnp 2>/dev/null | grep -E ':8003|:8888|:8080|:7800|:7802' || true
log "--- Startup log: $LOG ---"
