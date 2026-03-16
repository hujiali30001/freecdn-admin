"""更新三主仓库 const.go 版本号到 0.8.0"""
import json, http.client, base64, re, sys, os

TOKEN = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("GITHUB_TOKEN", "")
NEW_VERSION = "0.8.0"

REPOS = [
    ("hujiali30001", "freecdn-api",  "internal/const/const.go"),
    ("hujiali30001", "freecdn-node", "internal/const/const.go"),
]

def gh_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    headers = {
        "Authorization": f"token {TOKEN}",
        "User-Agent": "freecdn-build",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github.v3+json",
    }
    data = json.dumps(body).encode() if body else None
    conn.request(method, path, body=data, headers=headers)
    resp = conn.getresponse()
    raw = resp.read()
    return resp.status, json.loads(raw)

for owner, repo, file_path in REPOS:
    print(f"\n=== {repo}/{file_path} ===")
    status, data = gh_api("GET", f"/repos/{owner}/{repo}/contents/{file_path}")
    if status != 200:
        print(f"  ERROR: GET failed {status}: {data}")
        continue
    sha = data["sha"]
    content = base64.b64decode(data["content"]).decode("utf-8")
    
    new_content = re.sub(
        r'Version\s*=\s*"[0-9.]+"',
        f'Version = "{NEW_VERSION}"',
        content
    )
    if new_content == content:
        print(f"  SKIP: already at {NEW_VERSION}")
        continue
    
    encoded = base64.b64encode(new_content.encode()).decode()
    status2, data2 = gh_api("PUT", f"/repos/{owner}/{repo}/contents/{file_path}", {
        "message": f"chore: bump version to {NEW_VERSION} (v0.8.0 C-3 health endpoint)",
        "content": encoded,
        "sha": sha,
    })
    if status2 in (200, 201):
        print(f"  OK: updated to {NEW_VERSION}")
    else:
        print(f"  ERROR: PUT failed {status2}: {data2}")
