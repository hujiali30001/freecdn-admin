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
