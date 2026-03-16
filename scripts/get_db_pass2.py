import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("134.175.67.168", username="ubuntu", password="FreeCDN2026!", timeout=15)

_, stdout, _ = ssh.exec_command("sudo cat /usr/local/freecdn/edge-admin/edge-api/configs/db.yaml 2>&1")
db_yaml = stdout.read().decode()
print("db.yaml:", db_yaml)

ssh.close()
