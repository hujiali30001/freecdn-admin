#!/bin/bash
# ============================================================
# FreeCDN 状态检查脚本
# 用法: wsl -u huhuhu bash /mnt/c/.../FreeCDN/deploy/status.sh
# ============================================================

echo "============================="
echo "  FreeCDN Service Status"
echo "============================="

# 进程状态
echo ""
echo "[ Processes ]"
for svc in edge-admin edge-api edge-node python3; do
    if pgrep -x $svc >/dev/null 2>&1; then
        pid=$(pgrep -x $svc | head -1)
        echo "  ✓ $svc (PID $pid)"
    else
        echo "  ✗ $svc NOT running"
    fi
done

# 端口监听
echo ""
echo "[ Ports ]"
for port in 7788 8003 8080 8888; do
    if ss -tlnp 2>/dev/null | grep -q ":$port"; then
        svc=$(ss -tlnp 2>/dev/null | grep ":$port" | grep -oP 'users:\(\("\K[^"]+' | head -1)
        echo "  ✓ :$port  ($svc)"
    else
        echo "  ✗ :$port  (not listening)"
    fi
done

# Docker 容器
echo ""
echo "[ Docker ]"
docker ps --format "  {{.Names}}  {{.Status}}" 2>/dev/null | grep freecdn | while read line; do
    if echo "$line" | grep -q "Up"; then
        echo "  ✓ $line"
    else
        echo "  ✗ $line"
    fi
done || echo "  (no freecdn containers)"

# CDN 测试
echo ""
echo "[ CDN Proxy Test ]"
result=$(curl -si -H "Host: test.cdn.local" http://127.0.0.1:8888/ 2>/dev/null | grep -E "^HTTP|X-Cache" | tr '\r\n' ' ')
if echo "$result" | grep -q "200"; then
    echo "  ✓ $result"
else
    echo "  ✗ $result"
fi

echo ""
