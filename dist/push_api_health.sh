#!/bin/bash
# 将 /tmp/freecdn-b/freecdn-api 的 health 端点改动 commit + push
TOKEN=$1
export PATH=/usr/local/go/bin:/usr/bin:/bin
export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780
export GIT_AUTHOR_NAME="hujiali30001"
export GIT_AUTHOR_EMAIL="79893530@qq.com"
export GIT_COMMITTER_NAME="hujiali30001"
export GIT_COMMITTER_EMAIL="79893530@qq.com"

cd /tmp/freecdn-b/freecdn-api

git config user.name "hujiali30001"
git config user.email "79893530@qq.com"

# 设置 remote URL（带 token）
git remote set-url origin https://${TOKEN}@github.com/hujiali30001/freecdn-api.git

git add internal/nodes/api_node.go
git status --short
git commit -m "feat: add /health HTTP endpoint on port 8004 (C-3)"
git push origin main
echo "push exit: $?"
