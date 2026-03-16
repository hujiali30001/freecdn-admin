import paramiko, subprocess, sys, os, time

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "FreeCDN2026!"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, port=22, username=USER, password=PASS,
               timeout=15, look_for_keys=False, allow_agent=False)

print("=== Killing stuck wget processes ===")
_, out, _ = client.exec_command("sudo kill $(ps aux | grep 'wget.*freecdn' | grep -v grep | awk '{print $2}') 2>/dev/null; echo done")
print(out.read().decode())

print("=== Cleaning up partial download ===")
_, out, _ = client.exec_command("sudo rm -f /tmp/freecdn-pkg.tar.gz; echo cleaned")
print(out.read().decode())

# 用 sftp 直接上传本地已打好的包
LOCAL_PKG = r"c:\Users\Administrator\.workbuddy\FreeCDN\dist\build\freecdn-v0.1.0-linux-amd64.tar.gz"
REMOTE_TMP = "/tmp/freecdn-pkg.tar.gz"

size = os.path.getsize(LOCAL_PKG)
print(f"\n=== Uploading {LOCAL_PKG} ({size/1024/1024:.1f} MB) via SFTP ===")

sftp = client.open_sftp()
start = time.time()

def progress(transferred, total):
    pct = transferred * 100 // total
    elapsed = time.time() - start
    speed = transferred / elapsed / 1024 / 1024 if elapsed > 0 else 0
    print(f"\r  {pct}% ({transferred/1024/1024:.1f}/{total/1024/1024:.1f} MB) {speed:.1f} MB/s", end="", flush=True)

sftp.put(LOCAL_PKG, REMOTE_TMP, callback=progress)
sftp.close()
print(f"\nUpload done in {time.time()-start:.1f}s")

# 验证
_, out, _ = client.exec_command(f"ls -lh {REMOTE_TMP}")
print(out.read().decode())

client.close()
print("Ready to install!")
