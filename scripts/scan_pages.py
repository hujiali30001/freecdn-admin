#!/usr/bin/env python3
"""
后台功能验收 - 带登录的页面扫描
1. GET / 拿 cookie + token
2. POST / 登录
3. 用登录 cookie 扫描所有功能页面
"""
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar as urllib_cookiejar
import hashlib
import re
import time
import sys

BASE = "http://134.175.67.168:7788"
USERNAME = "admin"
PASSWORD_PLAIN = "FreeCDN2026!"
PASSWORD_MD5 = hashlib.md5(PASSWORD_PLAIN.encode()).hexdigest()

PAGES = [
    # ── 集群与节点 ──────────────────────────────────────────────────
    ("Dashboard",           "/dashboard"),
    ("集群列表",            "/clusters"),
    ("节点列表",            "/clusters/nodes?clusterId=1"),
    ("访问日志",            "/clusters/logs"),
    # 定时任务无独立页面，通过 Dashboard layout 弹窗触发 (/clusters/tasks/listPopup)
    ("地区管理",            "/clusters/regions"),
    # ── HTTP 服务 ───────────────────────────────────────────────────
    ("服务列表",            "/servers"),
    ("创建服务",            "/servers/create"),
    ("IP黑名单",            "/servers/iplists"),
    ("服务分组",            "/servers/groups"),
    ("指标监控",            "/servers/metrics"),
    ("访问日志查询",        "/servers/logs"),
    # ── 证书管理 ────────────────────────────────────────────────────
    ("证书列表",            "/servers/certs"),
    ("申请证书(ACME)",      "/servers/certs/acme"),
    ("上传证书(弹窗)",      "/servers/certs/uploadPopup"),
    # ── DNS ─────────────────────────────────────────────────────────
    ("DNS域名列表",         "/dns"),
    # ── 管理员 ──────────────────────────────────────────────────────
    ("管理员列表",          "/admins"),
    ("创建管理员(弹窗)",    "/admins/createPopup"),
    ("SSH授权(grants)",     "/clusters/grants"),
    ("个人信息",            "/settings/profile"),
    # ── 用户 ────────────────────────────────────────────────────────
    ("用户列表",            "/users"),
    # ── 系统设置 ────────────────────────────────────────────────────
    ("基本设置",            "/settings"),
    ("安全设置",            "/settings/security"),
    ("数据库状态",          "/db"),
    # ── 日志 ────────────────────────────────────────────────────────
    ("操作日志",            "/log"),
    ("登录日志",            "/settings/login"),
]

# ── Cookie jar + opener ───────────────────────────────────────────
cookie_jar = urllib_cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [("User-Agent", "Mozilla/5.0")]

def get(path, timeout=10):
    try:
        resp = opener.open(f"{BASE}{path}", timeout=timeout)
        body = resp.read().decode(errors="replace")
        return resp.getcode(), body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)

def post(path, data: dict, timeout=10):
    payload = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=payload)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    try:
        resp = opener.open(req, timeout=timeout)
        body = resp.read().decode(errors="replace")
        return resp.getcode(), body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except Exception as ex:
        return 0, str(ex)

# ── Step 1: GET 首页，拿 token ─────────────────────────────────────
print("[1] GET 首页拿 token + cookie...")
code, body = get("/")
print(f"    GET /: {code}")

# 从 HTML 中提取 token（格式：value="<32位md5><timestamp>"）
# <input type="hidden" name="token" ...> 的 v-model="token"
# token 实际上是在页面 HTML 里，通过模板渲染的
# 找 name="token" 的 input value 或者 data-token
token = ""
m = re.search(r'name=["\']token["\'][^>]*value=["\']([0-9a-f]{32}\d+)["\']', body)
if m:
    token = m.group(1)
    print(f"    token (from input): {token}")
else:
    # 也可能在 script 里
    m = re.search(r'"token"\s*:\s*"([0-9a-f]{32}\d+)"', body)
    if m:
        token = m.group(1)
        print(f"    token (from script): {token}")
    else:
        # 找所有 input hidden value
        all_inputs = re.findall(r'<input[^>]+type=["\']hidden["\'][^>]*>', body, re.I)
        print(f"    hidden inputs: {all_inputs[:5]}")
        # 还找 window.XX.token 这类赋值
        m2 = re.search(r'["\']token["\'][,\s:]+["\']([0-9a-f]{32,}[0-9]+)["\']', body)
        if m2:
            token = m2.group(1)
            print(f"    token (from json): {token}")

print(f"    cookies: {[(c.name, c.value[:20]) for c in cookie_jar]}")

if not token:
    print("    [WARN] 未找到 token，尝试直接扫描（可能大部分 403）")

# ── Step 2: GET /csrf/token 拿 CSRF Token ─────────────────────────
print("\n[1.5] GET /csrf/token ...")
import json as _json
csrf_code, csrf_body = get("/csrf/token")
print(f"    GET /csrf/token: {csrf_code}")
csrf_token = ""
try:
    csrf_data = _json.loads(csrf_body)
    csrf_token = csrf_data.get("data", {}).get("token", "")
    print(f"    csrfToken: {csrf_token[:40]}...")
except Exception as e:
    print(f"    [WARN] 解析 csrfToken 失败: {e}, body={csrf_body[:100]}")

# ── Step 3: POST 登录 ─────────────────────────────────────────────
print("\n[2] POST 登录...")
login_data = {
    "username": USERNAME,
    "password": PASSWORD_MD5,
    "token": token,
    "csrfToken": csrf_token,
}

code, resp_body = post("/", login_data)
print(f"    POST /: {code}")

# 判断是否登录成功
if '"code":200' in resp_body or '"isOk":true' in resp_body or '"localSid"' in resp_body:
    print("    [OK] 登录成功")
elif "incorrect" in resp_body.lower() or "failed" in resp_body.lower() or code != 200:
    print(f"    [WARN] 可能登录失败: {resp_body[:200]}")
else:
    print(f"    [?] 响应: {resp_body[:150]}")

print(f"    cookies after login: {[(c.name, c.value[:20]) for c in cookie_jar]}")

# ── Step 4: 扫描所有页面 ──────────────────────────────────────────
print(f"\n[3] 扫描 {len(PAGES)} 个页面...")
print("-" * 75)

results = []
ok_count = err_count = redirect_count = 0

for name, path in PAGES:
    code, body = get(path)
    # 判断
    # 200 + body 有实质内容 = 正常
    # 302/301 = 跳转（通常是未登录跳回 /）
    # 403 = 未授权
    # 500 = bug
    # 200 但 body 很短或含登录表单 = 被重定向到登录页了
    # 登录页特征：同时含有 passwordMd5（登录页特有的 JS 字段）AND 登录表单标志
    # 排除含密码修改表单的设置页（这些页面也有 name="password" 但不是登录页）
    is_login_page = ("passwordMd5" in body and "v-model=\"passwordMd5\"" in body)
    note = ""
    if code == 200 and not is_login_page:
        flag = "OK "
        ok_count += 1
    elif code == 200 and is_login_page:
        flag = ">>>"
        note = "重定向到登录页(未认证)"
        redirect_count += 1
    elif code in (301, 302):
        flag = ">>>"
        note = "重定向"
        redirect_count += 1
    elif code == 404:
        flag = "404"
        note = "页面不存在"
        err_count += 1
    elif code == 500:
        flag = "500"
        note = "服务端错误! " + body[:100].replace("\n", " ")
        err_count += 1
    elif code == 0:
        flag = "ERR"
        note = body[:60]
        err_count += 1
    else:
        flag = f"{code} "
        note = body[:60].replace("\n", " ")
        err_count += 1

    results.append((flag, code, name, path, note, body))
    line = f"  [{flag}] {name:<28} {path:<42}"
    if note:
        line += f" # {note}"
    print(line)
    time.sleep(0.05)

print("-" * 75)
print(f"OK={ok_count}  redirect/unauth={redirect_count}  error={err_count}")

# 500 详情
for flag, code, name, path, note, body in results:
    if code == 500:
        print(f"\n[500 DETAIL] {name} {path}")
        print(body[:500])

# 保存
out = "C:\\Users\\Administrator\\.workbuddy\\FreeCDN\\scripts\\scan_results.txt"
with open(out, "w", encoding="utf-8") as f:
    f.write(f"Scan time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Base: {BASE}\nCookies: {[(c.name,c.value[:30]) for c in cookie_jar]}\n\n")
    for flag, code, name, path, note, _ in results:
        f.write(f"[{flag}] {code} {name:<28} {path}\n")
        if note:
            f.write(f"       # {note}\n")
    f.write(f"\nOK={ok_count} redirect={redirect_count} err={err_count}\n")
print(f"\nSaved to {out}")
