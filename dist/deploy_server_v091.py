import paramiko, os, stat

KEY = paramiko.RSAKey(filename=r"C:\Users\Administrator\.ssh\id_rsa_nopass")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("134.175.67.168", username="ubuntu", pkey=KEY, timeout=60)
print("connected")

build_base = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\amd64\freecdn-v0.9.1-linux-amd64"

def upload_and_move(sftp, local_path, tmp_path, final_path, mode=None):
    size_mb = os.path.getsize(local_path) / 1024 / 1024
    print(f"Uploading {os.path.basename(local_path)} ({size_mb:.1f} MB) ...")
    sftp.put(local_path, tmp_path)
    cmd = f"sudo mv {tmp_path} {final_path}"
    if mode:
        cmd += f" && sudo chmod {mode} {final_path}"
    _, out, err = c.exec_command(cmd)
    out.channel.recv_exit_status()
    e = err.read().decode()
    if e: print(f"  mv STDERR: {e}")
    else: print(f"  -> {final_path}")

sftp = c.open_sftp()

# 1. 上传新 edge-installer-helper
upload_and_move(sftp,
    os.path.join(build_base, "edge-api", "installers", "edge-installer-helper-linux-amd64"),
    "/home/ubuntu/edge-installer-helper-linux-amd64",
    "/usr/local/freecdn/edge-admin/edge-api/installers/edge-installer-helper-linux-amd64",
    mode="755"
)

# 2. 上传新 edge-api
upload_and_move(sftp,
    os.path.join(build_base, "edge-api", "bin", "edge-api"),
    "/home/ubuntu/edge-api-new",
    "/usr/local/freecdn/edge-admin/edge-api/bin/edge-api",
    mode="755"
)

# 3. 上传新 edge-node zip（新 zip 含正确目录结构）
upload_and_move(sftp,
    os.path.join(build_base, "edge-api", "deploy", "edge-node-linux-amd64-v0.9.1.zip"),
    "/home/ubuntu/edge-node-linux-amd64-v0.9.1.zip",
    "/usr/local/freecdn/edge-admin/edge-api/deploy/edge-node-linux-amd64-v0.9.1.zip",
    mode="644"
)

sftp.close()

# 4. 重启 freecdn-api
print("\nRestarting freecdn-api ...")
_, out, err = c.exec_command("sudo systemctl restart freecdn-api && sleep 2 && sudo systemctl status freecdn-api --no-pager | head -8")
print(out.read().decode())
e = err.read().decode()
if e: print("STDERR:", e)

# 5. 验证文件大小（确认更新成功）
print("\nVerifying:")
_, out, _ = c.exec_command("ls -la /usr/local/freecdn/edge-admin/edge-api/installers/ /usr/local/freecdn/edge-admin/edge-api/bin/edge-api /usr/local/freecdn/edge-admin/edge-api/deploy/")
print(out.read().decode())

c.close()
print("Done")
