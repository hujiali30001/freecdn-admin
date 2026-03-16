"""
诊断 MySQL 配置
"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("134.175.67.168", username="ubuntu", password="FreeCDN2026!", timeout=15)

# 找到所有配置文件
_, out, _ = ssh.exec_command("find /usr/local/freecdn /opt/freecdn /root/freecdn -name 'db.yaml' -o -name '.env' 2>/dev/null | head -20")
print("config files:\n", out.read().decode())

# 列出 /usr/local/freecdn 结构
_, out2, _ = ssh.exec_command("find /usr/local/freecdn -maxdepth 4 2>/dev/null | head -30")
print("freecdn dir:\n", out2.read().decode())

# 读取 db.yaml
_, out3, _ = ssh.exec_command("cat /usr/local/freecdn/admin/configs/db.yaml 2>/dev/null || echo 'NOT_FOUND'")
print("admin db.yaml:\n", out3.read().decode())

# 列出 deploy 目录下的 .env
_, out4, _ = ssh.exec_command("ls /opt/freecdn/ 2>/dev/null; ls /root/freecdn/ 2>/dev/null || echo 'not root'; cat /opt/freecdn/deploy/.env 2>/dev/null || echo 'no opt env'")
print("env:\n", out4.read().decode())

ssh.close()
