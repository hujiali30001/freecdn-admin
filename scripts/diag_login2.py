"""
调查登录 403 的真正原因，并尝试登录
"""
import paramiko
import re

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"
BASE = "http://127.0.0.1:7788"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=20):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()

# 1. 带 User-Agent 的 GET /
print("=== 1. 带 User-Agent 的 GET / ===")
r = run('curl -si -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0" http://127.0.0.1:7788/ 2>&1 | head -40')
print(r)

# 2. 检查服务器端日志（最近几行）
print("\n=== 2. 服务日志（最近20行）===")
r = run("sudo journalctl -u freecdn-admin --no-pager -n 20 2>&1 | tail -20")
print(r)

# 3. 检查源码里的 403 触发逻辑
print("\n=== 3. 检查 parent_action.go 中 403 条件 ===")
r = run("grep -n '403\\|Forbidden\\|AllowedIP\\|allowedIP\\|clientIP\\|denyIP\\|IsAllowed' /usr/local/freecdn/edge-admin/internal/web/actions/actionutils/parent_action.go 2>/dev/null | head -30")
print(r)

# 4. 找 parent_action.go 实际路径
r2 = run("find /usr/local/freecdn -name 'parent_action.go' 2>/dev/null")
print(f"parent_action.go: {r2}")

# 5. 检查 user_must_auth.go
r3 = run("find /usr/local/freecdn -name 'user_must_auth.go' 2>/dev/null")
print(f"user_must_auth.go: {r3}")
if r3:
    r4 = run(f"cat {r3} 2>/dev/null | head -80")
    print(r4)

ssh.close()
