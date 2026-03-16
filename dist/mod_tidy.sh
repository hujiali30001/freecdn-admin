#!/bin/bash
export PATH=/usr/local/go/bin:/usr/bin:/bin
export GOOS=linux GOARCH=amd64 CGO_ENABLED=0
export GOFLAGS=-mod=mod
export GOPROXY=https://proxy.golang.org,direct
export GOPRIVATE=github.com/hujiali30001/*
export GONOSUMDB=github.com/hujiali30001/*
export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780

echo "=== go mod tidy (freecdn-admin) ==="
cd /mnt/c/Users/Administrator/.workbuddy/FreeCDN
go mod tidy 2>&1
echo "tidy exit: $?"
