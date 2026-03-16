"""
升级服务器到 v0.4.1（最简化版）
"""
import paramiko, time

def run_cmd(ssh, cmd, timeout=60):
    print(f"$ {cmd[:100]}")
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    rc = out.channel.recv_exit_status()
    o = out.read().decode().strip()
    e = err.read().decode().strip()
    if o: print("  OUT:", o[:400])
    if e: print("  ERR:", e[:200])
    return rc

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("134.175.67.168", username="ubuntu", password="REDACTED_SSH_PASS", timeout=15)

# 下载（大文件，超时 3 分钟）
print("=== 下载 v0.4.1 ===")
rc = run_cmd(ssh,
    "curl -sL --retry 3 "
    "-o /tmp/freecdn-v041.tar.gz "
    "https://github.com/hujiali30001/freecdn-admin/releases/download/v0.4.1/freecdn-v0.4.1-linux-amd64.tar.gz "
    "&& echo DONE || echo FAIL",
    timeout=200)
print("RC:", rc)

# 解压
rc = run_cmd(ssh, "cd /tmp && tar xzf freecdn-v041.tar.gz && ls freecdn-v0.4.1-linux-amd64/bin/")

# 停服务
run_cmd(ssh, "sudo systemctl stop freecdn-admin freecdn-api || true", timeout=30)

# 替换二进制
run_cmd(ssh, "cp /tmp/freecdn-v0.4.1-linux-amd64/bin/edge-admin /usr/local/freecdn/edge-admin/bin/edge-admin")
run_cmd(ssh, "cp /tmp/freecdn-v0.4.1-linux-amd64/bin/edge-api /usr/local/freecdn/edge-admin/edge-api/bin/edge-api")

# 重启
run_cmd(ssh, "sudo systemctl start freecdn-api", timeout=30)
time.sleep(6)
run_cmd(ssh, "sudo systemctl start freecdn-admin", timeout=30)
time.sleep(4)

# 检查
run_cmd(ssh, "sudo systemctl is-active freecdn-admin freecdn-api")
run_cmd(ssh, "sudo journalctl -u freecdn-api -n 5 --no-pager 2>&1 | tail -8")

ssh.close()
print("=== 完成 ===")
