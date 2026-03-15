#!/usr/bin/env python3
"""通过 SSH 在服务器上运行 FreeCDN 安装脚本，实时输出日志

用法:
  python ssh_install.py <host> <user> [--pass <password>]
  或通过环境变量: SSH_HOST, SSH_USER, SSH_PASS
"""

import subprocess, sys, time, os, argparse

parser = argparse.ArgumentParser()
parser.add_argument("host", nargs="?", default=os.environ.get("SSH_HOST", ""))
parser.add_argument("user", nargs="?", default=os.environ.get("SSH_USER", "root"))
parser.add_argument("--pass", dest="password", default=os.environ.get("SSH_PASS", ""))
args = parser.parse_args()

HOST = args.host
USER = args.user
PASS = args.password

if not HOST:
    print("ERROR: 请指定主机地址，例如: python ssh_install.py 1.2.3.4 ubuntu --pass yourpassword")
    sys.exit(1)

INSTALL_CMD = (
    "echo '=== 开始安装 ===' && "
    "curl -fsSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh -o /tmp/freecdn_install.sh && "
    "echo '=== 脚本下载完成 ===' && "
    "sudo bash /tmp/freecdn_install.sh 2>&1"
)

def run():
    # 先试 sshpass
    r = subprocess.run(["where", "sshpass"], capture_output=True, text=True)
    if r.returncode == 0:
        cmd = ["sshpass", "-p", PASS, "ssh",
               "-o", "StrictHostKeyChecking=no",
               "-o", "ConnectTimeout=15",
               f"{USER}@{HOST}", INSTALL_CMD]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, text=True,
                                encoding="utf-8", errors="replace")
        for line in proc.stdout:
            print(line, end="", flush=True)
        proc.wait()
        return proc.returncode

    # 用 paramiko
    try:
        import paramiko
    except ImportError:
        print("ERROR: paramiko not found", file=sys.stderr)
        return 1

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to {HOST}...")
    client.connect(HOST, username=USER, password=PASS,
                   timeout=15, allow_agent=False, look_for_keys=False)
    print("Connected. Starting installation...\n")

    transport = client.get_transport()
    transport.set_keepalive(30)

    chan = transport.open_session()
    chan.get_pty(width=220, height=50)
    chan.exec_command(INSTALL_CMD)

    out = open("C:/Temp/freecdn_install.log", "w", encoding="utf-8")

    def emit(data):
        # 同时写日志文件（UTF-8）和控制台（安全输出）
        out.write(data)
        out.flush()
        safe = data.encode("gbk", errors="replace").decode("gbk", errors="replace")
        print(safe, end="", flush=True)

    while True:
        if chan.recv_ready():
            emit(chan.recv(4096).decode("utf-8", errors="replace"))
        if chan.recv_stderr_ready():
            emit(chan.recv_stderr(4096).decode("utf-8", errors="replace"))
        if chan.exit_status_ready():
            while chan.recv_ready():
                emit(chan.recv(4096).decode("utf-8", errors="replace"))
            break
        time.sleep(0.1)

    out.close()

    rc = chan.recv_exit_status()
    client.close()
    print(f"\n=== 安装完成，exit code: {rc} ===")
    return rc

if __name__ == "__main__":
    sys.exit(run())
