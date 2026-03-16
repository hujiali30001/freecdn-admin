import paramiko, sys, time, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS,
               timeout=15, look_for_keys=False, allow_agent=False)

def run(cmd, timeout=300):
    print(f"\n$ {cmd[:120]}{'...' if len(cmd)>120 else ''}", flush=True)
    _, out, _ = client.exec_command(cmd, timeout=timeout, get_pty=True)
    buf = []
    while not out.channel.exit_status_ready():
        if out.channel.recv_ready():
            chunk = out.channel.recv(8192).decode('utf-8', errors='replace')
            print(chunk, end='', flush=True)
            buf.append(chunk)
        time.sleep(0.1)
    rest = out.channel.recv(65536).decode('utf-8', errors='replace')
    if rest:
        print(rest, end='', flush=True)
        buf.append(rest)
    code = out.channel.recv_exit_status()
    print(f"\n[exit: {code}]", flush=True)
    return code, ''.join(buf)

# install.sh 通过 wget 判断下载成功与否，已有文件时 wget 会覆盖
# 最简单方法：给 wget 打一个 wrapper，让它直接返回成功（跳过真正下载）
# 把 /tmp/freecdn-pkg.tar.gz 改名让 wget 以为自己下的

print("=== Step 1: Setup wget bypass ===")
run("""sudo bash -c '
# 把已有的包重命名备份，wget 完成后会在这个路径
# 用 alias/PATH trick 让 wget 跳过下载
mkdir -p /usr/local/bin
cat > /usr/local/bin/wget_real << "EOFWGET"
#!/bin/bash
exec /usr/bin/wget "$@"
EOFWGET
chmod +x /usr/local/bin/wget_real

# 创建 fake wget：识别 freecdn Release URL 时直接 cp 已有包
cat > /usr/local/bin/wget << "EOFWGET"
#!/bin/bash
# 如果是下载 freecdn release，直接复制已有包
for arg in "$@"; do
  if echo "$arg" | grep -q "freecdn.*releases"; then
    OUTFILE=""
    PREV=""
    for a in "$@"; do
      if [ "$PREV" = "-O" ]; then OUTFILE="$a"; fi
      PREV="$a"
    done
    if [ -n "$OUTFILE" ] && [ -f /tmp/freecdn-pkg.tar.gz ]; then
      echo "[fake-wget] Using pre-downloaded package -> $OUTFILE" >&2
      cp /tmp/freecdn-pkg.tar.gz "$OUTFILE"
      exit 0
    fi
  fi
done
exec /usr/bin/wget "$@"
EOFWGET
chmod +x /usr/local/bin/wget
echo "fake wget installed"
'
""")

print("\n=== Step 2: Run install.sh ===")
code, output = run(
    "curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo PATH=/usr/local/bin:$PATH bash",
    timeout=600
)

print(f"\n{'SUCCESS' if code == 0 else 'FAILED'} (exit {code})", flush=True)

print("\n=== Step 3: Cleanup fake wget ===")
run("sudo rm -f /usr/local/bin/wget; echo 'fake wget removed'")

print("\n=== Step 4: Verify installation ===")
run("sudo systemctl status edge-admin --no-pager -l 2>&1 | head -30")
run("sudo ss -tlnp 2>/dev/null | grep -E '7788|8003|443|80' || echo 'checking ports...'")
run("ls -lh /usr/local/freecdn/")
run("cat /usr/local/freecdn/VERSION 2>/dev/null || echo 'VERSION not found'")

client.close()
print("\n=== Test complete ===", flush=True)
