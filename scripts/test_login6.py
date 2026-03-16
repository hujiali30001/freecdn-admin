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

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BASE_URL = "http://134.175.67.168:7788"
COOKIE_FILE = "/tmp/ck6.txt"

print("=" * 60)
print("COMPLETE LOGIN FLOW - CSRF + page token")
print("=" * 60)

# Step 1: GET / to get session cookie + page token
print("\n[Step 1] GET / (establish session)")
out1, _ = run(
    f"curl -sf -c {COOKIE_FILE} "
    f"-A '{UA}' "
    f"-H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8' "
    f"-H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' "
    f"'{BASE_URL}/'"
)
# Extract page token (the anti-replay token embedded in window.TEA)
token_m = re.search(r'"token"\s*:\s*"([^"]+)"', out1)
page_token = token_m.group(1) if token_m else None
session_id_m = re.search(r'geadsid=([^\s;]+)', out1)

print(f"  Page token: {page_token}")
out_ck, _ = run(f"cat {COOKIE_FILE} 2>/dev/null | grep -v '^#' | grep -v '^$'")
print(f"  Cookies: {out_ck.strip()}")

# Step 2: Get CSRF token (as a logged-in JS would do)
print("\n[Step 2] GET /csrf/token (AJAX request)")
out2, _ = run(
    f"curl -sf -b {COOKIE_FILE} -c {COOKIE_FILE} "
    f"-A '{UA}' "
    f"-H 'Accept: application/json, text/plain, */*' "
    f"-H 'Referer: {BASE_URL}/' "
    f"-H 'X-Requested-With: XMLHttpRequest' "
    f"'{BASE_URL}/csrf/token'"
)
print(f"  Response: {out2.strip()}")
try:
    csrf_data = json.loads(out2)
    csrf_token = csrf_data['data']['token']
    print(f"  CSRF Token: {csrf_token[:40]}...")
except Exception as e:
    print(f"  Parse error: {e}")
    csrf_token = None

if page_token and csrf_token:
    # Step 3: POST login
    pwd_md5 = hashlib.md5('REDACTED_SSH_PASS'.encode()).hexdigest()
    print(f"\n[Step 3] POST /  (login)")
    print(f"  username: admin")
    print(f"  password md5: {pwd_md5}")
    print(f"  token (page): {page_token[:30]}...")
    print(f"  csrfToken: {csrf_token[:30]}...")
    
    post_out, _ = run(
        f"curl -v -b {COOKIE_FILE} -c {COOKIE_FILE} "
        f"-A '{UA}' "
        f"-X POST '{BASE_URL}/' "
        f"-H 'Accept: application/json, text/plain, */*' "
        f"-H 'Accept-Language: zh-CN,zh;q=0.9,en;q=0.8' "
        f"-H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' "
        f"-H 'Origin: {BASE_URL}' "
        f"-H 'Referer: {BASE_URL}/' "
        f"-H 'X-Requested-With: XMLHttpRequest' "
        f"-d 'username=admin&password={pwd_md5}&token={page_token}&csrfToken={csrf_token}' "
        f"2>&1 | grep -E '< HTTP|code|message|errors|Set-Cookie|Location|Forbidden|< Content' | head -20"
    )
    print(f"  Response: {post_out}")
    
    # Also get the response body
    post_body, _ = run(
        f"curl -sf -b {COOKIE_FILE} -c {COOKIE_FILE} "
        f"-A '{UA}' "
        f"-X POST '{BASE_URL}/' "
        f"-H 'Accept: application/json, text/plain, */*' "
        f"-H 'Content-Type: application/x-www-form-urlencoded; charset=UTF-8' "
        f"-H 'Origin: {BASE_URL}' "
        f"-H 'Referer: {BASE_URL}/' "
        f"-H 'X-Requested-With: XMLHttpRequest' "
        f"-d 'username=admin&password={pwd_md5}&token={page_token}&csrfToken={csrf_token}'"
    )
    print(f"  Body: {post_body.strip()[:500]}")

# Step 4: Check what page we're on now
print("\n[Step 4] GET / after login attempt")
out4, _ = run(
    f"curl -sf -b {COOKIE_FILE} -c {COOKIE_FILE} "
    f"-A '{UA}' "
    f"-L '{BASE_URL}/' "
    f"-w '\\nSTATUS:%{{http_code}} URL:%{{url_effective}}' "
    f"-o /tmp/after_login.html"
)
print(f"  Status: {out4.strip()}")
title, _ = run("grep -o '<title>[^<]*</title>' /tmp/after_login.html 2>/dev/null | head -3")
print(f"  Title: {title.strip()}")

c.close()
print("\nDone.")
