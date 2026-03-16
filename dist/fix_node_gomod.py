#!/usr/bin/env python3
"""修复 freecdn-node go.mod 的 EdgeCommon replace 版本"""
import json, http.client, base64, re, sys, os

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN", "")
NEW_TAG = "v1.3.10"
OLD_PSEUDO = "v1.3.10-0.20260316193426-45be148915e8"

def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "fix/1.0",
    }
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})

# Get freecdn-node go.mod
st, d = github_api("GET", "/repos/hujiali30001/freecdn-node/contents/go.mod")
content = base64.b64decode(d["content"]).decode()
sha = d["sha"]

print("Current replace lines:")
for line in content.splitlines():
    if "EdgeCommon" in line or "freecdn-common" in line:
        print(f"  {repr(line)}")

# Simple string replace
new_content = content.replace(OLD_PSEUDO, NEW_TAG)
if new_content == content:
    print("ERROR: could not find old pseudo-version")
    # Try different replacement
    new_content = re.sub(
        r'(github\.com/hujiali30001/EdgeCommon\s+)v[\d\.-]+',
        r'\g<1>' + NEW_TAG,
        content
    )
    if new_content == content:
        print("ERROR: replacement failed")
        sys.exit(1)

print(f"\nNew replace lines:")
for line in new_content.splitlines():
    if "EdgeCommon" in line or "freecdn-common" in line:
        print(f"  {repr(line)}")

body = {
    "message": f"chore: update freecdn-common replace to {NEW_TAG}",
    "content": base64.b64encode(new_content.encode()).decode(),
    "sha": sha,
    "branch": "master",
}
st, d = github_api("PUT", "/repos/hujiali30001/freecdn-node/contents/go.mod", body)
if st in (200, 201):
    print("[OK] freecdn-node/go.mod updated")
else:
    print(f"ERROR: {st} {d}")
