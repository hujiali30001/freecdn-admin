"""
DNS 记录验收：
1. 通过 UI 创建一个测试 DNS 域名
2. 查询 edgeDNSDomains 获取 ID
3. 验收 /dns/domain/records?domainId=X
"""
import paramiko
import re
import time

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"
BASE = "http://127.0.0.1:7788"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=20):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()

def mysql(sql):
    cmd = f"mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -sNe \"{sql}\" 2>/dev/null"
    return run(cmd).strip()

# 登录
md5 = run("echo -n 'REDACTED_SSH_PASS' | md5sum | cut -d' ' -f1")
get_raw = run(f'curl -si -c /tmp/dns_cookies.txt -A "{UA}" "{BASE}/" 2>&1', timeout=15)
parts = get_raw.split('\r\n\r\n', 1)
html = parts[1] if len(parts) > 1 else get_raw
tm = re.search(r'"token"\s*:\s*"([a-f0-9]+)"', html)
tok = tm.group(1) if tm else ""
cr = run(f'curl -s -b /tmp/dns_cookies.txt -c /tmp/dns_cookies.txt -A "{UA}" "{BASE}/csrf/token" 2>&1', timeout=15)
cm = re.search(r'"token"\s*:\s*"([^"]+)"', cr)
ctok = cm.group(1) if cm else ""
resp = run(f'curl -s -b /tmp/dns_cookies.txt -c /tmp/dns_cookies.txt -A "{UA}" -X POST "{BASE}/" -d "csrfToken={ctok}&token={tok}&username=admin&password={md5}&remember=1" 2>&1', timeout=15)
login_ok = '"code":200' in resp
print(f"登录: {'成功' if login_ok else '失败: ' + resp[:100]}")

# 检查当前 DNS 表状态
print("\n=== DNS 域名 ===")
dns_count = mysql("SELECT COUNT(*) FROM edgeDNSDomains;")
print(f"当前 DNS 域名数: {dns_count}")

# 找 DNS 域名创建 API
print("\n=== 找 DNS 创建 API ===")
# 先看 dns/domains/createPopup 接口要什么参数
cr2 = run(f'curl -s -b /tmp/dns_cookies.txt -A "{UA}" "{BASE}/dns/domains/createPopup" 2>&1')
print(f"createPopup 响应长度: {len(cr2)}")
# 找 DNS Provider 列表
provider_code = run(f'curl -s -b /tmp/dns_cookies.txt -A "{UA}" "{BASE}/dns/providers" 2>&1')
print(f"providers 响应长度: {len(provider_code)}")
# 找可用的 provider code
p_codes = re.findall(r'"code"\s*:\s*"([a-z][^"]{1,30})"', provider_code)
print(f"provider codes (前5): {p_codes[:5]}")

# 获取 CSRF token 用于提交
cr3 = run(f'curl -s -b /tmp/dns_cookies.txt -c /tmp/dns_cookies.txt -A "{UA}" "{BASE}/csrf/token" 2>&1', timeout=15)
cm3 = re.search(r'"token"\s*:\s*"([^"]+)"', cr3)
ctok2 = cm3.group(1) if cm3 else ""

# 查 edgeDNSProviders 表中有没有 provider
dns_providers = mysql("SELECT id,code FROM edgeDNSProviders LIMIT 5;")
print(f"\nDNS providers: {dns_providers or '(空)'}")

# 如果有 provider，尝试创建域名
if dns_providers:
    provider_id = mysql("SELECT id FROM edgeDNSProviders LIMIT 1;")
    print(f"使用 provider ID: {provider_id}")
    
    # POST 到 /dns/domains/createPopup 创建域名
    create_resp = run(
        f'curl -s -b /tmp/dns_cookies.txt -c /tmp/dns_cookies.txt -A "{UA}" '
        f'-X POST "{BASE}/dns/domains/createPopup" '
        f'-d "csrfToken={ctok2}&providerId={provider_id}&name=test.freecdntest.duckdns.org" 2>&1',
        timeout=15
    )
    print(f"创建域名响应: {create_resp[:300]}")
else:
    print("无 DNS provider，需要先添加 provider")
    # 直接往数据库插入测试数据
    print("\n=== 直接插入测试 DNS 域名 ===")
    insert_r = mysql("INSERT INTO edgeDNSDomains (name, state, createdAt, updatedAt, uniqueId) VALUES ('test.example.com', 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 'test001') ON DUPLICATE KEY UPDATE name=name;")
    print(f"插入结果: {insert_r or 'OK'}")

# 检查现在有没有 DNS 域名
dns_id = mysql("SELECT id FROM edgeDNSDomains LIMIT 1;")
print(f"\nDNS domain ID: {dns_id or '(仍然空)'}")

if dns_id:
    # 验收 DNS 记录路由
    code = run(f'curl -s -o /dev/null -w "%{{http_code}}" -b /tmp/dns_cookies.txt -A "{UA}" "{BASE}/dns/domain/records?domainId={dns_id}" 2>&1', timeout=15)
    print(f"\nDNS 记录路由验收: [{code}] /dns/domain/records?domainId={dns_id}")
    if code == "200":
        print("DNS 记录验收: PASS")
    else:
        # 尝试更多路径
        for p in ["/dns/domains/records", "/dns/records", f"/dns/domain?domainId={dns_id}"]:
            c2 = run(f'curl -s -o /dev/null -w "%{{http_code}}" -b /tmp/dns_cookies.txt -A "{UA}" "{BASE}{p}" 2>&1', timeout=15)
            print(f"[{c2}] {p}")

ssh.close()
