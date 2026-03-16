"""
上传 bash 登录脚本到服务器，执行登录测试
"""
import paramiko
import time

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

sftp = ssh.open_sftp()

# 写 bash 登录测试脚本
bash_script = r"""#!/bin/bash
COOKIEFILE=/tmp/login_test_cookies.txt
UA="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
BASE="http://127.0.0.1:7788"
PASS_MD5=$(echo -n 'REDACTED_SSH_PASS' | md5sum | cut -d' ' -f1)
echo "MD5: $PASS_MD5"

# 清理旧 cookie
rm -f $COOKIEFILE

# Step 1: GET / 保存 cookie
HTML=$(curl -s -c $COOKIEFILE -b $COOKIEFILE -A "$UA" "$BASE/")
echo "HTML length: ${#HTML}"

# 从 JS 中提取 token（在 "token":"xxxxx" 里）
TOKEN=$(echo "$HTML" | grep -oP '"token":"\K[a-f0-9]+' | head -1)
echo "Token: $TOKEN"
echo "Cookie file contents:"
cat $COOKIEFILE

# Step 2: POST / with same cookie file
echo ""
echo "=== POST login ==="
RESP=$(curl -si -b $COOKIEFILE -c $COOKIEFILE -A "$UA" \
    -X POST "$BASE/" \
    --data-urlencode "token=$TOKEN" \
    --data-urlencode "username=admin" \
    --data-urlencode "password=$PASS_MD5" \
    --data-urlencode "remember=1" 2>&1)
echo "$RESP" | head -20

# Step 3: Check dashboard
echo ""
echo "=== Check dashboard ==="
DASH=$(curl -s -o /dev/null -w '%{http_code}' -b $COOKIEFILE -A "$UA" "$BASE/dashboard")
echo "Dashboard status: $DASH"

# Step 4: Test a few protected pages
echo ""
echo "=== Protected pages ==="
for PATH in "/clusters/cluster?clusterId=1" "/servers/server/settings?serverId=1" "/users/user?userId=1"; do
    CODE=$(curl -s -o /dev/null -w '%{http_code}' -b $COOKIEFILE -A "$UA" "$BASE$PATH")
    echo "[$CODE] $PATH"
done
"""

with sftp.file('/tmp/login_test.sh', 'w') as f:
    f.write(bash_script)
sftp.chmod('/tmp/login_test.sh', 0o755)
sftp.close()

print("脚本已上传，执行中...")

# 执行
def run(cmd, timeout=30):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()

result = run("bash /tmp/login_test.sh", timeout=30)
print(result)

ssh.close()
