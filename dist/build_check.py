import subprocess, os, sys, shutil

env = {**os.environ, "HTTP_PROXY": "http://127.0.0.1:4780", "HTTPS_PROXY": "http://127.0.0.1:4780"}
cwd = r"C:\Users\Administrator\.workbuddy\FreeCDN"

import shutil
go_exe = r"C:\Go_temp\go\bin\go.exe"
print("go:", go_exe)

r = subprocess.run(
    [go_exe, "build", "./cmd/freecdn-init/"],
    cwd=cwd, capture_output=True, text=True, env=env
)
print("STDOUT:", r.stdout)
print("STDERR:", r.stderr)
print("RC:", r.returncode)
