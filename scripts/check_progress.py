import paramiko, sys

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS,
               timeout=15, look_for_keys=False, allow_agent=False)

def run(cmd):
    _, out, _ = client.exec_command(cmd, timeout=30, get_pty=False)
    result = out.read().decode('utf-8', errors='replace')
    print(result)

print("=== Running processes ===")
run("ps aux | grep -E 'install|wget|curl|bash|edge' | grep -v grep")

print("=== /usr/local/freecdn contents ===")
run("ls -lh /usr/local/freecdn/ 2>/dev/null || echo 'dir not found'")

print("=== systemctl edge-admin ===")
run("sudo systemctl status edge-admin --no-pager 2>&1 | head -20")

print("=== /tmp files ===")
run("ls -lh /tmp/freecdn* 2>/dev/null || echo 'no freecdn files in /tmp'")

print("=== port check ===")
run("ss -tlnp 2>/dev/null | grep -E '7788|8003|80 ' || echo 'no matching ports'")

client.close()
