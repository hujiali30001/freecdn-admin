"""
阶段一功能验收脚本 v3
- 修复：GET / 需要带 User-Agent 才能拿到登录页（否则返回 403）
- token 在 window.TEA.ACTION.data.token 里，不是 HTML input
- 使用正确的路由路径（通过 probe_routes.py 确认）
"""
import paramiko
import re
import time

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"
BASE = "http://127.0.0.1:7788"
DB_PASS = "FreeCDN2026!"
DB_USER = "freecdn"
DB_NAME = "freecdn"
ADMIN_USER = "admin"
ADMIN_PASS = "FreeCDN2026!"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=30):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()

def mysql(sql):
    cmd = f"mysql -h 127.0.0.1 -u {DB_USER} -p'{DB_PASS}' {DB_NAME} -sNe \"{sql}\" 2>/dev/null"
    return run(cmd).strip()

# ── 步骤 1：计算 MD5 密码 ─────────────────────────────────────────────────────
print("=== 1. 计算登录密码 MD5 ===")
md5_pass = run(f"echo -n '{ADMIN_PASS}' | md5sum | cut -d' ' -f1")
print(f"MD5: {md5_pass}")

# ── 步骤 2：GET / 带 UA，拿 window.TEA token（只请求一次）───────────────────
print("\n=== 2. GET / 获取登录页和 token ===")
get_raw = run(
    f'curl -si -c /tmp/verify_cookies.txt -A "{UA}" "{BASE}/" 2>&1',
    timeout=15
)
# 提取状态码
status_match = re.search(r'^HTTP/[\d.]+ (\d+)', get_raw)
status_code = status_match.group(1) if status_match else "?"
print(f"GET / 状态码: {status_code}")
# 分离 body
parts = get_raw.split('\r\n\r\n', 1)
get_html = parts[1] if len(parts) > 1 else get_raw

# ── 步骤 2b：GET /csrf/token 拿真正的 CSRF token ──────────────────────────
print("\n=== 2b. GET /csrf/token ===")
csrf_resp = run(
    f'curl -s -b /tmp/verify_cookies.txt -c /tmp/verify_cookies.txt -A "{UA}" "{BASE}/csrf/token" 2>&1',
    timeout=15
)
print(f"csrf/token 响应: {csrf_resp[:200]}")
# 解析 JSON 取 token
csrf_token_match = re.search(r'"token"\s*:\s*"([^"]+)"', csrf_resp)
csrf_token = csrf_token_match.group(1) if csrf_token_match else ""
print(f"csrfToken: {csrf_token[:30]}..." if csrf_token else "csrfToken: NOT FOUND")

# 从 window.TEA.ACTION.data.token 提取 token
token_match = re.search(r'"token"\s*:\s*"([a-f0-9]+)"', get_html)
if token_match:
    token = token_match.group(1)
    print(f"token: {token[:30]}...")
else:
    print("未找到 token，HTML 片段（前500字符）:")
    print(get_html[:500])
    token = ""

# 同时提取 systemName，顺便检查品牌替换
name_match = re.search(r'"systemName"\s*:\s*"([^"]+)"', get_html)
version_match = re.search(r'"version"\s*:\s*"([^"]+)"', get_html)
if name_match:
    print(f"systemName: {name_match.group(1)}")
if version_match:
    print(f"version: {version_match.group(1)}")

if not token:
    print("ERROR: 无法获取 token，终止")
    ssh.close()
    exit(1)

if not csrf_token:
    print("ERROR: 无法获取 csrfToken，终止")
    ssh.close()
    exit(1)

# ── 步骤 3：POST / 登录（同时发 csrfToken 和 token）─────────────────────────
print("\n=== 3. POST / 登录 ===")
login_resp = run(
    f'curl -si -b /tmp/verify_cookies.txt -c /tmp/verify_cookies.txt '
    f'-A "{UA}" -X POST "{BASE}/" '
    f'-d "csrfToken={csrf_token}&token={token}&username={ADMIN_USER}&password={md5_pass}&remember=1" 2>&1',
    timeout=15
)
print(login_resp[:800])

# 判断登录结果
LOGGED_IN = False
if '"code":0' in login_resp or '"data":' in login_resp:
    LOGGED_IN = True
elif "302" in login_resp.split('\n')[0] if login_resp else False:
    LOGGED_IN = True

# 尝试用 cookie 访问 dashboard 确认登录
dash_code = run(
    f'curl -s -o /dev/null -w "%{{http_code}}" -b /tmp/verify_cookies.txt '
    f'-A "{UA}" "{BASE}/dashboard" 2>&1',
    timeout=15
)
print(f"\ndashboard 状态码: {dash_code}")
if dash_code == "200":
    LOGGED_IN = True

print(f"登录状态: {'成功' if LOGGED_IN else '失败'}")

# ── 步骤 4：查询数据库 IDs ─────────────────────────────────────────────────────
print("\n=== 4. 查询数据库 IDs ===")
cluster_id = mysql("SELECT id FROM edgeNodeClusters LIMIT 1;")
node_id = mysql("SELECT id FROM edgeNodes LIMIT 1;")
server_id = mysql("SELECT id FROM edgeServers LIMIT 1;")
cert_id = mysql("SELECT id FROM edgeSSLCerts LIMIT 1;")
user_id = mysql("SELECT id FROM edgeUsers LIMIT 1;")
dns_id = mysql("SELECT id FROM edgeDNSDomains LIMIT 1;")
print(f"cluster={cluster_id}, node={node_id}, server={server_id}")
print(f"cert={cert_id}, user={user_id}, dns_domain={dns_id or '(空，未创建)'}")

# ── 步骤 5：构造待验收页面（使用正确的路由路径）──────────────────────────────
# 路径映射（通过 probe_routes.py 探测确认）：
# 集群详情   PLAN: /clusters/cluster/detail  -> 实际: /clusters/cluster?clusterId=X (有 ClusterSettings 子路由)
# 节点详情   PLAN: /clusters/cluster/node    -> 实际: /clusters/cluster/node?nodeId=X 
# 节点缓存   PLAN: /clusters/cluster/node/cache -> 实际: /clusters/cluster/node/settings/cache?nodeId=X
# 节点日志   PLAN: /clusters/cluster/node/log   -> 实际: /clusters/cluster/node/logs?nodeId=X
# 服务详情   PLAN: /servers/server/detail    -> 实际: /servers/server/settings?serverId=X
# 源站配置   PLAN: /servers/server/origins   -> 实际: /servers/server/settings/reverseProxy?serverId=X
# HTTPS配置  PLAN: /servers/server/https     -> 实际: /servers/server/settings/https?serverId=X
# 缓存规则   PLAN: /servers/server/cache     -> 实际: /servers/server/settings/cache?serverId=X
# WAF规则    PLAN: /servers/server/waf       -> 实际: /servers/server/settings/waf?serverId=X
# 重写规则   PLAN: /servers/server/rewrites  -> 实际: /servers/server/settings/rewrite?serverId=X
# Header规则 PLAN: /servers/server/headers   -> 实际: /servers/server/settings/headers?serverId=X
# 访问控制   PLAN: /servers/server/access    -> 实际: /servers/server/settings/access?serverId=X
# 证书详情   PLAN: /servers/certs/cert       -> 实际: /servers/certs/certPopup?certId=X (弹窗)
# 用户详情   PLAN: /users/user               -> 实际: /users/user?userId=X (已确认 403)
# 带宽统计   PLAN: /servers/server/stat      -> 实际: /servers/server/stat?serverId=X (已确认 403)

pages = []

if cluster_id:
    pages += [
        ("集群详情/基本设置",   f"/clusters/cluster?clusterId={cluster_id}",             "/clusters/cluster/detail"),
        ("集群节点列表",        f"/clusters/cluster/nodes?clusterId={cluster_id}",         "/clusters/cluster/detail"),
        ("集群基本设置",        f"/clusters/cluster/settings?clusterId={cluster_id}",      "/clusters/cluster/detail"),
    ]

if node_id and cluster_id:
    pages += [
        ("节点详情/基本信息",   f"/clusters/cluster/node?nodeId={node_id}",               "/clusters/cluster/node"),
        ("节点详情（含cluster）",f"/clusters/cluster/node/detail?nodeId={node_id}&clusterId={cluster_id}", "/clusters/cluster/node"),
        ("节点缓存配置",        f"/clusters/cluster/node/settings/cache?nodeId={node_id}","/clusters/cluster/node/cache"),
        ("节点日志配置",        f"/clusters/cluster/node/logs?nodeId={node_id}",          "/clusters/cluster/node/log"),
    ]

if server_id:
    pages += [
        ("服务详情/基本信息",   f"/servers/server/settings?serverId={server_id}",         "/servers/server/detail"),
        ("源站配置",           f"/servers/server/settings/reverseProxy?serverId={server_id}", "/servers/server/origins"),
        ("HTTPS配置",          f"/servers/server/settings/https?serverId={server_id}",   "/servers/server/https"),
        ("缓存规则",           f"/servers/server/settings/cache?serverId={server_id}",   "/servers/server/cache"),
        ("WAF规则",            f"/servers/server/settings/waf?serverId={server_id}",     "/servers/server/waf"),
        ("重写规则",           f"/servers/server/settings/rewrite?serverId={server_id}", "/servers/server/rewrites"),
        ("Header规则",         f"/servers/server/settings/headers?serverId={server_id}", "/servers/server/headers"),
        ("访问控制",           f"/servers/server/settings/access?serverId={server_id}",  "/servers/server/access"),
        ("带宽/流量统计",      f"/servers/server/stat?serverId={server_id}",             "/servers/server/stat"),
    ]

if cert_id:
    pages += [
        ("证书详情(弹窗)",     f"/servers/certs/certPopup?certId={cert_id}",            "/servers/certs/cert"),
    ]

if user_id:
    pages += [
        ("用户详情",           f"/users/user?userId={user_id}",                         "/users/user"),
    ]

if dns_id:
    pages += [
        ("DNS记录管理",        f"/dns/domain/records?domainId={dns_id}",               "/dns/domain/records"),
    ]
else:
    print("NOTE: edgeDNSDomains 为空，跳过 DNS 记录验收")

print(f"\n共 {len(pages)} 个待验收页面")

# ── 步骤 6：逐页验收 ─────────────────────────────────────────────────────────
print("\n=== 5. 页面验收 ===")
cookie_flag = "-b /tmp/verify_cookies.txt" if LOGGED_IN else ""
results = []

for name, path, plan_path in pages:
    url = BASE + path
    code = run(
        f'curl -s -o /dev/null -w "%{{http_code}}" {cookie_flag} -A "{UA}" "{url}" 2>&1',
        timeout=15
    ).strip()
    
    if code == "200":
        status = "OK"
        verdict = "PASS"
    elif code in ("301", "302", "307", "308"):
        # 跟随重定向，确认最终状态码
        redir_code = run(
            f'curl -sL -o /dev/null -w "%{{http_code}}" {cookie_flag} -A "{UA}" "{url}" 2>&1',
            timeout=15
        ).strip()
        status = f"REDIRECT({code}) -> {redir_code}"
        verdict = "PASS" if redir_code == "200" else "CHECK"
    elif code == "403":
        status = "AUTH_REQUIRED (403)"
        verdict = "AUTH" if not LOGGED_IN else "FAIL_AUTH"
    elif code == "404":
        status = "NOT FOUND (404)"
        verdict = "FAIL"
    elif code == "500":
        status = "SERVER ERROR (500)"
        verdict = "FAIL"
    else:
        status = f"UNKNOWN ({code})"
        verdict = "CHECK"
    
    icon = "✓" if verdict == "PASS" else ("?" if verdict in ("AUTH", "CHECK") else "✗")
    print(f"  [{verdict:<8}] [{code}] {name}")
    if verdict != "PASS":
        print(f"            {path}")
    results.append((name, path, plan_path, code, status, verdict))

# ── 步骤 7：汇总 ─────────────────────────────────────────────────────────────
print("\n=== 验收汇总 ===")
passed = [r for r in results if r[5] == "PASS"]
failed = [r for r in results if r[5] in ("FAIL",)]
auth_req = [r for r in results if r[5] in ("AUTH", "FAIL_AUTH")]
check = [r for r in results if r[5] == "CHECK"]

print(f"PASS     (页面正常): {len(passed)}/{len(results)}")
print(f"AUTH_REQ (需认证):   {len(auth_req)}/{len(results)}")
print(f"FAIL     (需修复):   {len(failed)}/{len(results)}")
print(f"CHECK    (需确认):   {len(check)}/{len(results)}")

if failed:
    print("\n[需修复]:")
    for r in failed:
        print(f"  [{r[3]}] {r[0]} -> {r[1]}")
        print(f"         PLAN路径: {r[2]}")

if auth_req and not LOGGED_IN:
    print(f"\n[注意] 未登录时 AUTH 页面视为路由存在（{len(auth_req)} 个），重新登录后再验收")
elif auth_req and LOGGED_IN:
    print(f"\n[警告] 已登录但仍 403 ({len(auth_req)} 个)，可能权限问题:")
    for r in auth_req:
        print(f"  {r[0]} -> {r[1]}")

print(f"\n路由探测结论: {len(passed)+len(auth_req)}/{len(results)} 路由存在")
print(f"登录状态: {'已登录' if LOGGED_IN else '未登录（使用 403=路由存在 作为判据）'}")

ssh.close()
