#!/bin/bash
# ============================================================
# FreeCDN 停止脚本（WSL2 本地环境）
# 用法: wsl -u root bash /mnt/c/.../FreeCDN/deploy/stop.sh
# ============================================================

GOEDGE="/home/huhuhu/freecdn/goedge"

echo "[$(date '+%F %T')] Stopping FreeCDN..."

# 停止 GoEdge 服务
for svc in edge-node edge-api edge-admin; do
    if pgrep -x $svc >/dev/null 2>&1; then
        echo "Stopping $svc..."
        su -s /bin/bash huhuhu -c "cd $GOEDGE/$svc && ./bin/$svc stop" 2>/dev/null || pkill -x $svc
    fi
done

# 停止测试源站
pkill -f "python3 -m http.server 8080" 2>/dev/null || true

echo "[$(date '+%F %T')] FreeCDN stopped."
