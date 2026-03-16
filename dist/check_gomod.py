#!/usr/bin/env python3
"""检查各仓库 go.mod 当前状态"""
import urllib.request, json, base64, os

TOKEN = os.environ.get("GITHUB_TOKEN", "")  # set via env: GITHUB_TOKEN=ghp_...
PROXY = "http://127.0.0.1:4780"

REPOS = [
    ("hujiali30001/freecdn-api",   "go.mod"),
    ("hujiali30001/freecdn-node",  "go.mod"),
    ("hujiali30001/EdgeCommon",    "go.mod"),
]

opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"https": PROXY, "http": PROXY})
)

for repo, path in REPOS:
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "check-gomod/1.0",
    })
    try:
        r = opener.open(req)
        d = json.loads(r.read())
        content = base64.b64decode(d["content"]).decode()
        print(f"\n=== {repo}/{path} ===")
        for line in content.splitlines():
            if any(x in line for x in ["module ", "replace", "EdgeCommon", "freecdn", "TeaOS", "hujiali"]):
                print(f"  {line}")
    except Exception as e:
        print(f"ERROR {repo}: {e}")
