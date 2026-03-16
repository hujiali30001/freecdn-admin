"""
诊断：查登录接口 + 正确表名
"""
import paramiko

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"
BASE = "http://127.0.0.1:7788"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=20):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    r = (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()
    print(r if r else "(no output)")
    return r

print("=== 1. 查登录相关路由 ===")
run("grep -r 'login' /usr/local/freecdn/edge-admin/bin/ 2>/dev/null | head -5 || true")

# 看一下登录页 HTML，找到实际的 POST action
print("\n=== 2. 获取根页面（找登录接口）===")
run(f"curl -si {BASE}/ 2>&1 | head -20")

print("\n=== 3. 尝试常见登录路径 ===")
for path in ["/index/do/login", "/api/login", "/index/login", "/admin/login"]:
    out = run(f"curl -si -X POST {BASE}{path} -d 'username=admin&password=test' 2>&1 | head -5")

print("\n=== 4. 查集群表名 ===")
DB_PASS = "FreeCDN2026!"
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SHOW TABLES LIKE '%luster%';\" 2>/dev/null")

print("\n=== 5. 查 cluster 表内容 ===")
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SHOW TABLES;\" 2>/dev/null | grep -i cluster")

print("\n=== 6. 查 edgeNodeClusters ===")
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SELECT id, name FROM edgeNodeClusters LIMIT 3;\" 2>/dev/null")

print("\n=== 7. 查 server 表名 ===")
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SHOW TABLES LIKE '%Server%';\" 2>/dev/null")
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SELECT id FROM edgeHTTPServers LIMIT 1;\" 2>/dev/null")
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SELECT id FROM edgeServers LIMIT 1;\" 2>/dev/null")

print("\n=== 8. 查 DNS 表名 ===")
run(f"mysql -h 127.0.0.1 -u freecdn -p'{DB_PASS}' freecdn -sNe \"SHOW TABLES LIKE '%DNS%';\" 2>/dev/null")

ssh.close()
