@echo off
set GOPATH=C:\Users\Administrator\go
set GOPROXY=https://goproxy.cn,direct
set GONOSUMDB=*
set GOOS=linux
set GOARCH=amd64
set CGO_ENABLED=0
set GOFLAGS=-mod=mod

echo [1/2] go mod download...
cd /d C:\Users\Administrator\.workbuddy\FreeCDN
C:\Go_temp\go\bin\go.exe mod download 2>&1
if errorlevel 1 (
    echo [!] mod download failed
    exit /b 1
)

echo [2/2] building edge-admin for linux/amd64...
C:\Go_temp\go\bin\go.exe build -o C:\Temp\edge-admin-linux-amd64 ./cmd/edge-admin/ 2>&1
if errorlevel 1 (
    echo [!] build failed
    exit /b 1
)

echo [OK] Build succeeded!
dir C:\Temp\edge-admin-linux-amd64
