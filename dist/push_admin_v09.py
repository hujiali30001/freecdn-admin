import subprocess, os, sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("ERROR: set GITHUB_TOKEN env var first"); sys.exit(1)
PROXY = "http://127.0.0.1:4780"
CWD = r"C:\Users\Administrator\.workbuddy\FreeCDN"

env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY,
       "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "http.proxy",
       "GIT_CONFIG_VALUE_0": PROXY}

def run(cmd):
    r = subprocess.run(cmd, cwd=CWD, capture_output=True, text=True, env=env)
    print(f"$ {' '.join(cmd)}")
    if r.stdout: print(r.stdout.rstrip())
    if r.stderr: print(r.stderr.rstrip())
    if r.returncode != 0:
        raise SystemExit(f"FAILED rc={r.returncode}")

run(["git", "add",
     "cmd/freecdn-init/main.go",
     "internal/initdb/initdb.go",
     "internal/const/const.go",
     "install.sh",
     "scripts/local_build_release.py",
])
run(["git", "commit", "-F", "commit_msg.txt"])
run(["git", "push",
     f"https://{TOKEN}@github.com/hujiali30001/freecdn-admin.git",
     "HEAD:main"])
print("Done!")
