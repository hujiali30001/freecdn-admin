import paramiko, time, sys, io

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"

LOG_FILE = r"c:\Users\Administrator\.workbuddy\FreeCDN\dist\build\reinstall.log"
log_fh = open(LOG_FILE, "w", encoding="utf-8")

# Windows cmd 是 GBK，用 buffer 写 UTF-8 字节避免 UnicodeEncodeError
stdout_buf = sys.stdout.buffer if hasattr(sys.stdout, 'buffer') else None

def log(msg):
    if stdout_buf:
        stdout_buf.write(msg.encode('utf-8', errors='replace'))
        stdout_buf.flush()
    log_fh.write(msg)
    log_fh.flush()

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS,
               timeout=15, look_for_keys=False, allow_agent=False)
log("Connected!\n\n")

def run(cmd, timeout=600):
    log(f"$ {cmd}\n")
    chan = client.get_transport().open_session()
    chan.set_combine_stderr(True)
    chan.get_pty(width=220, height=50)
    chan.exec_command(cmd)
    deadline = time.time() + timeout
    while not chan.exit_status_ready():
        if chan.recv_ready():
            chunk = chan.recv(4096).decode('utf-8', errors='replace')
            log(chunk)
        if time.time() > deadline:
            log("\n[TIMEOUT]\n")
            chan.close()
            return -1, ""
        time.sleep(0.1)
    # drain remaining
    while chan.recv_ready():
        chunk = chan.recv(4096).decode('utf-8', errors='replace')
        log(chunk)
    code = chan.recv_exit_status()
    log(f"\n[exit: {code}]\n\n")
    chan.close()
    return code, ""

# ── Step 1: 停止旧服务 ─────────────────────────────────────────
log("=== Step 1: 停止旧服务 ===\n")
run("sudo systemctl stop freecdn-admin 2>/dev/null || true; sleep 1")
run("sudo pkill -9 -f 'edge-admin|edge-api' 2>/dev/null || true; sleep 1")
run("pgrep -fa 'edge-admin|edge-api' || echo 'all stopped'")

# ── Step 2: 确认包文件在服务器上 ────────────────────────────────
log("=== Step 2: 确认本地缓存包 ===\n")
run("ls -lh /tmp/freecdn-pkg.tar.gz 2>/dev/null || echo 'no local cache'")

# ── Step 3: 预放包文件 + 安装 fake-wget ─────────────────────────
log("=== Step 3: 预放包文件到 install.sh 期望的路径 ===\n")
# install.sh 里 DOWNLOAD_FILE=/tmp/freecdn-pkg，最终写成 /tmp/freecdn-pkg.tar.gz
# 提前把缓存包复制过去，同时装 fake-wget 作双重保险
run("sudo cp /tmp/freecdn-pkg.tar.gz /tmp/freecdn-pkg.tar.gz.bak 2>/dev/null || true")

# fake-wget：只要有 -O 参数，就用本地包（优先备份路径，防止主路径被覆盖）
fake_wget = r"""sudo bash -c 'cat > /usr/local/bin/wget << '"'"'FWEOF'"'"'
#!/bin/bash
OUTFILE=""
PREV=""
for a in "$@"; do
  if [ "$PREV" = "-O" ]; then OUTFILE="$a"; fi
  PREV="$a"
done
if [ -n "$OUTFILE" ]; then
  SRC=""
  [ -f /tmp/freecdn-pkg-backup.tar.gz ] && SRC=/tmp/freecdn-pkg-backup.tar.gz
  [ -z "$SRC" ] && [ -f /tmp/freecdn-pkg.tar.gz ] && SRC=/tmp/freecdn-pkg.tar.gz
  if [ -n "$SRC" ]; then
    echo "[fake-wget] Using cached package $SRC -> $OUTFILE" >&2
    cp "$SRC" "$OUTFILE"
    exit 0
  fi
fi
exec /usr/bin/wget "$@"
FWEOF
chmod +x /usr/local/bin/wget
echo fake_wget_ready'"""
run(fake_wget)

# 把包备份到另一个路径，防止 ghfast.top 损坏的下载覆盖主路径
# 注意：不用 chattr +i，因为 install.sh 里 rm -f 会失败导致脚本退出
log("=== 备份本地包（防止镜像覆盖，不锁定，install.sh 可正常操作）===\n")
run("sudo cp -f /tmp/freecdn-pkg.tar.gz /tmp/freecdn-pkg-backup.tar.gz && echo 'backup ok'")

# ── Step 4: 拉最新 install.sh（镜像站）并执行 --reinstall ───────
log("=== Step 4: 拉最新 install.sh 并执行 --reinstall ===\n")
# 优先从镜像站拉脚本，失败才直连；下载后用 tr 去掉 CR（镜像站可能返回 CRLF）
install_cmd = (
    "{ curl -fsSL --max-time 15 "
    "https://ghfast.top/https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh "
    "|| curl -fsSL --max-time 30 "
    "https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh; } "
    "| tr -d '\\r' > /tmp/freecdn_install.sh && "
    "echo 'script downloaded' && "
    "sudo PATH=/usr/local/bin:$PATH bash /tmp/freecdn_install.sh --reinstall"
)
run(install_cmd, timeout=600)



# ── Step 5: 清理 fake-wget ─────────────────────────────────────
run("sudo chattr -i /tmp/freecdn-pkg.tar.gz 2>/dev/null || true")  # 以防万一解锁
run("sudo rm -f /usr/local/bin/wget /tmp/freecdn_install.sh /tmp/freecdn-pkg-backup.tar.gz && echo 'cleanup done'")

# ── Step 6: 验证结果 ────────────────────────────────────────────
log("=== Step 6: 验证安装结果 ===\n")
run("sudo systemctl status freecdn-admin --no-pager -l | head -25")
run("ss -tlnp 2>/dev/null | grep -E '7788|8003' || echo 'ports not listening'")
run("ps aux | grep -E 'edge-admin|edge-api' | grep -v grep")
run("sudo journalctl -u freecdn-admin -n 40 --no-pager 2>/dev/null")

client.close()
log("\n=== Done ===\n")
log_fh.close()
print("Log: " + LOG_FILE)
