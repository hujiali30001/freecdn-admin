#!/bin/bash
set -e
TOKEN="$1"
HOST_IP=172.24.208.1
export PATH=/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export HTTPS_PROXY=http://${HOST_IP}:4780 HTTP_PROXY=http://${HOST_IP}:4780
export GOPROXY=https://proxy.golang.org,direct
export GOFLAGS=-mod=mod
export CGO_ENABLED=0
export GOOS=linux GOARCH=amd64

echo "=== Checking/updating repos ==="
for repo in api node; do
    REPO_URL="https://${TOKEN}@github.com/hujiali30001/freecdn-${repo}.git"
    DIR="/tmp/freecdn-build/${repo}"
    if [ -d "${DIR}/.git" ]; then
        echo "Updating $repo..."
        cd "$DIR"
        git fetch origin master
        git reset --hard FETCH_HEAD
    else
        echo "Cloning $repo..."
        mkdir -p /tmp/freecdn-build
        git clone --branch master "$REPO_URL" "$DIR"
    fi
done

echo ""
echo "=== Building freecdn-api ==="
cd /tmp/freecdn-build/api
go mod download
go build ./cmd/...
echo "[BUILD OK] freecdn-api"

echo ""
echo "=== Building freecdn-node (CGO) ==="
export CGO_ENABLED=1
go mod download
go build ./cmd/...
echo "[BUILD OK] freecdn-node"
