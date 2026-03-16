#!/bin/bash

REPO=/mnt/c/Users/Administrator/.workbuddy/FreeCDN
export PATH=/usr/local/go/bin:/usr/bin:/bin
export GOOS=linux GOARCH=amd64 CGO_ENABLED=0
export GOFLAGS=-mod=mod
export GOPROXY=https://proxy.golang.org,direct
export GONOSUMCHECK=github.com/hujiali30001/*
export GONOSUMDB=github.com/hujiali30001/*
export GOPRIVATE=github.com/hujiali30001/*
export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780

echo "=== Clearing module cache for hujiali30001 ===" 2>&1
rm -rf /root/go/pkg/mod/cache/download/github.com/hujiali30001 2>/dev/null
rm -rf /root/go/pkg/mod/github.com/hujiali30001 2>/dev/null
echo "Cache cleared"

echo "=== Verifying EdgeCommon tag content (direct from GitHub) ==="
rm -rf /tmp/ec_verify 2>/dev/null
git clone --branch v1.3.9-freecdn.1 --depth 1 https://github.com/hujiali30001/EdgeCommon.git /tmp/ec_verify 2>&1 || true
if grep -r "DenyProviderIds" /tmp/ec_verify/pkg/serverconfigs/firewallconfigs/ 2>/dev/null | head -1; then
  echo "[OK] DenyProviderIds found in tag"
else
  echo "[FAIL] DenyProviderIds NOT found in tag - need to re-tag!"
  git -C /tmp/ec_verify log --oneline -3 2>/dev/null || true
  exit 1
fi

echo "=== go mod tidy to refresh ==="
cd $REPO
go mod tidy 2>&1 || true

echo "=== Building freecdn-admin ==="
cd $REPO
go build ./cmd/... 2>&1
RET=$?
if [ $RET -eq 0 ]; then
  echo "[OK] freecdn-admin build PASSED"
else
  echo "[FAIL] freecdn-admin build FAILED (exit $RET)"
fi
exit $RET
