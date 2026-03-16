import paramiko
import sys
import io
import json
import hashlib
import re
import time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '134.175.67.168'
USER = 'ubuntu'
PASS = 'REDACTED_SSH_PASS'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=22, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30):
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8', errors='replace')
    err = e.read().decode('utf-8', errors='replace')
    return out, err

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "http://134.175.67.168:7788"

print("=== Current run.log tail ===")
out, _ = run("docker exec freecdn-admin tail -20 /app/edge-admin/logs/run.log 2>/dev/null")
print(out)

print("\n=== Current edge-api run.log tail ===")
out, _ = run("docker exec freecdn-admin tail -10 /app/edge-admin/edge-api/logs/run.log 2>/dev/null")
print(out)

# Check if 8003 is truly listening right now
print("\n=== Current 8003 state ===")
out, _ = run("docker exec freecdn-admin cat /proc/net/tcp6 2>/dev/null | awk '$4==\"0A\"{print $2, $4}'")
print(out)

# Attempt login from the server's external curl (not inside docker)
# This will have proper external Referer
print("\n=== Login attempt with correct Referer from server ===")

# First GET to get token and cookies
step1 = (
    f"curl -sf -c /tmp/ck4.txt "
    f"-A '{UA}' "
    f"'{BASE_URL}/' "
)
out, err = run(step1)
page_html = out

token_match = re.search(r'"token"\s*:\s*"([^"]+)"', page_html)
if token_match:
    page_token = token_match.group(1)
    print(f"Got page token: {page_token[:30]}...")
    
    pwd_md5 = hashlib.md5('REDACTED_SSH_PASS'.encode()).hexdigest()
    
    login_cmd = (
        f"curl -v -b /tmp/ck4.txt -c /tmp/ck4.txt "
        f"-A '{UA}' "
        f"-X POST '{BASE_URL}/' "
        f"-H 'Origin: {BASE_URL}' "
        f"-H 'Referer: {BASE_URL}/' "
        f"-H 'X-Requested-With: XMLHttpRequest' "
        f"-H 'Content-Type: application/x-www-form-urlencoded' "
        f"-d 'username=admin&password={pwd_md5}&token={page_token}' "
        f"2>&1 | grep -E 'HTTP|code|message|Set-Cookie|Location' | head -20"
    )
    out, err = run(login_cmd)
    print(f"Login response: {out}")
else:
    print("No token found in page!")

# Check if run.log has any new entries after our test
print("\n=== run.log AFTER login attempt ===")
out, _ = run("docker exec freecdn-admin tail -10 /app/edge-admin/logs/run.log 2>/dev/null")
print(out)

print("\n=== edge-api run.log AFTER login attempt ===")
out, _ = run("docker exec freecdn-admin tail -5 /app/edge-admin/edge-api/logs/run.log 2>/dev/null")
print(out)

c.close()
print("Done.")
