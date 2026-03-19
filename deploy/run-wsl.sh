#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

ADMIN_USERNAME="${ADMIN_USERNAME:-admin}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-huhuhu}"
ADMIN_PORT="${ADMIN_PORT:-17788}"
API_PORT="${API_PORT:-18003}"
FREECDN_VERSION="${FREECDN_VERSION:-v0.11.0}"

if [ -z "${ADMIN_PASSWORD}" ]; then
  echo "ADMIN_PASSWORD 不能为空"
  exit 1
fi

export ADMIN_USERNAME ADMIN_PASSWORD ADMIN_PORT API_PORT FREECDN_VERSION
docker compose up -d --build
docker compose ps

WSL_IP="$(hostname -I | awk '{print $1}')"
echo ""
echo "FreeCDN 已启动"
echo "用户名: ${ADMIN_USERNAME}"
echo "密码: ${ADMIN_PASSWORD}"
echo "Windows 访问: http://127.0.0.1:${ADMIN_PORT}"
if [ -n "${WSL_IP}" ]; then
  echo "WSL 内访问: http://${WSL_IP}:${ADMIN_PORT}"
fi
