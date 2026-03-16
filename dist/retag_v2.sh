#!/bin/bash
# Re-tag EdgeCommon with a NEW tag name to bypass proxy.golang.org immutable cache
# The old v1.3.9-freecdn.1 was cached BEFORE cherry-pick, so we use v1.3.9-freecdn.2

set -e
TOKEN=$1
REPO=/tmp/freecdn-b/EdgeCommon
export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780
export GIT_AUTHOR_NAME="hujiali30001"
export GIT_AUTHOR_EMAIL="79893530@qq.com"

echo "=== Current HEAD of freecdn-v1.3.9 ==="
git -C $REPO log --oneline -3

echo "=== Tagging HEAD as v1.3.9-freecdn.2 ==="
git -C $REPO tag -d v1.3.9-freecdn.2 2>/dev/null || true
git -C $REPO tag v1.3.9-freecdn.2

echo "=== Pushing tag ==="
git -C $REPO push https://${TOKEN}@github.com/hujiali30001/EdgeCommon.git :refs/tags/v1.3.9-freecdn.2 2>/dev/null || true
git -C $REPO push https://${TOKEN}@github.com/hujiali30001/EdgeCommon.git v1.3.9-freecdn.2

echo "=== Done. New tag v1.3.9-freecdn.2 pushed ==="
