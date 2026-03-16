import paramiko, sys, time, io

sys.stdout = io.TextIOWrapper(open(
    r"c:\Users\Administrator\.workbuddy\FreeCDN\dist\build\install_run2.log",
    "w", encoding="utf-8"), errors='replace')
sys.stderr = sys.stdout

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS,
               timeout=15, look_for_keys=False, allow_agent=False)

def run(cmd, timeout=600):
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

print("=== Setup fake wget ===", flush=True)
run("""sudo bash -c '
mkdir -p /usr/local/bin
cat > /usr/local/bin/wget << "EOFWGET"
#!/bin/bash
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
echo done
'""")

print("\n=== Run install.sh ===", flush=True)
code, _ = run(
    "curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo PATH=/usr/local/bin:$PATH bash",
    timeout=600
)

run("sudo rm -f /usr/local/bin/wget; echo 'fake wget removed'")

print(f"\n{'SUCCESS' if code == 0 else 'FAILED'} (exit {code})", flush=True)

print("\n=== Verify ===", flush=True)
run("sudo systemctl status edge-admin --no-pager -l 2>&1 | head -30")
run("sudo ss -tlnp 2>/dev/null | grep -E '7788|8003' || echo 'no ports'")
run("ls -lh /usr/local/freecdn/")
run("cat /usr/local/freecdn/VERSION 2>/dev/null")

client.close()
print("\n=== Done ===", flush=True)
