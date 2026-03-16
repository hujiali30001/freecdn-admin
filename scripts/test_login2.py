import paramiko
import sys
import io
import json
import hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = '134.175.67.168'
USER = 'ubuntu'
PASS = 'FreeCDN2026!'

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, port=22, username=USER, password=PASS, timeout=15)

def run(cmd, timeout=30):
    i, o, e = c.exec_command(cmd, timeout=timeout)
    out = o.read().decode('utf-8', errors='replace')
    err = e.read().decode('utf-8', errors='replace')
    return out, err

BASE_URL = "http://134.175.67.168:7788"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

print("=" * 60)
print("END-TO-END LOGIN TEST (with Origin/Referer)")
print("=" * 60)

# Step 1: Get CSRF token with cookie jar
print("\n[Step 1] GET / to get session cookie + CSRF token...")
out, _ = run(
    f"curl -sf -c /tmp/cookies2.txt "
    f"-A '{UA}' "
    f"'{BASE_URL}/csrf/token' "
)
print(f"  CSRF response: {out.strip()[:200]}")

try:
    csrf_token = json.loads(out)['data']['token']
    print(f"  Got token: {csrf_token[:40]}...")
except:
    print("  CSRF token parse failed")
    csrf_token = ""

# Also do a GET / first to get session
print("\n[Step 1b] GET / first to establish session...")
out, _ = run(
    f"curl -sf -c /tmp/cookies2.txt -b /tmp/cookies2.txt "
    f"-A '{UA}' "
    f"'{BASE_URL}/' "
    f"-o /dev/null -w 'HTTP:%{{http_code}} URL:%{{url_effective}}'"
)
print(f"  GET /: {out}")

# Re-get CSRF with session
out, _ = run(
    f"curl -sf -c /tmp/cookies2.txt -b /tmp/cookies2.txt "
    f"-A '{UA}' "
    f"'{BASE_URL}/csrf/token' "
)
print(f"\n[Step 1c] CSRF after session: {out.strip()[:200]}")
try:
    csrf_token = json.loads(out)['data']['token']
    print(f"  Token: {csrf_token[:40]}...")
except:
    pass

if csrf_token:
    # Step 2: POST login with Origin and Referer
    pwd_md5 = hashlib.md5('FreeCDN2026!'.encode()).hexdigest()
    print(f"\n[Step 2] POST login...")
    print(f"  Password MD5: {pwd_md5}")
    
    login_cmd = (
        f"curl -sf -b /tmp/cookies2.txt -c /tmp/cookies2.txt "
        f"-A '{UA}' "
        f"-X POST '{BASE_URL}/' "
        f"-H 'Origin: {BASE_URL}' "
        f"-H 'Referer: {BASE_URL}/' "
        f"-H 'Content-Type: application/x-www-form-urlencoded' "
        f"-d 'username=admin&password={pwd_md5}&csrfToken={csrf_token}' "
        f"-D /tmp/login2_headers.txt"
    )
    out, err = run(login_cmd)
    print(f"  Login body: {out.strip()[:500]}")
    
    out2, _ = run("cat /tmp/login2_headers.txt 2>/dev/null | head -10")
    print(f"  Headers: {out2.strip()}")

# Step 3: Access / after login
print("\n[Step 3] Access / after login (follow redirects)...")
out, _ = run(
    f"curl -sf -b /tmp/cookies2.txt -c /tmp/cookies2.txt "
    f"-A '{UA}' "
    f"-L '{BASE_URL}/' "
    f"| grep -o '<title>[^<]*</title>'"
)
print(f"  Title: {out.strip() or '(empty - probably 500 or blank)'}")

out2, _ = run(
    f"curl -sf -b /tmp/cookies2.txt "
    f"-A '{UA}' "
    f"-L '{BASE_URL}/' "
    f"-w '\\nSTATUS:%{{http_code}} URL:%{{url_effective}}' "
    f"-o /dev/null"
)
print(f"  Status: {out2.strip()}")

# Try /dashboard
out3, _ = run(
    f"curl -sf -b /tmp/cookies2.txt "
    f"-A '{UA}' "
    f"'{BASE_URL}/index/dashboard' "
    f"-w '\\nSTATUS:%{{http_code}} URL:%{{url_effective}}' "
    f"-o /tmp/dash.html"
)
print(f"\n[Step 4] GET /index/dashboard: {out3.strip()}")
out4, _ = run("grep -o '<title>[^<]*</title>' /tmp/dash.html 2>/dev/null | head -3")
print(f"  Dashboard title: {out4.strip() or '(check body)'}")
out5, _ = run("head -5 /tmp/dash.html 2>/dev/null")
print(f"  Body preview: {out5.strip()[:200]}")

c.close()
print("\nDone.")
