"""
验证 install.sh 安装后的登录
"""
import paramiko, time, sys, io, json

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30, show=True):
    _, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    if show:
        if out.strip(): print("[OUT]", out.strip()[:3000])
        if err.strip(): print("[ERR]", err.strip()[:500])
    return out, err

print("=== 服务状态 ===")
run("sudo systemctl is-active freecdn-api freecdn-admin", timeout=10)

print("\n=== 端口情况 ===")
run("ss -tlnp | grep -E '7788|8003'", timeout=10)

print("\n=== 登录测试 ===")
# 写临时脚本再执行，避免引号嵌套问题
login_script = """#!/bin/bash
curl -s -X POST http://127.0.0.1:7788/login/session \\
  -H 'Content-Type: application/json' \\
  -d '{"username":"admin","password":"REDACTED_SSH_PASS"}' 2>&1
"""
# 通过 SFTP 上传脚本
sftp = ssh.open_sftp()
with sftp.file('/tmp/test_login.sh', 'w') as f:
    f.write(login_script)
sftp.close()

run("chmod +x /tmp/test_login.sh && bash /tmp/test_login.sh", timeout=15)

print("\n=== 版本检查 ===")
run("sudo /usr/local/freecdn/edge-admin/bin/edge-admin -version 2>/dev/null || echo 'cannot get version'", timeout=10)
run("sudo /usr/local/freecdn/edge-admin/edge-api/bin/edge-api -version 2>/dev/null || echo 'cannot get version'", timeout=10)

print("\n=== 日志尾部（admin）===")
run("sudo journalctl -u freecdn-admin -n 10 --no-pager 2>/dev/null", timeout=15)

ssh.close()
print("\n=== Done ===")
