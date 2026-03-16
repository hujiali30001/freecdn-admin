#!/bin/bash
# Build freecdn-api and freecdn-node with new EdgeCommon v1.3.9-freecdn.2

TOKEN=$1
export PATH=/usr/local/go/bin:/usr/bin:/bin
export GOOS=linux GOARCH=amd64 CGO_ENABLED=0
export GOFLAGS=-mod=mod
export GOPROXY=https://proxy.golang.org,direct
export GOPRIVATE=github.com/hujiali30001/*
export GONOSUMDB=github.com/hujiali30001/*
export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780
export GIT_AUTHOR_NAME="hujiali30001"
export GIT_AUTHOR_EMAIL="79893530@qq.com"

git config --global safe.directory "*"

echo "=== [1] Clone freecdn-api ==="
rm -rf /tmp/fc_api
git clone https://${TOKEN}@github.com/hujiali30001/freecdn-api.git /tmp/fc_api 2>&1
git -C /tmp/fc_api log --oneline -3

echo "=== [2] Clone freecdn-node ==="
rm -rf /tmp/fc_node
git clone https://${TOKEN}@github.com/hujiali30001/freecdn-node.git /tmp/fc_node 2>&1
git -C /tmp/fc_node log --oneline -3

echo "=== [3] Build freecdn-api ==="
cd /tmp/fc_api
go build ./cmd/... 2>&1
echo "freecdn-api exit: $?"

echo "=== [4] Build freecdn-node (CGO required) ==="
export CGO_ENABLED=1
cd /tmp/fc_node
go build ./cmd/... 2>&1
echo "freecdn-node exit: $?"
