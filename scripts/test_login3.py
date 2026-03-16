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

# Use localhost to avoid rate limit
BASE_URL = "http://127.0.0.1:7788"
EXTERNAL_URL = "http://134.175.67.168:7788"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

print("=" * 60)
print("CORRECT LOGIN TEST - Using page-embedded token")
print("=" * 60)

# Step 1: GET login page and extract embedded token
print("\n[Step 1] GET login page from container (localhost)...")
out, _ = run(
    f"docker exec freecdn-admin curl -sf -A '{UA}' "
    f"-c /tmp/ck3.txt "
    f"'{BASE_URL}/' "
    f"-D /tmp/headers3.txt"
)
page_html = out

# Extract token from window.TEA ACTION data
token_match = re.search(r'"token"\s*:\s*"([^"]+)"', page_html)
if token_match:
    page_token = token_match.group(1)
    print(f"  Extracted token: {page_token}")
else:
    print("  Could not find token in page!")
    page_token = None

# Also extract CSRF token from form if present
csrf_input = re.search(r'name=["\']csrfToken["\'][^>]*value=["\']([^"\']+)["\']', page_html)
if csrf_input:
    print(f"  CSRF input: {csrf_input.group(1)}")

# Check cookies
out2, _ = run("cat /tmp/ck3.txt 2>/dev/null")
print(f"\n  Cookies: {out2.strip()}")
out3, _ = run("cat /tmp/headers3.txt 2>/dev/null | head -5")
print(f"  Response headers: {out3.strip()}")

if page_token:
    # Step 2: POST login with the page token
    pwd_md5 = hashlib.md5('REDACTED_SSH_PASS'.encode()).hexdigest()
    print(f"\n[Step 2] POST login with token from page...")
    print(f"  password MD5: {pwd_md5}")
    print(f"  token: {page_token}")
    
    # Try with Tea framework format
    login_cmd = (
        f"docker exec freecdn-admin curl -sf "
        f"-b /tmp/ck3.txt -c /tmp/ck3.txt "
        f"-A '{UA}' "
        f"-X POST '{BASE_URL}/' "
        f"-H 'Origin: {BASE_URL}' "
        f"-H 'Referer: {BASE_URL}/' "
        f"-H 'X-Requested-With: XMLHttpRequest' "
        f"-H 'Content-Type: application/x-www-form-urlencoded' "
        f"-d 'username=admin&password={pwd_md5}&token={page_token}' "
        f"-D /tmp/login3_headers.txt"
    )
    out, _ = run(login_cmd)
    print(f"  Response: {out.strip()[:500]}")
    
    h3, _ = run("cat /tmp/login3_headers.txt 2>/dev/null | head -10")
    print(f"  Headers: {h3.strip()}")

# Step 3: Check if login succeeded
print("\n[Step 3] Access / after login...")
out, _ = run(
    f"docker exec freecdn-admin curl -sf "
    f"-b /tmp/ck3.txt -A '{UA}' "
    f"-L '{BASE_URL}/' "
    f"| grep -o '<title>[^<]*</title>'"
)
print(f"  Title: {out.strip()}")

out2, _ = run(
    f"docker exec freecdn-admin curl -sf "
    f"-b /tmp/ck3.txt -A '{UA}' "
    f"-L '{BASE_URL}/' "
    f"-w 'STATUS:%{{http_code}} URL:%{{url_effective}}' -o /dev/null"
)
print(f"  Status: {out2.strip()}")

c.close()
print("\nDone.")
