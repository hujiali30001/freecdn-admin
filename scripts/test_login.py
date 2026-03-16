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

print("=" * 60)
print("END-TO-END LOGIN TEST")
print("=" * 60)

# Step 1: Get CSRF token
print("\n[Step 1] Get CSRF token...")
out, _ = run("curl -sf -c /tmp/cookies.txt -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120' 'http://134.175.67.168:7788/csrf/token'")
print(f"  Response: {out.strip()}")
try:
    token_data = json.loads(out)
    csrf_token = token_data['data']['token']
    print(f"  CSRF Token: {csrf_token[:30]}...")
except Exception as e:
    print(f"  ERROR parsing CSRF: {e}")
    csrf_token = None

if csrf_token:
    # Step 2: POST login
    print("\n[Step 2] POST login with admin/FreeCDN2026!...")
    # Password needs to be MD5 hashed
    pwd_md5 = hashlib.md5('FreeCDN2026!'.encode()).hexdigest()
    print(f"  Password MD5: {pwd_md5}")
    
    login_cmd = (
        f"curl -sf -b /tmp/cookies.txt -c /tmp/cookies.txt "
        f"-A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120' "
        f"-X POST 'http://134.175.67.168:7788/' "
        f"-d 'username=admin&password={pwd_md5}&csrfToken={csrf_token}' "
        f"-D /tmp/login_headers.txt"
    )
    out, err = run(login_cmd)
    print(f"  Login response body (first 500 chars):")
    print(f"  {out[:500]}")
    
    # Check headers
    out2, _ = run("cat /tmp/login_headers.txt 2>/dev/null | head -20")
    print(f"\n  Response headers:")
    print(f"  {out2}")

# Step 3: Check session (follow redirect)
print("\n[Step 3] Access dashboard after login...")
out, _ = run(
    "curl -sf -b /tmp/cookies.txt -c /tmp/cookies.txt "
    "-A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120' "
    "-L 'http://134.175.67.168:7788/' "
    "| grep -o '<title>[^<]*</title>' | head -3"
)
print(f"  Page title: {out.strip() or '(empty)'}")

# Also check if we land on dashboard or still login
out2, _ = run(
    "curl -sf -b /tmp/cookies.txt -c /tmp/cookies.txt "
    "-A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120' "
    "-L 'http://134.175.67.168:7788/' "
    "-w '\\nHTTP_CODE:%{http_code} FINAL_URL:%{url_effective}'"
    " -o /dev/null"
)
print(f"  HTTP status: {out2.strip()}")

print("\n" + "=" * 60)
print("Summary:")
print(f"  Server: http://134.175.67.168:7788/")
print(f"  Username: admin")
print(f"  Password: FreeCDN2026!")
print("=" * 60)

c.close()
