#!/bin/bash
# 在 freecdn-api api_node.go 的 Start() 末尾（select{} 之前）插入 health HTTP server
FILE=/tmp/freecdn-b/freecdn-api/internal/nodes/api_node.go

# 确认目标行
if ! grep -q "// 保持进程" "$FILE"; then
  echo "ERROR: marker not found"
  exit 1
fi

# 用 Python 做精确插入（避免 sed 多行匹配问题）
python3 - "$FILE" <<'PYEOF'
import sys

path = sys.argv[1]
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

OLD = "\t// 保持进程\n\tselect {}"
NEW = """\t// 健康检查 HTTP 端点（/health），供 install.sh / Docker healthcheck 使用
\tgoman.New(func() {
\t\tvar healthMux = http.NewServeMux()
\t\thealthMux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
\t\t\tw.Header().Set("Content-Type", "application/json; charset=utf-8")
\t\t\tw.WriteHeader(http.StatusOK)
\t\t\t_, _ = w.Write([]byte(`{"status":"ok","service":"freecdn-api","version":"` + teaconst.Version + `"}`))
\t\t})
\t\tvar healthServer = &http.Server{Handler: healthMux}
\t\thealthListener, err := net.Listen("tcp", ":8004")
\t\tif err == nil {
\t\t\t_ = healthServer.Serve(healthListener)
\t\t}
\t})

\t// 保持进程
\tselect {}"""

if OLD not in content:
    print("ERROR: old string not found")
    sys.exit(1)

content = content.replace(OLD, NEW, 1)

# 确保 net/http 已在 import 中（已有 "net" 和 grpc，但 "net/http" 需要检查）
if '"net/http"' not in content:
    # 在 import ( 后找到第一个 "net" 并在其后加 "net/http"
    content = content.replace('"net"', '"net"\n\t"net/http"', 1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("OK: health server inserted")
PYEOF
