#!/bin/bash
# FreeCDN UI CSS 部署脚本

echo "============================================================"
echo "FreeCDN UI CSS 部署脚本"
echo "============================================================"

# 源文件和目标路径
FILES=(
  "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/@layout.css:/usr/local/freecdn/edge-admin/web/views/@default/@layout.css"
  "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/@left_menu.css:/usr/local/freecdn/edge-admin/web/views/@default/@left_menu.css"
  "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/index/index.css:/usr/local/freecdn/edge-admin/web/views/@default/index/index.css"
  "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/dashboard/index.css:/usr/local/freecdn/edge-admin/web/views/@default/dashboard/index.css"
)

echo ""
echo "[Step 1] 检查源文件..."
for file in "${FILES[@]}"; do
  SRC="${file%:*}"
  if [ -f "$SRC" ]; then
    SIZE=$(stat -f%z "$SRC" 2>/dev/null || stat -c%s "$SRC" 2>/dev/null)
    echo "  [OK] $(basename $SRC) ($SIZE bytes)"
  else
    echo "  [FAIL] $(basename $SRC) 不存在"
    exit 1
  fi
done

echo ""
echo "[Step 2] 部署 CSS 文件到服务器..."
for file in "${FILES[@]}"; do
  SRC="${file%:*}"
  DEST="${file#*:}"
  cp "$SRC" "$DEST" 2>/dev/null
  if [ $? -eq 0 ]; then
    echo "  [OK] $(basename $SRC) -> $(basename $DEST)"
  else
    echo "  [FAIL] 无法部署 $(basename $SRC)"
    exit 1
  fi
done

echo ""
echo "[Step 3] 验证部署..."
for file in "${FILES[@]}"; do
  DEST="${file#*:}"
  if [ -f "$DEST" ]; then
    SIZE=$(stat -c%s "$DEST" 2>/dev/null)
    echo "  [OK] $(basename $DEST) 已验证 ($SIZE bytes)"
  else
    echo "  [FAIL] $(basename $DEST) 验证失败"
    exit 1
  fi
done

echo ""
echo "[Step 4] 当前服务进程状态..."
pgrep -l edge-admin || echo "  [INFO] edge-admin 未运行（正常，WSL 无 systemd）"

echo ""
echo "[提示] CSS 文件已部署"
echo "  - 地址：http://172.24.213.247:7788"
echo "  - 请清空浏览器缓存或使用无痕窗口刷新查看效果"
echo ""
echo "============================================================"
echo "部署完成！"
echo "============================================================"
