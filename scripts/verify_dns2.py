import paramiko, re, time
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.175.67.168', username='ubuntu', password='FreeCDN2026!', timeout=30)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"
BASE = "http://127.0.0.1:7788"

def run(c, timeout=20):
    _, o, e = ssh.exec_command(c, timeout=timeout)
    return (o.read().decode(errors="replace") + e.read().decode(errors="replace")).strip()
def mysql(s):
    return run(f"mysql -h 127.0.0.1 -u freecdn -p'FreeCDN2026!' freecdn -sNe \"{s}\" 2>/dev/null").strip()

# 插入测试 DNS 域名（使用正确字段）
print("=== 插入测试 DNS 域名 ===")
r = run("mysql -h 127.0.0.1 -u freecdn -p'FreeCDN2026!' freecdn -e \"INSERT INTO edgeDNSDomains (adminId, name, state, createdAt, isOn, isUp, isDeleted) VALUES (1, 'test.example.com', 1, UNIX_TIMESTAMP(), 1, 1, 0);\" 2>&1")
print(r or "OK")

dns_id = mysql("SELECT id FROM edgeDNSDomains LIMIT 1;")
print(f"DNS domain ID: {dns_id}")

if not dns_id:
    print("插入失败")
    ssh.close()
    exit(1)

# 登录
md5 = run("echo -n 'FreeCDN2026!' | md5sum | cut -d' ' -f1")
get_raw = run(f'curl -si -c /tmp/dns2_cookies.txt -A "{UA}" "{BASE}/" 2>&1', timeout=15)
parts = get_raw.split('\r\n\r\n', 1)
html = parts[1] if len(parts) > 1 else get_raw
tm = re.search(r'"token"\s*:\s*"([a-f0-9]+)"', html)
tok = tm.group(1) if tm else ""
cr = run(f'curl -s -b /tmp/dns2_cookies.txt -c /tmp/dns2_cookies.txt -A "{UA}" "{BASE}/csrf/token" 2>&1', timeout=15)
cm = re.search(r'"token"\s*:\s*"([^"]+)"', cr)
ctok = cm.group(1) if cm else ""
resp = run(f'curl -s -b /tmp/dns2_cookies.txt -c /tmp/dns2_cookies.txt -A "{UA}" -X POST "{BASE}/" -d "csrfToken={ctok}&token={tok}&username=admin&password={md5}&remember=1" 2>&1', timeout=15)
login_ok = '"code":200' in resp
print(f"登录: {'OK' if login_ok else 'FAIL'}")

# 验收 DNS 记录路由
print("\n=== DNS 记录路由验收 ===")
for path in [
    f"/dns/domain/records?domainId={dns_id}",
    f"/dns/domains/domain?domainId={dns_id}",
    f"/dns/domain?domainId={dns_id}",
]:
    code = run(f'curl -sL -o /dev/null -w "%{{http_code}}" -b /tmp/dns2_cookies.txt -A "{UA}" "{BASE}{path}" 2>&1', timeout=15)
    print(f"[{code}] {path}")

# 清理测试数据
print("\n=== 清理测试 DNS 域名 ===")
r = mysql(f"DELETE FROM edgeDNSDomains WHERE id={dns_id} AND name='test.example.com';")
print(r or "已删除")

ssh.close()
