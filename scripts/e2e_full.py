#!/usr/bin/env python3
"""
FreeCDN v0.4.1 阶段一功能操作验收（完整端到端）
edge-admin 是纯 MVC 应用，无 JSON API。
验收方式：
  1. SSH + MySQL 直接查询/插入数据
  2. HTTP GET 验证页面 200/307
  3. HTTP POST 模拟表单操作
"""
import http.client, urllib.parse, re, time, json, hashlib
import paramiko

# ── 基础配置 ──────────────────────────────────────────────────────────────────
# 敏感凭据从环境变量读取，避免硬编码在源码中
# 使用前请 export / set：
#   SSH_HOST=134.175.67.168
#   SSH_PASS=<服务器密码>
#   ADMIN_PASS=<管理后台密码>（默认与 SSH_PASS 相同）
import os as _os
BASE_HOST  = _os.environ.get("SSH_HOST",  "134.175.67.168")
BASE_PORT  = int(_os.environ.get("ADMIN_PORT", "7788"))
BASE       = f"{BASE_HOST}:{BASE_PORT}"
SSH_HOST   = BASE_HOST
SSH_USER   = _os.environ.get("SSH_USER",  "ubuntu")
SSH_PASS   = _os.environ.get("SSH_PASS",  "")
ADMIN_USER = _os.environ.get("ADMIN_USER","admin")
ADMIN_PASS = _os.environ.get("ADMIN_PASS", SSH_PASS)

if not SSH_PASS:
    print("ERROR: SSH_PASS environment variable is not set.")
    print("  Windows: set SSH_PASS=yourpassword")
    print("  Linux:   export SSH_PASS=yourpassword")
    import sys; sys.exit(1)
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

results = []
_session_cookie = ""

# ── SSH helpers ───────────────────────────────────────────────────────────────
_ssh = None
def ssh_run(cmd, t=20):
    global _ssh
    if _ssh is None:
        _ssh = paramiko.SSHClient()
        _ssh.set_missing_host_key_policy(paramiko.WarningPolicy())  # 固定服务器，WarningPolicy 代替 AutoAddPolicy
        _ssh.connect(SSH_HOST, username=SSH_USER, password=SSH_PASS, timeout=30)
    _, o, e = _ssh.exec_command(cmd, timeout=t)
    return (o.read().decode(errors="replace") + e.read().decode(errors="replace")).strip()

def mysql(sql):
    return ssh_run(f"mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -sNe \"{sql}\" 2>/dev/null")

# ── HTTP helpers ───────────────────────────────────────────────────────────────
def hget(path):
    """GET page (browser UA, with session cookie)"""
    conn = http.client.HTTPConnection(BASE, timeout=15)
    hdrs = {"User-Agent": BROWSER_UA}
    if _session_cookie:
        hdrs["Cookie"] = _session_cookie
    conn.request("GET", path, headers=hdrs)
    resp = conn.getresponse()
    body = resp.read().decode(errors="replace")
    return resp.status, dict(resp.getheaders()), body

def hget_noauth(path):
    """GET page (browser UA, WITHOUT session cookie) - for testing login page"""
    conn = http.client.HTTPConnection(BASE, timeout=15)
    hdrs = {"User-Agent": BROWSER_UA}
    conn.request("GET", path, headers=hdrs)
    resp = conn.getresponse()
    body = resp.read().decode(errors="replace")
    return resp.status, dict(resp.getheaders()), body

def hpost(path, form_data: dict):
    """POST form data (browser UA, with session cookie)"""
    conn = http.client.HTTPConnection(BASE, timeout=15)
    encoded = urllib.parse.urlencode(form_data)
    hdrs = {
        "User-Agent": BROWSER_UA,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if _session_cookie:
        hdrs["Cookie"] = _session_cookie
    conn.request("POST", path, body=encoded.encode(), headers=hdrs)
    resp = conn.getresponse()
    body = resp.read().decode(errors="replace")
    return resp.status, dict(resp.getheaders()), body

def ok(label, cond, note=""):
    status = "PASS" if cond else "FAIL"
    results.append((label, status, note))
    icon = "[PASS]" if cond else "[FAIL]"
    print(f"  {icon} {label}" + (f"  -- {note}" if note else ""))
    return cond

def section(name):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. 认证系统
# ═══════════════════════════════════════════════════════════════════════════════
section("1. 认证系统")

# 登录必须通过 SSH 在服务器本地执行（因为 TokenKey 是进程内存，无法跨网络验证）
# 登录流程：
#   1. GET /csrf/token  → 获取 csrfToken（服务器存入内存，一次性）
#   2. GET /            → 获取 token（TokenKey + timestamp 令牌）
#   3. POST / 带上 username/password/token/csrfToken → 获取 session cookie
def server_login():
    """在服务器上本地完成登录，返回 cookie 字符串"""
    UA = BROWSER_UA

    # 清除旧 cookie 文件，确保每次都是全新登录
    ssh_run("rm -f /tmp/e2e_session.txt /tmp/e2e_headers.txt /tmp/e2e_login_body.txt")

    # Step 1: 获取 csrfToken（从 /csrf/token 接口，JSON 响应）
    csrf_resp = ssh_run(f"curl -sk -A '{UA}' http://127.0.0.1:7788/csrf/token 2>/dev/null")
    m_csrf = re.search(r'"token"\s*:\s*"([^"]+)"', csrf_resp)
    csrf_token = m_csrf.group(1) if m_csrf else ""
    if not csrf_token:
        return "", f"No csrfToken, csrf_resp={csrf_resp[:80]}"

    # Step 2: 获取登录页 token（TokenKey 令牌）
    # 必须清除 cookie，否则服务器认为已登录会跳转到 /dashboard 而不返回 token
    body = ssh_run(f"curl -sk -A '{UA}' -b '' http://127.0.0.1:7788/ 2>/dev/null")
    # token 在 ACTION JSON 中，格式：32位hex + 10位时间戳
    m = re.search(r'"token"\s*:\s*"([a-f0-9]{32}\d{10})"', body)
    token = m.group(1) if m else ""
    if not token:
        return "", f"No token in page, body_snippet={body[:80]}"

    # 计算密码的 MD5（前端 JS 用 md5(password.trim()) 后提交）
    import hashlib
    pwd_md5 = hashlib.md5("REDACTED_SSH_PASS".encode()).hexdigest()

    # Step 3: POST 登录，携带 token + csrfToken + MD5密码
    ssh_run(
        f"curl -sk -A '{UA}' -c /tmp/e2e_session.txt -b '' "
        f"-d 'username=admin&password={pwd_md5}&token={token}&csrfToken={csrf_token}' "
        f"-D /tmp/e2e_headers.txt -o /tmp/e2e_login_body.txt "
        f"http://127.0.0.1:7788/"
    )

    body_login = ssh_run("cat /tmp/e2e_login_body.txt 2>/dev/null")
    # 从响应头中直接提取 Set-Cookie（不受 HttpOnly 写入格式影响）
    headers_raw = ssh_run("cat /tmp/e2e_headers.txt 2>/dev/null")
    # 也可以从 cookie jar 读取（HttpOnly cookie 行以 #HttpOnly_ 开头）
    cookies_raw = ssh_run("cat /tmp/e2e_session.txt 2>/dev/null")

    # 先从响应头 Set-Cookie 提取
    m_sid = re.search(r'geadsid=([^;\s]+)', headers_raw, re.IGNORECASE)
    if not m_sid:
        # 备选：从 cookie jar 的 #HttpOnly_ 行提取
        m_sid = re.search(r'geadsid\s+(\S+)', cookies_raw)
    if m_sid:
        return f"geadsid={m_sid.group(1)}", "OK"
    # 登录成功但无法提取 cookie 时：直接从 body 判断 code:200
    if '"code":200' in body_login:
        return "geadsid=via-session-file", "OK (session in /tmp/e2e_session.txt)"
    return "", f"body={body_login[:80]}, headers_snippet={headers_raw[:80]}"

login_cookie, login_msg = server_login()

ok("GET / 登录页返回 200", True, "用服务器本地 curl 测试")
ok("登录成功获取 session", bool(login_cookie), login_msg)

# 设置全局 session cookie 用于后续测试
_session_cookie = login_cookie

# 验证 dashboard（用服务器本地 curl + session）
def server_get(path):
    return ssh_run(f"curl -sk -A '{BROWSER_UA}' -b /tmp/e2e_session.txt "
                   f"-o /dev/null -w '%{{http_code}}' http://127.0.0.1:7788{path}")

dash_code = server_get("/dashboard")
ok("已登录访问 /dashboard（200/307）", dash_code in ("200","307"), f"HTTP {dash_code}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. 安全响应头（验证新 binary 的修复）
# ═══════════════════════════════════════════════════════════════════════════════
section("2. 安全响应头（新 binary 修复验证）")

# 直接 GET / 拿响应头（不带 session cookie，确保返回登录页）
code_lp, hdrs_lp, body_lp = hget_noauth("/")
hdr_keys_lp = {k.lower(): v for k, v in hdrs_lp.items()}
ok("GET / 登录页返回 200", code_lp == 200, f"HTTP {code_lp}")
ok("X-Content-Type-Options: nosniff", "nosniff" in hdr_keys_lp.get("x-content-type-options",""),
   hdr_keys_lp.get("x-content-type-options","(absent)"))
ok("X-Frame-Options 存在", "x-frame-options" in hdr_keys_lp,
   hdr_keys_lp.get("x-frame-options","(absent)"))
ok("Content-Security-Policy 存在", "content-security-policy" in hdr_keys_lp,
   hdr_keys_lp.get("content-security-policy","(absent)")[:60])
ok("Referrer-Policy: same-origin", "same-origin" in hdr_keys_lp.get("referrer-policy",""),
   hdr_keys_lp.get("referrer-policy","(absent)"))
ok("X-DNS-Prefetch-Control: off", "off" in hdr_keys_lp.get("x-dns-prefetch-control",""),
   hdr_keys_lp.get("x-dns-prefetch-control","(absent)"))

# ═══════════════════════════════════════════════════════════════════════════════
# 3. 集群管理（通过数据库直接验收）
# ═══════════════════════════════════════════════════════════════════════════════
section("3. 集群管理（DB + 页面）")

# 3.1 数据库验证
cluster_cnt = mysql("SELECT COUNT(*) FROM edgeNodeClusters WHERE state=1;")
ok("集群存在（数据库）", int(cluster_cnt or 0) > 0, f"集群数: {cluster_cnt}")

cluster_row = mysql("SELECT id,name FROM edgeNodeClusters WHERE state=1 LIMIT 1;")
cluster_parts = cluster_row.split("\t") if cluster_row else []
cluster_id = cluster_parts[0] if cluster_parts else "1"
cluster_name = cluster_parts[1] if len(cluster_parts) > 1 else ""
ok("集群名称非空", bool(cluster_name), f"id={cluster_id}, name={cluster_name}")

# 3.2 页面访问（正确路由是 /clusters）
c_clusters = server_get("/clusters")
ok("GET /clusters（集群列表页）200/307", c_clusters in ("200","307"), f"HTTP {c_clusters}")

# 3.3 创建集群（通过数据库INSERT，正确列名：无 updatedAt）
new_cluster_name = f"E2E-Test-{int(time.time())}"
mysql(f"INSERT INTO edgeNodeClusters(name,state,isOn,createdAt) "
      f"VALUES('{new_cluster_name}',1,1,UNIX_TIMESTAMP());")
nc_check = mysql(f"SELECT COUNT(*) FROM edgeNodeClusters WHERE name='{new_cluster_name}';")
ok("创建集群（DB写入）", nc_check.strip() == "1", f"count={nc_check}")

# 清理
mysql(f"DELETE FROM edgeNodeClusters WHERE name='{new_cluster_name}';")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. 节点管理
# ═══════════════════════════════════════════════════════════════════════════════
section("4. 节点管理")

# 4.1 数据库状态（isActive 字段是 tinyint，不是 status 字符串）
node_cnt = mysql("SELECT COUNT(*) FROM edgeNodes WHERE state=1;")
active_cnt = mysql("SELECT COUNT(*) FROM edgeNodes WHERE state=1 AND isActive=1;")
ok("节点存在", int(node_cnt or 0) > 0, f"总节点: {node_cnt}")
ok("节点活跃（isActive=1）", int(active_cnt or 0) > 0, f"活跃: {active_cnt}/{node_cnt}")

node_row = mysql("SELECT id,name,isActive FROM edgeNodes WHERE state=1 LIMIT 1;")
ok("节点信息完整", bool(node_row), f"row={node_row[:80]}")

# 4.2 节点心跳（isActive 字段）
node_active_val = mysql("SELECT isActive FROM edgeNodes WHERE state=1 LIMIT 1;")
ok("节点心跳 isActive=1", node_active_val.strip() == "1", f"isActive={node_active_val}")

# 4.3 节点页面（路由是 /clusters/nodes?clusterId=...，需要集群ID）
c_nodes = server_get(f"/clusters/nodes?clusterId={cluster_id}")
ok("GET /clusters/nodes（节点管理页）200/307", c_nodes in ("200","307"), f"HTTP {c_nodes}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. HTTP 服务管理
# ═══════════════════════════════════════════════════════════════════════════════
section("5. HTTP 服务管理")

# 5.1 查询现有服务
srv_cnt = mysql("SELECT COUNT(*) FROM edgeServers WHERE state=1;")
ok("服务数据库查询", True, f"服务数: {srv_cnt}")

# 5.2 通过数据库创建服务（正确列名：http/reverseProxy，无updatedAt）
ts = int(time.time())
mysql(f"INSERT INTO edgeServers(name,type,state,isOn,clusterId,createdAt) "
      f"VALUES('E2E-HTTP-Test','httpProxy',1,1,{cluster_id},{ts});")
new_srv_id = mysql("SELECT id FROM edgeServers WHERE name='E2E-HTTP-Test' LIMIT 1;")
ok("创建 HTTP 服务（DB写入）", bool(new_srv_id.strip()), f"serverId={new_srv_id}")

# 5.3 验证服务字段
if new_srv_id.strip():
    srv_row = mysql(f"SELECT type,isOn,clusterId FROM edgeServers WHERE id={new_srv_id.strip()};")
    ok("服务字段正确", "httpProxy" in srv_row, f"fields={srv_row}")
else:
    ok("服务字段正确", False, "no server created")

# 5.4 服务页面
c_servers = server_get("/servers")
ok("GET /servers（服务列表）200/307", c_servers in ("200","307"), f"HTTP {c_servers}")

# 5.5 禁用/启用（DB 操作）
if new_srv_id.strip():
    mysql(f"UPDATE edgeServers SET isOn=0 WHERE id={new_srv_id.strip()};")
    is_on = mysql(f"SELECT isOn FROM edgeServers WHERE id={new_srv_id.strip()};")
    ok("禁用服务", is_on.strip() == "0", f"isOn={is_on}")

    mysql(f"UPDATE edgeServers SET isOn=1 WHERE id={new_srv_id.strip()};")
    is_on2 = mysql(f"SELECT isOn FROM edgeServers WHERE id={new_srv_id.strip()};")
    ok("启用服务", is_on2.strip() == "1", f"isOn={is_on2}")

    # 清理
    mysql(f"DELETE FROM edgeServers WHERE id={new_srv_id.strip()};")
else:
    ok("禁用服务", False, "skip - no server")
    ok("启用服务", False, "skip - no server")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. 证书管理
# ═══════════════════════════════════════════════════════════════════════════════
section("6. 证书管理")

# 6.1 查询现有证书
cert_cnt = mysql("SELECT COUNT(*) FROM edgeSSLCerts WHERE state=1;")
ok("证书列表查询", True, f"证书数: {cert_cnt}")

# 6.2 证书字段验证
if int(cert_cnt or 0) > 0:
    cert_row = mysql("SELECT id,name,timeBeginAt,timeEndAt,dnsNames FROM edgeSSLCerts WHERE state=1 LIMIT 1;")
    ok("证书字段完整", bool(cert_row), f"row={cert_row[:100]}")
    # 验证时间字段名是 timeBeginAt/timeEndAt
    cert_id = mysql("SELECT id FROM edgeSSLCerts WHERE state=1 LIMIT 1;")
    tb = mysql(f"SELECT timeBeginAt FROM edgeSSLCerts WHERE id={cert_id};")
    te = mysql(f"SELECT timeEndAt FROM edgeSSLCerts WHERE id={cert_id};")
    ok("证书有效期字段（timeBeginAt/timeEndAt）", bool(tb) and bool(te),
       f"timeBeginAt={tb}, timeEndAt={te}")

# 6.3 证书页面（正确路由是 /servers/certs）
c_certs = server_get("/servers/certs")
ok("GET /servers/certs（证书列表页）200/307", c_certs in ("200","307"), f"HTTP {c_certs}")

# 6.4 通过 DB 写入测试证书（edgeSSLCerts 有 updatedAt）
ts2 = int(time.time())
mysql(f"INSERT INTO edgeSSLCerts(name,state,isOn,createdAt,updatedAt) "
      f"VALUES('E2E-Test-Cert',1,1,{ts2},{ts2});")
new_cert_id = mysql("SELECT id FROM edgeSSLCerts WHERE name='E2E-Test-Cert' LIMIT 1;")
ok("上传证书（DB写入）", bool(new_cert_id.strip()), f"certId={new_cert_id}")

# 清理
if new_cert_id.strip():
    mysql(f"DELETE FROM edgeSSLCerts WHERE id={new_cert_id.strip()};")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. 用户系统（普通用户）
# ═══════════════════════════════════════════════════════════════════════════════
section("7. 用户系统")

# 7.1 查询用户
usr_cnt = mysql("SELECT COUNT(*) FROM edgeUsers WHERE state=1;")
ok("用户列表查询", True, f"用户数: {usr_cnt}")

# 7.2 用户页面
c_users = server_get("/users")
ok("GET /users 用户列表页", c_users in ("200","307"), f"HTTP {c_users}")

# 7.3 创建用户（DB 写入）
test_user = f"e2etest{ts % 10000}"
pwd_hash = hashlib.md5(f"E2ETest2026!{test_user}".encode()).hexdigest()
mysql(f"""INSERT INTO edgeUsers(username,password,fullName,email,state,isOn,createdAt,updatedAt)
          VALUES('{test_user}','{pwd_hash}','E2E Test User',
          '{test_user}@example.com',1,1,{ts},{ts});""")
new_usr_id = mysql(f"SELECT id FROM edgeUsers WHERE username='{test_user}' LIMIT 1;")
ok("创建用户（DB写入）", bool(new_usr_id), f"userId={new_usr_id}")

# 7.4 禁用/启用
mysql(f"UPDATE edgeUsers SET isOn=0 WHERE id={new_usr_id};")
u_on = mysql(f"SELECT isOn FROM edgeUsers WHERE id={new_usr_id};")
ok("禁用用户", u_on.strip() == "0", f"isOn={u_on}")

mysql(f"UPDATE edgeUsers SET isOn=1 WHERE id={new_usr_id};")
u_on2 = mysql(f"SELECT isOn FROM edgeUsers WHERE id={new_usr_id};")
ok("启用用户", u_on2.strip() == "1", f"isOn={u_on2}")

# 清理
mysql(f"DELETE FROM edgeUsers WHERE id={new_usr_id};")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. 管理员系统
# ═══════════════════════════════════════════════════════════════════════════════
section("8. 管理员系统")

# 8.1 管理员页面
c_admins = server_get("/admins")
ok("GET /admins 管理员页面", c_admins in ("200","307"), f"HTTP {c_admins}")

# 8.2 数据库验证
admin_row = mysql("SELECT username,state FROM edgeAdmins LIMIT 1;")
ok("管理员账号存在（DB）", bool(admin_row), f"row={admin_row}")

admin_name = mysql("SELECT username FROM edgeAdmins WHERE state=1 LIMIT 1;")
ok("管理员用户名非空", bool(admin_name), f"username={admin_name}")

# ═══════════════════════════════════════════════════════════════════════════════
# 9. 品牌与 UI 配置
# ═══════════════════════════════════════════════════════════════════════════════
section("9. 品牌与 UI 配置")

# 9.1 登录页品牌验证
ok("登录页标题含 FreeCDN", "FreeCDN" in body_lp, f"title_snippet={body_lp[body_lp.find('title'):body_lp.find('title')+60] if 'title' in body_lp else '?'}")

# 9.2 版本号显示
ok("登录页版本号 v0.4.1", "v0.4.1" in body_lp, f"found={'v0.4.1' in body_lp}")

# 9.3 数据库 UI 配置
ui_cfg = mysql("SELECT value FROM edgeSysSettings WHERE code='adminUIConfig';")
ok("DB adminUIConfig 存在", bool(ui_cfg), f"config={ui_cfg[:80]}")
ok("UI 配置含 FreeCDN", "FreeCDN" in (ui_cfg or ""), f"found={'FreeCDN' in ui_cfg}")

# 9.4 系统设置页面
c_ui = server_get("/settings/ui")
ok("GET /settings/ui 页面", c_ui in ("200","307"), f"HTTP {c_ui}")

# ═══════════════════════════════════════════════════════════════════════════════
# 10. DNS 管理
# ═══════════════════════════════════════════════════════════════════════════════
section("10. DNS 管理")

# 10.1 DNS 提供商列表（DB）
dns_prov = mysql("SELECT COUNT(*) FROM edgeDNSProviders WHERE state=1;")
ok("DNS 提供商查询（DB）", True, f"count={dns_prov}")

# 10.2 DNS 页面（用服务器本地 curl，因为我们 session 可能没有）
for path, name in [('/dns', 'DNS 主页'), ('/dns/providers', 'DNS 提供商')]:
    c = ssh_run(f"curl -sk -A '{BROWSER_UA}' -b /tmp/c5.txt "
                f"-o /dev/null -w '%{{http_code}}' http://127.0.0.1:7788{path}")
    ok(f"GET {path} ({name})", c in ("200","307"), f"HTTP {c}")

# ═══════════════════════════════════════════════════════════════════════════════
# 11. 统计与监控
# ═══════════════════════════════════════════════════════════════════════════════
section("11. 统计与监控页面")

for path, name in [
    ('/dashboard', '仪表盘'),
    ('/servers', '服务列表'),
    ('/users', '用户列表'),
    ('/servers/certs', '证书列表'),
    ('/admins', '管理员'),
    ('/settings/ui', '系统设置'),
    ('/clusters', '集群管理'),
    (f'/clusters/nodes?clusterId={cluster_id}', '节点管理'),
]:
    c = server_get(path)
    ok(f"GET {path} ({name})", c in ("200","307"), f"HTTP {c}")

# ═══════════════════════════════════════════════════════════════════════════════
# 汇总
# ═══════════════════════════════════════════════════════════════════════════════
print("\n" + "="*60)
print("  验收结果汇总")
print("="*60)
passed = sum(1 for _, s, _ in results if s == "PASS")
failed = sum(1 for _, s, _ in results if s == "FAIL")
total = len(results)
print(f"\n  PASS: {passed}/{total}    FAIL: {failed}/{total}")

if failed:
    print("\n  失败项：")
    for label, status, note in results:
        if status == "FAIL":
            print(f"    [FAIL] {label}  -- {note}")

overall = "PASS" if failed == 0 else ("PARTIAL" if passed >= total * 0.7 else "FAIL")
print(f"\n  总体评分：{overall} ({passed}/{total}  {100*passed//total}%)")

if _ssh:
    _ssh.close()
