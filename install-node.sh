#!/bin/bash
# ==============================================================================
# FreeCDN 边缘节点快速安装脚本
# 由管理后台「节点 -> 安装」页面自动生成
#
# 用法：
#   bash <(curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install-node.sh) \
#     --api-endpoint http://ADMIN_IP:8003 \
#     --node-id NODE_ID \
#     --node-secret NODE_SECRET
# ==============================================================================

curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh \
  | bash -s -- --node "$@"
