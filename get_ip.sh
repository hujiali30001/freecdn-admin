#!/bin/bash
# 获取 WSL IP 并清理浏览器缓存
WSL_IP=$(hostname -I | awk '{print $1}')
echo "WSL_IP=$WSL_IP"

# 清理 Chrome 缓存以强制重新加载（可选）
curl -s -I "http://${WSL_IP}:7788/" | head -1
