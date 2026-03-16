import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("134.175.67.168", username="ubuntu", password="FreeCDN2026!", timeout=15)

# 读取 db.yaml 获取实际 MySQL 密码
_, stdout, _ = ssh.exec_command("cat /usr/local/freecdn/admin/configs/db.yaml 2>/dev/null || echo 'NOT FOUND'")
print("db.yaml:", stdout.read().decode())

# 也试试 /etc/freecdn
_, stdout2, _ = ssh.exec_command("find /usr/local/freecdn -name '*.yaml' -o -name '*.conf' 2>/dev/null | head -10")
print("config files:", stdout2.read().decode())

ssh.close()
