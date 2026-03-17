#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把新编译的 edge-api 打包进 tar.gz，上传到 GitHub Release v0.9.1
"""
import os, sys, shutil, subprocess, tarfile, tempfile, time
import urllib.request

TOKEN = os.environ.get("GITHUB_TOKEN", "")  # set via env: $env:GITHUB_TOKEN=...
if not TOKEN:
    print("Error: GITHUB_TOKEN env var not set. Usage: $env:GITHUB_TOKEN='ghp_...'")
    sys.exit(1)

REPO = "hujiali30001/freecdn-admin"
TAG = "v0.9.1"
ASSET_NAME = "freecdn-v0.9.1-linux-amd64.tar.gz"

BUILD_DIR = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\amd64\freecdn-v0.9.1-linux-amd64"
NEW_EDGE_API = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\amd64\edge-api-new"
EDGE_API_IN_BUILD = os.path.join(BUILD_DIR, "edge-api", "bin", "edge-api")
OUTPUT_TAR = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\freecdn-v0.9.1-linux-amd64.tar.gz"

def safe_print(s):
    b = (str(s) + "\n").encode('utf-8', errors='replace')
    sys.stdout.buffer.write(b)
    sys.stdout.buffer.flush()

def api(method, path, data=None, headers=None):
    import json
    url = f"https://api.github.com{path}"
    h = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "python-updater",
    }
    if headers:
        h.update(headers)
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    # 通过代理发送（GitHub API 也需要代理）
    proxy = urllib.request.ProxyHandler({
        "http": "http://127.0.0.1:4780",
        "https": "http://127.0.0.1:4780",
    })
    opener = urllib.request.build_opener(proxy)
    try:
        with opener.open(req, timeout=60) as resp:
            body = resp.read()
            return (json.loads(body) if body else {}), resp.status
    except urllib.error.HTTPError as e:
        body = e.read()
        return (json.loads(body) if body else {"error": str(e)}), e.code

safe_print("=" * 60)
safe_print("Step 1: 更新本地 build 目录的 edge-api")
safe_print("=" * 60)
shutil.copy2(NEW_EDGE_API, EDGE_API_IN_BUILD)
safe_print(f"  OK: {EDGE_API_IN_BUILD}  size={os.path.getsize(EDGE_API_IN_BUILD)/1024/1024:.1f}MB")

safe_print("\n" + "=" * 60)
safe_print("Step 2: 重新打包 tar.gz（Linux 格式，保留权限）")
safe_print("=" * 60)

os.makedirs(os.path.dirname(OUTPUT_TAR), exist_ok=True)

# 用 Python tarfile 打包（保持 Unix 权限位）
BASE = os.path.basename(BUILD_DIR)  # freecdn-v0.9.1-linux-amd64
with tarfile.open(OUTPUT_TAR, "w:gz") as tar:
    # 递归添加整个目录
    tar.add(BUILD_DIR, arcname=BASE)

size_mb = os.path.getsize(OUTPUT_TAR) / 1024 / 1024
safe_print(f"  OK: {OUTPUT_TAR}  size={size_mb:.1f}MB")

safe_print("\n" + "=" * 60)
safe_print("Step 3: 获取 GitHub Release ID")
safe_print("=" * 60)
resp, status = api("GET", f"/repos/{REPO}/releases/tags/{TAG}")
if "id" not in resp:
    safe_print(f"  ERROR: {status} {resp}")
    sys.exit(1)
release_id = resp["id"]
safe_print(f"  Release ID: {release_id}")

# 找到已有的同名 asset 并删除
safe_print("\n  查找已有 asset...")
for asset in resp.get("assets", []):
    if asset["name"] == ASSET_NAME:
        safe_print(f"  删除旧 asset: {asset['name']} (id={asset['id']})")
        api("DELETE", f"/repos/{REPO}/releases/assets/{asset['id']}")
        time.sleep(1)

safe_print("\n" + "=" * 60)
safe_print("Step 4: 上传新 tar.gz 到 Release")
safe_print("=" * 60)

upload_url = f"https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets?name={ASSET_NAME}"

with open(OUTPUT_TAR, "rb") as f:
    data = f.read()

import json
safe_print(f"  上传 {size_mb:.1f}MB...")
req = urllib.request.Request(
    upload_url,
    data=data,
    headers={
        "Authorization": f"token {TOKEN}",
        "Content-Type": "application/octet-stream",
        "User-Agent": "python-updater",
    },
    method="POST"
)

proxies_env = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")

import urllib.request
# 走代理
proxy = urllib.request.ProxyHandler({
    "http": "http://127.0.0.1:4780",
    "https": "http://127.0.0.1:4780",
})
opener = urllib.request.build_opener(proxy)

try:
    with opener.open(req, timeout=300) as resp:
        result = json.loads(resp.read())
        safe_print(f"  OK: asset id={result.get('id')} name={result.get('name')}")
        safe_print(f"      download_url={result.get('browser_download_url','')}")
except urllib.error.HTTPError as e:
    safe_print(f"  ERROR {e.code}: {e.read().decode()[:500]}")
    sys.exit(1)

safe_print("\n[DONE] Release tar.gz 已更新！")
safe_print(f"  以后 install.sh 下载的就是含 chown 修复的版本。")
