#!/bin/bash
# ==============================================================
# FreeCDN Node 容器入口脚本
#
# 环境变量（必填）：
#   API_ENDPOINTS   EdgeAPI 的 RPC 地址，如 http://192.168.1.1:8003
#   NODE_ID         节点 ID（在管理后台"节点安装"页面获取）
#   NODE_SECRET     节点密钥（在管理后台"节点安装"页面获取）
#
# 可选：
#   TZ              时区（默认：Asia/Shanghai）
# ==============================================================
set -e

WORKDIR=/app/edge-node

echo "[entrypoint] FreeCDN Node starting..."

# ---- 校验必填参数 ----
if [ -z "${API_ENDPOINTS}" ]; then
  echo "[entrypoint] ERROR: API_ENDPOINTS is required."
  echo "[entrypoint]   Example: -e API_ENDPOINTS=http://192.168.1.1:8003"
  echo "[entrypoint] Get it from FreeCDN Admin -> Node -> Install page."
  exit 1
fi

if [ -z "${NODE_ID}" ] || [ -z "${NODE_SECRET}" ]; then
  echo "[entrypoint] ERROR: NODE_ID and NODE_SECRET are required."
  echo "[entrypoint]   Get them from FreeCDN Admin -> Node -> Install page."
  exit 1
fi

# ---- 生成 api_node.yaml ----
cat > ${WORKDIR}/configs/api_node.yaml << EOF
rpc.endpoints: [ "${API_ENDPOINTS}" ]
nodeId: "${NODE_ID}"
secret: "${NODE_SECRET}"
EOF
echo "[entrypoint] Generated configs/api_node.yaml"
echo "[entrypoint] API: ${API_ENDPOINTS}"
echo "[entrypoint] Node ID: ${NODE_ID}"

# ---- 前台运行 edge-node ----
echo "[entrypoint] Starting edge-node..."
exec ${WORKDIR}/bin/edge-node
