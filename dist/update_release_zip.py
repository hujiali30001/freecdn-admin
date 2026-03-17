#!/usr/bin/env python3
"""
更新 GitHub Release v0.9.1 上的 tar.gz 和 SHA256SUMS：
1. 删除旧的 tar.gz asset
2. 上传新的 tar.gz
3. 更新 SHA256SUMS
"""
import http.client, json, os, hashlib

TOKEN = os.environ.get("GITHUB_TOKEN", "")  # set via env: $env:GITHUB_TOKEN=...
REPO = "hujiali30001/freecdn-admin"
VERSION = "v0.9.1"
WORK_DIR = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\amd64"
TAR_NAME = "freecdn-v0.9.1-linux-amd64.tar.gz"
TAR_PATH = os.path.join(WORK_DIR, TAR_NAME)

def github_api(method, path, body=None, extra_headers=None):
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-Builder/1.0",
    }
    if extra_headers:
        headers.update(extra_headers)
    if body and not isinstance(body, (bytes, bytearray)):
        body = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    conn.request(method, path, body=body, headers=headers)
    resp = conn.getresponse()
    data = resp.read()
    try:
        return resp.status, json.loads(data)
    except:
        return resp.status, data.decode()

# 1. 找到 release
print(f"Finding release {VERSION}...")
status, data = github_api("GET", f"/repos/{REPO}/releases/tags/{VERSION}")
if status != 200:
    print(f"ERROR: {status} {data}")
    exit(1)
release_id = data["id"]
upload_url_base = data["upload_url"].split("{")[0]
print(f"  Release ID: {release_id}")
print(f"  Upload URL: {upload_url_base}")

# 2. 列出现有 assets，找 tar.gz 和 SHA256SUMS
print("\nListing assets...")
status, assets = github_api("GET", f"/repos/{REPO}/releases/{release_id}/assets")
asset_map = {a["name"]: a["id"] for a in assets}
print(f"  Found assets: {list(asset_map.keys())}")

# 3. 删除旧 tar.gz
if TAR_NAME in asset_map:
    print(f"\nDeleting old {TAR_NAME}...")
    status, _ = github_api("DELETE", f"/repos/{REPO}/releases/assets/{asset_map[TAR_NAME]}")
    print(f"  Status: {status}")

# 4. 上传新 tar.gz
print(f"\nUploading {TAR_NAME} ({os.path.getsize(TAR_PATH)/1024/1024:.1f} MB)...")
with open(TAR_PATH, "rb") as f:
    data = f.read()

conn = http.client.HTTPSConnection("uploads.github.com")
headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "FreeCDN-Builder/1.0",
    "Content-Type": "application/octet-stream",
    "Content-Length": str(len(data)),
}
conn.request("POST", f"/repos/{REPO}/releases/{release_id}/assets?name={TAR_NAME}", body=data, headers=headers)
resp = conn.getresponse()
resp_data = resp.read()
print(f"  Status: {resp.status}")
if resp.status in (200, 201):
    print(f"  Upload OK")
else:
    print(f"  Error: {resp_data.decode()[:300]}")

# 5. 计算 SHA256 并更新 SHA256SUMS
sha256 = hashlib.sha256(open(TAR_PATH, "rb").read()).hexdigest()
checksums_content = f"{sha256}  {TAR_NAME}\n"

# 找 install.sh SHA256
install_sh = os.path.join(r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\amd64\freecdn-v0.9.1-linux-amd64", "install.sh")
if os.path.exists(install_sh):
    sha256_sh = hashlib.sha256(open(install_sh, "rb").read()).hexdigest()
    checksums_content += f"{sha256_sh}  install.sh\n"

if "SHA256SUMS" in asset_map:
    print(f"\nDeleting old SHA256SUMS...")
    status, _ = github_api("DELETE", f"/repos/{REPO}/releases/assets/{asset_map['SHA256SUMS']}")

print(f"\nUploading SHA256SUMS...")
sha_data = checksums_content.encode()
conn2 = http.client.HTTPSConnection("uploads.github.com")
conn2.request("POST", f"/repos/{REPO}/releases/{release_id}/assets?name=SHA256SUMS",
              body=sha_data, headers={
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "FreeCDN-Builder/1.0",
    "Content-Type": "text/plain",
    "Content-Length": str(len(sha_data)),
})
resp2 = conn2.getresponse()
print(f"  Status: {resp2.status}")

print(f"\n=== SHA256SUMS ===\n{checksums_content}")
print("Done.")
