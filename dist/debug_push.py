import subprocess, os, sys, traceback

TOKEN = os.environ.get("GITHUB_TOKEN", "")
if not TOKEN:
    print("ERROR: set GITHUB_TOKEN env var first"); sys.exit(1)
PROXY = "http://127.0.0.1:4780"
CWD = r"C:\Users\Administrator\.workbuddy\FreeCDN"

env = {**os.environ, "HTTP_PROXY": PROXY, "HTTPS_PROXY": PROXY}

try:
    # 第一步：git add
    print("Step 1: git add PLAN.md ...", flush=True)
    r = subprocess.run(
        ["git", "add", "PLAN.md"],
        cwd=CWD, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    print("rc:", r.returncode, flush=True)
    print(r.stdout.decode("utf-8", errors="replace"), flush=True)

    # 第二步：git commit
    print("Step 2: git commit ...", flush=True)
    r = subprocess.run(
        ["git", "commit", "-F", "commit_msg.txt"],
        cwd=CWD, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    print("rc:", r.returncode, flush=True)
    print(r.stdout.decode("utf-8", errors="replace"), flush=True)

    # 第三步：git push
    print("Step 3: git push ...", flush=True)
    r = subprocess.run(
        ["git", "push",
         f"https://{TOKEN}@github.com/hujiali30001/freecdn-admin.git",
         "HEAD:main"],
        cwd=CWD, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    print("rc:", r.returncode, flush=True)
    print(r.stdout.decode("utf-8", errors="replace"), flush=True)

except Exception as e:
    traceback.print_exc()
    print("Exception:", e)
