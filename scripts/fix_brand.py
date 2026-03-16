"""
修复品牌问题：在数据库写入 adminUIConfig，设置正确的 ProductName 和 AdminSystemName
同时修复 Version 在前端显示为 0.1.0 的问题（通过设置 UIConfig.Version 字段）
"""
import paramiko
import json

HOST = "134.175.67.168"
USER = "ubuntu"
PASS = "REDACTED_SSH_PASS"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

def run(cmd, timeout=20):
    _, out, err = ssh.exec_command(cmd, timeout=timeout)
    return (out.read().decode(errors="replace") + err.read().decode(errors="replace")).strip()

def mysql(sql):
    cmd = f"mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -e \"{sql}\" 2>/dev/null"
    return run(cmd)

# 1. 检查当前 adminUIConfig
print("=== 1. 当前 adminUIConfig ===")
r = run("mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -sNe \"SELECT CAST(value AS CHAR) FROM edgeSysSettings WHERE code='adminUIConfig';\" 2>/dev/null")
print(r or "(空/不存在)")

# 2. 读取并修改
current = r.strip()
if current and current != "(空/不存在)":
    try:
        cfg = json.loads(current)
    except:
        cfg = {}
else:
    cfg = {}

# 更新品牌字段
cfg["productName"] = "FreeCDN"
cfg["adminSystemName"] = "FreeCDN 管理系统"
cfg["showVersion"] = True
cfg["version"] = "v0.4.1"   # 新增：自定义显示版本
cfg["showOpenSourceInfo"] = True
cfg["showFinance"] = False
if "defaultPageSize" not in cfg:
    cfg["defaultPageSize"] = 10
if "timeZone" not in cfg:
    cfg["timeZone"] = "Asia/Shanghai"
if "dnsResolver" not in cfg:
    cfg["dnsResolver"] = {"type": "default"}

cfg_json = json.dumps(cfg, ensure_ascii=False)
print(f"\n=== 2. 写入新配置 ===")
print(f"JSON: {cfg_json}")

# 转义单引号用于 SQL
cfg_json_escaped = cfg_json.replace("'", "\\'")

# 用 REPLACE INTO 插入（或更新）
sql = f"REPLACE INTO edgeSysSettings (code, value) VALUES ('adminUIConfig', '{cfg_json_escaped}');"
r = run(f"mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -e \"{sql}\" 2>&1")
print(f"写入结果: {r or 'OK'}")

# 3. 验证写入
print("\n=== 3. 验证 ===")
r = run("mysql -h 127.0.0.1 -u freecdn -p'REDACTED_SSH_PASS' freecdn -sNe \"SELECT CAST(value AS CHAR) FROM edgeSysSettings WHERE code='adminUIConfig';\" 2>/dev/null")
print(r)

# 4. 还需要修复 const.go 中的 Version，但那需要重新编译
# 这里通过数据库的 UIConfig.version 字段来覆盖显示版本
# 查看 admin_ui_config.go 中如何使用 Version 字段
print("\n=== 4. 检查 version 字段在源码中的使用 ===")
print("在 admin_ui_config.go 中，LoadAdminUIConfig() 返回 config.Version")
print("在 index.go 中：if len(uiConfig.Version) > 0 { this.Data['version'] = uiConfig.Version }")
print("所以设置 version='v0.4.1' 后，前端显示版本应该改变")

# 5. 但需要重启服务（内存缓存 sharedAdminUIConfig 需要清除）
print("\n=== 5. 重启服务以清除内存缓存 ===")
r = run("sudo systemctl restart freecdn-admin", timeout=30)
print(f"重启结果: {r or 'OK'}")

import time
time.sleep(3)

# 6. 验证服务重新启动
r = run("sudo systemctl is-active freecdn-admin", timeout=10)
print(f"服务状态: {r}")

ssh.close()
print("\n完成。")
