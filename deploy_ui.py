#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部署 UI CSS 文件到 WSL 服务器
"""
import os
import subprocess
import sys
import shutil
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def run_cmd(cmd, shell=True):
    """执行命令"""
    print(f"[执行] {cmd}")
    result = subprocess.run(cmd, shell=shell, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[错误] {result.stderr}")
        return False
    if result.stdout:
        print(f"[输出] {result.stdout.strip()}")
    return True

def deploy_css():
    """部署 CSS 文件"""
    print("=" * 60)
    print("FreeCDN UI CSS 部署脚本")
    print("=" * 60)
    
    # 源文件
    files_to_deploy = [
        ("web/views/@default/@layout.css", "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/@layout.css", "/usr/local/freecdn/edge-admin/web/views/@default/@layout.css"),
        ("web/views/@default/@left_menu.css", "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/@left_menu.css", "/usr/local/freecdn/edge-admin/web/views/@default/@left_menu.css"),
        ("web/views/@default/index/index.css", "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/index/index.css", "/usr/local/freecdn/edge-admin/web/views/@default/index/index.css"),
        ("web/views/@default/dashboard/index.css", "/mnt/c/Users/Administrator/.workbuddy/FreeCDN/web/views/@default/dashboard/index.css", "/usr/local/freecdn/edge-admin/web/views/@default/dashboard/index.css"),
    ]
    
    print("\n[步骤 1] 检查源文件存在性...")
    for name, src, _ in files_to_deploy:
        if os.path.exists(src):
            size = os.path.getsize(src)
            print(f"  ✓ {name} ({size} bytes)")
        else:
            print(f"  ✗ {name} 不存在")
            return False
    
    print("\n[步骤 2] 部署文件到 WSL 服务器...")
    for name, src, dest in files_to_deploy:
        cmd = f'wsl -d Ubuntu-24.04 -u root cp "{src}" "{dest}"'
        if not run_cmd(cmd):
            return False
        print(f"  ✓ {name} 已部署")
    
    print("\n[步骤 3] 验证部署文件...")
    for name, _, dest in files_to_deploy:
        cmd = f'wsl -d Ubuntu-24.04 -u root ls -lh "{dest}"'
        if run_cmd(cmd):
            print(f"  ✓ {name} 验证成功")
        else:
            return False
    
    print("\n[步骤 4] 获取服务状态...")
    cmd = 'wsl -d Ubuntu-24.04 -u root pgrep -l edge-admin'
    run_cmd(cmd)
    
    print("\n[步骤 5] 清空浏览器缓存提示...")
    print("  ⚠  CSS 文件已部署到服务器")
    print("  ⚠  请手动清空浏览器缓存或打开无痕窗口刷新查看效果")
    print("  ⚠  管理后台地址：http://172.24.213.247:7788")
    
    print("\n" + "=" * 60)
    print("✓ 部署完成！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    if not deploy_css():
        sys.exit(1)
