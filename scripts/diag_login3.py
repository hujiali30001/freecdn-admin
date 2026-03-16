"""
调试 GoEdge 登录机制：
- 分析 CSRF token 格式和验证逻辑
- 尝试在服务器上用 curl 直接登录
"""
import paramiko
import re

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"
BASE = "http://127.0.0.1:7788"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=30):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()

# 1. 查看 index.js 中的登录逻辑
print("=== 1. 查看 index.js 登录提交逻辑 ===")
r = run("grep -n 'submitBefore\\|token\\|password\\|md5\\|submitSuccess' /usr/local/freecdn/edge-admin/web/views/@default/index/index.js 2>/dev/null | head -40")
print(r)

# 2. 查看 vue.tea.js 中的 csrf-token 组件
print("\n=== 2. csrf-token 组件定义 ===")
r = run("grep -n 'csrf-token\\|csrfToken\\|csrf\\|CSRF' /usr/local/freecdn/edge-admin/web/public/js/vue.tea.js 2>/dev/null | head -30")
print(r)

# 3. 查看服务端 CSRF 验证逻辑（Go 源码）
print("\n=== 3. 服务端 CSRF token 验证 ===")
r = run("find /usr/local/freecdn -name '*.go' 2>/dev/null | xargs grep -l 'tokenKey\\|TokenKey\\|csrf\\|CSRF' 2>/dev/null | head -10")
print("相关 Go 文件:", r)

r = run("find /usr/local/freecdn -name 'index.go' 2>/dev/null | head -5")
print("index.go 路径:", r)

# 4. 尝试用 bash 一行搞定登录（GET 和 POST 用同一个 shell 进程，避免 cookie 问题）
print("\n=== 4. 尝试 bash 一体化登录脚本 ===")
login_script = """
set -e
COOKIEFILE=/tmp/login_test_cookies.txt
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
BASE="http://127.0.0.1:7788"
PASS_MD5=$(echo -n 'REDACTED_SSH_PASS' | md5sum | cut -d' ' -f1)
echo "MD5: $PASS_MD5"

# Step 1: GET / with cookie save
HTML=$(curl -s -c $COOKIEFILE -b $COOKIEFILE -A "$UA" "$BASE/")
STATUS=$(curl -s -o /dev/null -w '%{http_code}' -b $COOKIEFILE -A "$UA" "$BASE/")

# 从 JS 中提取 token
TOKEN=$(echo "$HTML" | grep -oP '"token":"\\K[a-f0-9]+' | head -1)
echo "Token: $TOKEN"
echo "GET status: $STATUS"
echo "Cookie file:"
cat $COOKIEFILE

# Step 2: POST / with same cookie
echo ""
echo "=== POST login ==="
RESP=$(curl -si -b $COOKIEFILE -c $COOKIEFILE -A "$UA" \\
    -X POST "$BASE/" \\
    -d "token=$TOKEN&username=admin&password=$PASS_MD5&remember=1" 2>&1)
echo "$RESP" | head -20

# Step 3: Check dashboard
echo ""
echo "=== Check dashboard ==="
DASH=$(curl -s -o /dev/null -w '%{http_code}' -b $COOKIEFILE -A "$UA" "$BASE/dashboard")
echo "Dashboard status: $DASH"
"""
r = run(f"bash -c {repr(login_script)}", timeout=30)
print(r)

ssh.close()
