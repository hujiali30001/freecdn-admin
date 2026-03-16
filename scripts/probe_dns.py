import paramiko

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"
BASE = "http://127.0.0.1:7788"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def get_code(path):
    cmd = f"curl -s -o /dev/null -w '%{{http_code}}' '{BASE}{path}' 2>&1"
    _, out, err = ssh.exec_command(cmd, timeout=15)
    return out.read().decode().strip()

# DNS 相关路径探测
dns_paths = [
    "/dns/domains/domain?domainId=1",
    "/dns/domain/records?domainId=1",
    "/dns/domains/records?domainId=1",
    "/dns/domain?domainId=1",
    "/dns/record?domainId=1",
    "/dns/records?domainId=1",
    "/dns/domain/record?domainId=1",
]

# 先查数据库找 DNS 域名 ID
_, out, _ = ssh.exec_command("mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -sNe 'SELECT id FROM edgeDNSDomains LIMIT 1;' 2>/dev/null", timeout=15)
dns_id = out.read().decode().strip()
print(f"DNS domain ID: '{dns_id}'")

print("\nDNS 路由探测:")
for path in dns_paths:
    if dns_id:
        path = path.replace("domainId=1", f"domainId={dns_id}")
    code = get_code(path)
    marker = ""
    if code == "403":
        marker = " <== 需登录(路由存在)"
    elif code == "404":
        marker = "  (路由不存在)"
    elif code == "200":
        marker = " <== OK"
    print(f"[{code}]  {path}{marker}")

# 同时探测登录机制
print("\n=== 登录机制探测 ===")
# 1. 从 127.0.0.1 访问是否能得到登录页
_, out, _ = ssh.exec_command("curl -si http://127.0.0.1:7788/ 2>&1 | head -30", timeout=15)
print("GET / 响应前30行:")
print(out.read().decode())

# 2. 检查 /login 或其他登录路径
for login_path in ["/login", "/index/login", "/admin/login", "/?from=%2Fdashboard"]:
    code = get_code(login_path)
    print(f"[{code}] {login_path}")

ssh.close()
