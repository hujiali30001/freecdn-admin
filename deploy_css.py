#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess
import sys

# 使用 Python 处理文件复制，避免 cmd 和 bash 的 @ 符号问题
src = r"C:\Users\Administrator\.workbuddy\FreeCDN\web\views\@default\@layout.css"
wsl_src = "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/@layout.css"
wsl_dst = "/usr/local/freecdn/edge-admin/web/views/@default/@layout.css"

# 方法1：直接读 Windows 文件，通过 wsl tee 写入
print("[+] 读取编译好的 CSS 文件...")
try:
    with open(src, 'rb') as f:
        css_content = f.read()
    print(f"    读取成功 ({len(css_content)} bytes)")
except Exception as e:
    print(f"    [ERROR] 读取失败: {e}")
    sys.exit(1)

# 通过 wsl 的 bash -c 创建临时文件
print("[+] 通过 WSL 部署文件...")
cmd = [
    'wsl', '-d', 'Ubuntu-24.04', '-u', 'root', 
    'bash', '-c', f'cat > {wsl_dst} && chmod 644 {wsl_dst} && echo "deployed"'
]

try:
    result = subprocess.run(cmd, input=css_content, capture_output=True, timeout=30)
    if result.returncode == 0:
        print(f"    部署成功！")
        print(f"    输出: {result.stdout.decode('utf-8', errors='replace').strip()}")
    else:
        print(f"    [ERROR] 部署失败 (exit {result.returncode})")
        print(f"    stdout: {result.stdout.decode('utf-8', errors='replace')}")
        print(f"    stderr: {result.stderr.decode('utf-8', errors='replace')}")
        sys.exit(1)
except Exception as e:
    print(f"    [ERROR] 执行失败: {e}")
    sys.exit(1)

print("\n[+] 验证部署结果...")
verify_cmd = [
    'wsl', '-d', 'Ubuntu-24.04', '-u', 'root',
    'bash', '-c', f'ls -la {wsl_dst} && head -3 {wsl_dst}'
]

try:
    result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)
    print(result.stdout)
    if result.returncode != 0:
        print(f"警告: {result.stderr}")
except Exception as e:
    print(f"验证失败: {e}")

print("\n[✓] CSS 文件部署完成！")
print("    刷新浏览器即可查看最新样式")
