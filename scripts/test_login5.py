import paramiko
import sys
import io
import json
import hashlib
import re
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

UA_BROWSER = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "http://134.175.67.168:7788"

print("=== Test GET with verbose ===")
out, _ = run(
    f"curl -v -A '{UA_BROWSER}' '{BASE_URL}/' 2>&1 | grep -E 'HTTP|< |> ' | head -20"
)
print(out)

print("\n=== Test POST with verbose (see exact 403 reason) ===")
out, _ = run(
    f"curl -v -A '{UA_BROWSER}' -X POST '{BASE_URL}/' "
    f"-H 'Origin: {BASE_URL}' "
    f"-H 'Referer: {BASE_URL}/' "
    f"-d 'username=admin&password=test&token=test' "
    f"2>&1 | grep -E 'HTTP|< |> |forbidden|Deny' | head -25"
)
print(out)

print("\n=== Check DenySpiders config in edge-admin ===")
# Look for DenySpiders config
out, _ = run("docker exec freecdn-admin find /app/edge-admin -name '*.yaml' -o -name '*.conf' 2>/dev/null | xargs grep -l 'DenySpider\\|denySpider\\|spider' 2>/dev/null | head -5")
print("Config with DenySpiders:", out)

out2, _ = run("docker exec freecdn-admin find /app/edge-admin/configs -type f 2>/dev/null")
print("All configs:", out2)

out3, _ = run("docker exec freecdn-admin cat /app/edge-admin/configs/server.yaml 2>/dev/null")
print("server.yaml:", out3)

# Check if there's a specific port for internal/admin access
print("\n=== Check server.yaml and api_admin.yaml ===")
out, _ = run("docker exec freecdn-admin cat /app/edge-admin/configs/api_admin.yaml 2>/dev/null")
print("api_admin.yaml:", out)

# The 403 might be DenySpiders from GoEdge itself on the HTTP server
# Check if there's a way to disable it
print("\n=== Check GoEdge HTTP server config ===")
out, _ = run("docker exec freecdn-admin ls /app/edge-admin/configs/ 2>/dev/null")
print("configs dir:", out)

out2, _ = run("docker exec freecdn-admin ls /app/edge-admin/ 2>/dev/null")
print("edge-admin dir:", out2)

# Check if there's a static file or web config
out3, _ = run("docker exec freecdn-admin find /app/edge-admin -maxdepth 2 -type d 2>/dev/null | head -20")
print("Dirs:", out3)

# Since DenySpiders uses Go's net/http package and checks headers,
# let's try with Accept header too
print("\n=== Login attempt with full browser headers ===")

# GET first
out_get, _ = run(
    f"curl -sf -c /tmp/ck5.txt "
    f"-A '{UA_BROWSER}' "
    f"-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' "
    f"-H 'Accept-Language: zh-CN,zh;q=0.9' "
    f"-H 'Connection: keep-alive' "
    f"'{BASE_URL}/'"
)

token_m = re.search(r'"token"\s*:\s*"([^"]+)"', out_get)
if token_m:
    tok = token_m.group(1)
    print(f"Page token: {tok[:30]}...")
    pwd_md5 = hashlib.md5('REDACTED_SSH_PASS'.encode()).hexdigest()
    
    out_post, _ = run(
        f"curl -v -b /tmp/ck5.txt -c /tmp/ck5.txt "
        f"-A '{UA_BROWSER}' "
        f"-X POST '{BASE_URL}/' "
        f"-H 'Accept: application/json, text/plain, */*' "
        f"-H 'Accept-Language: zh-CN,zh;q=0.9' "
        f"-H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' "
        f"-H 'Origin: {BASE_URL}' "
        f"-H 'Referer: {BASE_URL}/' "
        f"-H 'X-Requested-With: XMLHttpRequest' "
        f"-H 'Connection: keep-alive' "
        f"-d 'username=admin&password={pwd_md5}&token={tok}' "
        f"2>&1 | grep -E '< HTTP|code|message|< Set-Cookie|< Location' | head -15"
    )
    print(f"POST response: {out_post}")
else:
    print("No token found")

c.close()
print("Done.")
