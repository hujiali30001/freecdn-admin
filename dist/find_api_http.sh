#!/bin/bash
grep -r 'ListenAndServe\|http.HandleFunc\|HTTPServer\|gRPC\|grpcServer\|ListenAndServeTLS' /tmp/freecdn-b/freecdn-api/internal/nodes/ 2>/dev/null
echo "---go.mod---"
head -5 /tmp/freecdn-b/freecdn-api/go.mod
