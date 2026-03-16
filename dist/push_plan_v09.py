import subprocess, os, sys

# Token 从环境变量 GITHUB_TOKEN 读取，不硬编码
TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("ERROR: set GITHUB_TOKEN env var first")
    sys.exit(1)

PROXY = "http://127.0.0.1:4780"
CWD = r"C:\Users\Administrator\.workbuddy\FreeCDN"

env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY}

def run(cmd):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=CWD, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", errors="replace").rstrip(), flush=True)
    print(f"rc={r.returncode}", flush=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED")

run(["git", "add",
     "dist/push_version_v09.py", "dist/push_admin_v09.py",
     "dist/launch_build_v09.py", "dist/push_plan_v09.py",
     "dist/debug_push.py"])
run(["git", "commit", "-m", "chore: remove hardcoded token from dist scripts, use GITHUB_TOKEN env var"])
run(["git", "push",
     f"https://{TOKEN}@github.com/hujiali30001/freecdn-admin.git",
     "HEAD:main"])
print("Done!")
