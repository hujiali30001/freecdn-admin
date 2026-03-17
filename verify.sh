#!/bin/bash
echo "=== 检查侧边栏渐变背景 ==="
grep "linear-gradient.*180deg" /usr/local/freecdn/edge-admin/web/views/@default/@layout.css
echo ""
echo "=== 检查 body 渐变背景 ==="
grep -A1 "^body {" /usr/local/freecdn/edge-admin/web/views/@default/@layout.css
