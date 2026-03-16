import paramiko, re
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('134.175.67.168', username='ubuntu', password='FreeCDN2026!', timeout=30)
def run(c, t=20):
    _, o, e = ssh.exec_command(c, timeout=t)
    return (o.read().decode(errors="replace") + e.read().decode(errors="replace")).strip()
def mysql(s):
    return run(f"mysql -h 127.0.0.1 -u freecdn -p'FreeCDN2026!' freecdn -sNe \"{s}\" 2>/dev/null").strip()

# 查表结构
print("=== edgeDNSDomains 表结构 ===")
print(mysql("DESCRIBE edgeDNSDomains;"))
print()

# 查 INSERT 失败原因
print("=== 尝试插入（verbose）===")
r = run("mysql -h 127.0.0.1 -u freecdn -p'FreeCDN2026!' freecdn -e \"INSERT INTO edgeDNSDomains (name, state, createdAt, updatedAt, uniqueId, adminId, userId, clusterId, providerId) VALUES ('test.example.com', 1, UNIX_TIMESTAMP(), UNIX_TIMESTAMP(), 'testdns001', 1, 0, 1, 0);\" 2>&1")
print(r)
print()

# 检查是否插入成功
print("=== 查询 ===")
print(mysql("SELECT id, name FROM edgeDNSDomains;"))

ssh.close()
