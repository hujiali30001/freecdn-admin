#!/usr/bin/env python3
"""
验证 v0.1.7 install.sh 在服务器上能正确下载并安装
"""
import paramiko, time, sys

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"

def ssh_run(client, cmd, timeout=300):
    print(f"\n$ {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    rc  = stdout.channel.recv_exit_status()
    if out: print(out)
    if err: print("[STDERR]", err)
    return rc, out, err

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=15)
print(f"Connected to {HOST}")

steps = []

# 1. 检查 install.sh 下载的版本号
rc, out, _ = ssh_run(client, "curl -sSL https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh 2>/dev/null | grep FREECDN_VERSION | head -5")
steps.append(("install.sh 版本号", "v0.1.7" in out, out.strip()))

# 2. 下载 v0.1.7 包并检查是否可下载
rc, out, _ = ssh_run(client,
    "curl -fsSL -o /tmp/freecdn-v0.1.7-test.tar.gz "
    "https://ghfast.top/https://github.com/hujiali30001/freecdn-admin/releases/download/v0.1.7/freecdn-v0.1.7-linux-amd64.tar.gz "
    "&& ls -lh /tmp/freecdn-v0.1.7-test.tar.gz",
    timeout=120
)
steps.append(("v0.1.7 tar.gz 可下载", rc == 0 and ".tar.gz" in out, out.strip()))

# 3. 解压并验证二进制存在
rc, out, _ = ssh_run(client,
    "tar xzf /tmp/freecdn-v0.1.7-test.tar.gz -C /tmp/ && "
    "ls /tmp/freecdn-v0.1.7-linux-amd64/ && "
    "file /tmp/freecdn-v0.1.7-linux-amd64/edge-admin"
)
steps.append(("解压验证 edge-admin", rc == 0 and "ELF" in out, out.strip()))

# 4. 检查 VERSION 文件
rc, out, _ = ssh_run(client, "cat /tmp/freecdn-v0.1.7-linux-amd64/VERSION")
steps.append(("VERSION 文件", "v0.1.7" in out, out.strip()))

# 5. 检查当前服务状态（安装还在跑的那个）
rc, out, _ = ssh_run(client, "systemctl is-active freecdn-admin freecdn-api 2>/dev/null || true")
steps.append(("服务状态", "active" in out, out.strip()))

# 清理
ssh_run(client, "rm -rf /tmp/freecdn-v0.1.7-test.tar.gz /tmp/freecdn-v0.1.7-linux-amd64")

client.close()

print("\n" + "="*60)
print("验证结果")
print("="*60)
all_ok = True
for name, ok, detail in steps:
    status = "✓" if ok else "✗"
    print(f"  [{status}] {name}")
    if detail:
        for line in detail.splitlines():
            print(f"       {line}")
    if not ok:
        all_ok = False

print("\n" + ("全部通过 ✓" if all_ok else "有失败项 ✗"))
sys.exit(0 if all_ok else 1)
