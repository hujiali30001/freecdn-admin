import paramiko, re
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.175.67.168', username='ubuntu', password='REDACTED_SSH_PASS', timeout=30)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
def run(cmd, t=20):
    _, o, e = ssh.exec_command(cmd, timeout=t)
    return (o.read().decode(errors="replace") + e.read().decode(errors="replace")).strip()

# GET 登录页检查 systemName 和 version
html = run(f'curl -s -A "{UA}" "http://127.0.0.1:7788/" 2>&1')
nm = re.search(r'"systemName"\s*:\s*"([^"]+)"', html)
ver = re.search(r'"version"\s*:\s*"([^"]+)"', html)
print(f"systemName: {nm.group(1) if nm else 'NOT FOUND'}")
print(f"version: {ver.group(1) if ver else 'NOT FOUND'}")

# 登录后检查 teaName 和 teaTitle
md5 = run("echo -n 'REDACTED_SSH_PASS' | md5sum | cut -d' ' -f1")
get_raw = run(f'curl -si -c /tmp/v2.txt -A "{UA}" "http://127.0.0.1:7788/" 2>&1')
parts = get_raw.split('\r\n\r\n', 1)
html2 = parts[1] if len(parts) > 1 else get_raw
tm = re.search(r'"token"\s*:\s*"([a-f0-9]+)"', html2)
tok = tm.group(1) if tm else ""
cr = run(f'curl -s -b /tmp/v2.txt -c /tmp/v2.txt -A "{UA}" "http://127.0.0.1:7788/csrf/token" 2>&1')
cm = re.search(r'"token"\s*:\s*"([^"]+)"', cr)
ctok = cm.group(1) if cm else ""
run(f'curl -s -b /tmp/v2.txt -c /tmp/v2.txt -A "{UA}" -X POST "http://127.0.0.1:7788/" -d "csrfToken={ctok}&token={tok}&username=admin&password={md5}&remember=1" 2>&1')
dash = run(f'curl -s -b /tmp/v2.txt -A "{UA}" "http://127.0.0.1:7788/dashboard" 2>&1')
# 找 teaName 和 teaTitle
tname = re.search(r'"teaName"\s*:\s*"([^"]+)"', dash)
ttitle = re.search(r'"teaTitle"\s*:\s*"([^"]+)"', dash)
tver = re.search(r'"teaVersion"\s*:\s*"([^"]+)"', dash)
print(f"teaName: {tname.group(1) if tname else 'NOT FOUND'}")
print(f"teaTitle: {ttitle.group(1) if ttitle else 'NOT FOUND'}")
print(f"teaVersion: {tver.group(1) if tver else 'NOT FOUND'}")
ssh.close()
