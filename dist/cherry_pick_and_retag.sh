#!/bin/bash
set -e

REPO=/tmp/freecdn-b/EdgeCommon
CHERRY_HASH=7ed7574dde08def89f6cdca20efa93620b0c4618
TOKEN=$1

export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780
export GIT_AUTHOR_NAME="hujiali30001"
export GIT_AUTHOR_EMAIL="79893530@qq.com"
export GIT_COMMITTER_NAME="hujiali30001"
export GIT_COMMITTER_EMAIL="79893530@qq.com"

echo "=== [1] checkout freecdn-v1.3.9 ==="
cd $REPO
git checkout freecdn-v1.3.9

echo "=== [2] cherry-pick FreeCDN compatibility commit ==="
git cherry-pick $CHERRY_HASH

echo "=== [3] delete old tag v1.3.9-freecdn.1 locally ==="
git tag -d v1.3.9-freecdn.1 2>/dev/null || true

echo "=== [4] create new tag v1.3.9-freecdn.1 at HEAD ==="
git tag v1.3.9-freecdn.1

echo "=== [5] push branch freecdn-v1.3.9 ==="
git push https://${TOKEN}@github.com/hujiali30001/EdgeCommon.git freecdn-v1.3.9 --force

echo "=== [6] delete old tag on remote ==="
git push https://${TOKEN}@github.com/hujiali30001/EdgeCommon.git :refs/tags/v1.3.9-freecdn.1 2>/dev/null || true

echo "=== [7] push new tag ==="
git push https://${TOKEN}@github.com/hujiali30001/EdgeCommon.git v1.3.9-freecdn.1

echo "=== New HEAD ==="
git log --oneline -3
