#!/bin/bash
# ==============================================================
# FreeCDN Docker 镜像构建脚本
# 在 WSL 里运行，因为源文件在 WSL 文件系统
#
# 用法：
#   wsl -u huhuhu bash /mnt/c/Users/Administrator/.workbuddy/FreeCDN/deploy/docker-build.sh
# ==============================================================
set -e
export PATH=$PATH:/usr/local/go/bin

FREECDN_BASE=/home/huhuhu/freecdn
SCRIPTS_DIR=/mnt/c/Users/Administrator/.workbuddy/FreeCDN

echo "============================================="
echo "  FreeCDN Docker Build"
echo "============================================="

# ---- 创建临时 build context 目录 ----
BUILD_CTX=/tmp/freecdn-docker-build
rm -rf "$BUILD_CTX"
mkdir -p "$BUILD_CTX"

echo "[1/5] Preparing build context at $BUILD_CTX ..."

# 复制二进制和静态文件
mkdir -p "$BUILD_CTX/goedge/edge-admin/bin"
mkdir -p "$BUILD_CTX/goedge/edge-admin/web"
mkdir -p "$BUILD_CTX/goedge/edge-api/bin"
mkdir -p "$BUILD_CTX/goedge/edge-node/bin"
mkdir -p "$BUILD_CTX/deploy"

cp "$FREECDN_BASE/goedge/edge-admin/bin/edge-admin"  "$BUILD_CTX/goedge/edge-admin/bin/"
cp -r "$FREECDN_BASE/goedge/edge-admin/web/."        "$BUILD_CTX/goedge/edge-admin/web/"
cp "$FREECDN_BASE/goedge/edge-api/bin/edge-api"      "$BUILD_CTX/goedge/edge-api/bin/"
cp "$FREECDN_BASE/goedge/edge-node/bin/edge-node"    "$BUILD_CTX/goedge/edge-node/bin/"

# 复制 Dockerfile 和 entrypoint 脚本
cp "$SCRIPTS_DIR/deploy/Dockerfile"                  "$BUILD_CTX/deploy/"
cp "$SCRIPTS_DIR/deploy/Dockerfile.node"             "$BUILD_CTX/deploy/"
cp "$SCRIPTS_DIR/deploy/docker-entrypoint-admin.sh"  "$BUILD_CTX/deploy/"
cp "$SCRIPTS_DIR/deploy/docker-entrypoint-node.sh"   "$BUILD_CTX/deploy/"

echo "[2/5] Build context size: $(du -sh $BUILD_CTX | cut -f1)"

# ---- 构建 freecdn/admin 镜像 ----
echo "[3/5] Building freecdn/admin:latest ..."
docker build \
  -f "$BUILD_CTX/deploy/Dockerfile" \
  -t freecdn/admin:latest \
  "$BUILD_CTX"
echo "      freecdn/admin:latest - OK"

# ---- 构建 freecdn/node 镜像 ----
echo "[4/5] Building freecdn/node:latest ..."
docker build \
  -f "$BUILD_CTX/deploy/Dockerfile.node" \
  -t freecdn/node:latest \
  "$BUILD_CTX"
echo "      freecdn/node:latest - OK"

# ---- 清理 ----
echo "[5/5] Cleaning up build context..."
rm -rf "$BUILD_CTX"

echo ""
echo "============================================="
echo "  Build Complete!"
echo "============================================="
docker images | grep freecdn
echo ""
echo "Next: cd deploy && docker compose up -d"
