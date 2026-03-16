#!/bin/bash
# FreeCDN 品牌化替换 + 编译一体脚本
# 用法: bash deploy/brand-and-build.sh
# 在 WSL 中以 huhuhu 用户执行

set -e
export PATH=$PATH:/usr/local/go/bin:/home/huhuhu/go/bin

SRC=/home/huhuhu/freecdn/src
BIN=/home/huhuhu/freecdn/goedge

echo "============================================"
echo "  FreeCDN Brand Replace + Build"
echo "============================================"

# ─── 品牌字符串替换 ───────────────────────────

echo ""
echo ">>> [1/8] EdgeAdmin const.go"
sed -i \
    's|ProductName = "Edge Admin"|ProductName = "FreeCDN Admin"|g' \
    "$SRC/EdgeAdmin/internal/const/const.go"
sed -i \
    's|UpdatesURL.*= "https://goedge.cloud/api/boot/versions.*"|UpdatesURL = ""|g' \
    "$SRC/EdgeAdmin/internal/const/const.go"

echo ">>> [2/8] EdgeAPI const.go"
EAPI="$SRC/EdgeAPI/internal/const/const.go"
sed -i -e 's|ProductName   = "Edge API"|ProductName   = "FreeCDN API"|g' \
        -e 's|ProductNameZH = "Edge"|ProductNameZH = "FreeCDN"|g' \
        -e 's|GlobalProductName = "GoEdge"|GlobalProductName = "FreeCDN"|g' \
        "$EAPI"

echo ">>> [3/8] EdgeNode const.go"
ENODE=$(find "$SRC/EdgeNode/internal/const" -name "const.go" | head -1)
sed -i 's|ProductName = "Edge Node"|ProductName = "FreeCDN Node"|g' "$ENODE"

echo ">>> [4/8] EdgeCommon product_config.go"
sed -i 's|DefaultProductName = "GoEdge"|DefaultProductName = "FreeCDN"|g' \
    "$SRC/EdgeCommon/pkg/nodeconfigs/product_config.go"

echo ">>> [5/8] EdgeCommon messages_zh_cn.go"
sed -i \
    -e 's|"admin_ui@default_product_name":.*"GoEdge"|"admin_ui@default_product_name":                                       "FreeCDN"|' \
    -e 's|"admin_ui@default_system_name":.*"GoEdge管理员系统"|"admin_ui@default_system_name":                                        "FreeCDN 管理系统"|' \
    "$SRC/EdgeCommon/pkg/langs/messages/messages_zh_cn.go"

echo ">>> [6/8] EdgeAdmin @footer.html"
cat > "$SRC/EdgeAdmin/web/views/@default/@footer.html" << 'EOF'
<div id="footer" class="ui menu inverted light-blue borderless small" v-if="teaShowOpenSourceInfo">
    <a  href="/settings/upgrade" class="item" title="点击进入检查版本更新页面">{{teaName}} v{{teaVersion}}</a>
    <a href="https://github.com/your-org/freecdn" target="_blank" class="item">官网</a>
    <a href="https://github.com/your-org/freecdn/wiki" target="_blank" class="item">文档</a>
    <a href="https://github.com/your-org/freecdn" target="_blank" class="item">GitHub</a>
    <a href="https://github.com/your-org/freecdn/issues" target="_blank" class="item">提Bug</a>
</div>
EOF

echo ">>> [7/8] HTML 页面 goedge.cloud 链接替换"
VIEWS="$SRC/EdgeAdmin/web/views"
grep -rl "goedge\.cloud\|GoEdge" "$VIEWS" --include="*.html" 2>/dev/null | while read f; do
    sed -i \
        -e 's|https://goedge\.cloud/docs|https://github.com/your-org/freecdn/wiki|g' \
        -e 's|href="https://goedge\.cloud"|href="https://github.com/your-org/freecdn"|g' \
        -e 's|https://goedge\.cloud/commercial[^"]*|https://github.com/your-org/freecdn|g' \
        "$f"
done

echo ">>> [8/8] setup 页面文字替换"
SETUP="$SRC/EdgeAdmin/web/views/@default/setup/index.html"
sed -i \
    -e 's|感谢你选择使用<strong>GoEdge</strong>|感谢你选择使用<strong>FreeCDN</strong>|g' \
    -e 's|GoEdge软件开发者|FreeCDN开发团队|g' \
    -e 's|GoEdge开发者拥有本软件的所有著作权|FreeCDN基于GoEdge(BSD-3-Clause)二次开发，保留原作者版权|g' \
    -e 's|<title>安装GoEdge管理系统</title>|<title>安装 FreeCDN 管理系统</title>|g' \
    "$SETUP"
CONFIRM="$SRC/EdgeAdmin/web/views/@default/setup/confirm/index.html"
[ -f "$CONFIRM" ] && sed -i 's|<title>确认GoEdge管理系统</title>|<title>确认 FreeCDN 管理系统</title>|g' "$CONFIRM"

# ─── 编译 ─────────────────────────────────────

echo ""
echo "============================================"
echo "  Building..."
echo "============================================"

echo "[1/3] edge-admin..."
cd "$SRC/EdgeAdmin" && go build -tags community -o "$BIN/edge-admin/bin/edge-admin" ./cmd/edge-admin/main.go
echo "      ✓ $(ls -lh $BIN/edge-admin/bin/edge-admin | awk '{print $5}')"

echo "[2/3] edge-api..."
cd "$SRC/EdgeAPI" && go build -tags community -o "$BIN/edge-api/bin/edge-api" ./cmd/edge-api/main.go
echo "      ✓ $(ls -lh $BIN/edge-api/bin/edge-api | awk '{print $5}')"

echo "[3/3] edge-node..."
cd "$SRC/EdgeNode" && go build -tags community -o "$BIN/edge-node/bin/edge-node" ./cmd/edge-node/main.go
echo "      ✓ $(ls -lh $BIN/edge-node/bin/edge-node | awk '{print $5}')"

echo ""
echo "============================================"
echo "  Brand replace + build done!"
echo "  Next: restart services with deploy/start.sh"
echo "============================================"
