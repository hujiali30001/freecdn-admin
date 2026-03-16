"""
在腾讯云服务器上实际运行 install.sh，捕获完整输出。
服务器: 134.175.67.168 ubuntu / FreeCDN2026!
"""
import paramiko, time, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30, show=True):
    _, stdout, stderr = ssh.exec_command(f"sudo bash -c {repr(cmd)}", timeout=timeout)
    out = stdout.read().decode(errors='replace')
    err = stderr.read().decode(errors='replace')
    if show:
        if out.strip(): print("[OUT]", out.strip()[:3000])
        if err.strip(): print("[ERR]", err.strip()[:500])
    return out, err

print("=== 环境信息 ===")
run("uname -a && cat /etc/os-release | head -5", timeout=10)
run("which mysql && mysql --version 2>/dev/null || echo 'mysql: NOT installed'", timeout=10)
run("systemctl is-active mysql 2>/dev/null || echo 'mysql service: not running'", timeout=10)
run("ls /usr/local/freecdn 2>/dev/null || echo '/usr/local/freecdn: not exists'", timeout=10)
run("systemctl list-units --state=active | grep freecdn || echo 'no freecdn services'", timeout=10)

print("\n=== 清理旧安装 ===")
run(
    "systemctl stop freecdn-api freecdn-admin 2>/dev/null; "
    "systemctl disable freecdn-api freecdn-admin 2>/dev/null; "
    "rm -f /etc/systemd/system/freecdn-*.service; "
    "rm -rf /usr/local/freecdn /var/lib/freecdn /var/log/freecdn; "
    "rm -f /tmp/freecdn-pkg* ; "
    "rm -rf /tmp/freecdn-admin-src; "
    "systemctl daemon-reload; "
    "echo CLEAN_DONE",
    timeout=30
)

print("\n=== 运行 install.sh（最多等 5 分钟）===")
# 先下载脚本到服务器再执行，避免 pipe 模式的限制
dl_cmd = (
    "curl -sSfL 'https://ghfast.top/https://raw.githubusercontent.com/"
    "hujiali30001/freecdn-admin/main/install.sh' -o /tmp/freecdn_install.sh && "
    "echo DOWNLOAD_OK || echo DOWNLOAD_FAIL"
)
run(dl_cmd, timeout=30)
run("wc -l /tmp/freecdn_install.sh 2>/dev/null || echo 'script not downloaded'", timeout=10)

# 直接执行下载下来的脚本
_, stdout_chan, _ = ssh.exec_command(
    "sudo bash /tmp/freecdn_install.sh --reinstall 2>&1",
    timeout=320
)
stdout_chan.channel.settimeout(320)

buf = []
start = time.time()
try:
    while True:
        line = stdout_chan.readline()
        if not line:
            break
        line_stripped = line.rstrip()
        buf.append(line_stripped)
        print(line_stripped)
        if time.time() - start > 290:
            print("[TIMEOUT] 290 秒，停止")
            break
except Exception as e:
    print(f"[READ ERROR] {e}")

print("\n=== 安装后状态 ===")
run("systemctl is-active freecdn-api freecdn-admin 2>&1 || true", timeout=10)
run("ls /usr/local/freecdn/edge-admin/bin/ 2>/dev/null || echo NOT_FOUND", timeout=10)
run("ls /usr/local/freecdn/edge-admin/edge-api/bin/ 2>/dev/null || echo NOT_FOUND", timeout=10)
run("curl -s -o /dev/null -w 'HTTP:%{http_code}' http://127.0.0.1:7788/ 2>&1 || echo NO_RESPONSE", timeout=15)
run("journalctl -u freecdn-api -n 15 --no-pager 2>/dev/null || echo 'no journal'", timeout=15)
run("journalctl -u freecdn-admin -n 15 --no-pager 2>/dev/null || echo 'no journal'", timeout=15)

ssh.close()
print("\n=== Done ===")
