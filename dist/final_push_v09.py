import subprocess, os, sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN and len(sys.argv) > 1:
    TOKEN = sys.argv[1]
if not TOKEN:
    print("ERROR: need GITHUB_TOKEN"); sys.exit(1)

PROXY = "http://127.0.0.1:4780"
CWD = r"C:\Users\Administrator\.workbuddy\FreeCDN"
env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY}

def run(cmd, allow_fail=False):
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    r = subprocess.run(cmd, cwd=CWD, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(r.stdout.decode("utf-8", errors="replace").rstrip(), flush=True)
    if r.returncode != 0 and not allow_fail:
        raise SystemExit(f"FAILED rc={r.returncode}")
    return r

# Stage 所有需要的文件（token 已改为环境变量）
run(["git", "add",
     "PLAN.md",
     "dist/build_check.py",
     "dist/check_exists.py",
     "dist/find_go.py",
     "dist/launch_build_v09.py",
     "dist/push_admin_v09.py",
     "dist/push_plan_v09.py",
     "dist/push_version_v09.py",
     "dist/debug_push.py",
     "dist/fix_tokens.py",
])

# Commit
run(["git", "commit", "-m",
     "docs+chore: PLAN.md v0.9.0; dist scripts use GITHUB_TOKEN env var (no hardcoded token)"])

# Force push (overwrite the 2 commits that had tokens)
run(["git", "push", "--force-with-lease",
     f"https://{TOKEN}@github.com/hujiali30001/freecdn-admin.git",
     "HEAD:main"])

print("\nAll done!")
