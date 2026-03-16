import subprocess, os, sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("ERROR: set GITHUB_TOKEN env var first"); sys.exit(1)
PROXY = "http://127.0.0.1:4780"

env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY,
       "GIT_CONFIG_COUNT": "1",
       "GIT_CONFIG_KEY_0": "http.proxy",
       "GIT_CONFIG_VALUE_0": PROXY}

def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    print(f"$ {' '.join(cmd)}")
    if r.stdout: print(r.stdout.rstrip())
    if r.stderr: print(r.stderr.rstrip())
    if r.returncode != 0:
        raise SystemExit(f"FAILED rc={r.returncode}")
    return r

repos = {
    "api":  (r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\src\api",  "master",
             "https://github.com/hujiali30001/freecdn-api.git"),
    "node": (r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\src\node", "master",
             "https://github.com/hujiali30001/freecdn-node.git"),
}

for name, (cwd, branch, url) in repos.items():
    print(f"\n=== {name} ===")
    auth_url = url.replace("https://", f"https://{TOKEN}@")
    run(["git", "add", "internal/const/const.go"], cwd)
    run(["git", "commit", "-m", f"chore: bump version to v0.9.0"], cwd)
    run(["git", "push", auth_url, f"HEAD:{branch}"], cwd)

print("\nAll pushed OK")
