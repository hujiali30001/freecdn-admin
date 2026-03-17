#!/usr/bin/env python3
"""
只重新打包 edge-node zip（不重新编译），修复 create_system=3 问题，
然后推到服务器的 edge-api/deploy/ 目录并替换 Release。
"""
import sys, os, io, zipfile, stat as stat_mod

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BUILD_BASE = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\build\amd64\freecdn-v0.9.1-linux-amd64"
DEPLOY_DIR = os.path.join(BUILD_BASE, "edge-api", "deploy")
ZIP_NAME = "edge-node-linux-amd64-v0.9.1.zip"
ZIP_PATH = os.path.join(DEPLOY_DIR, ZIP_NAME)

# 也找 node 仓库里的 configs
NODE_REPO_DIR = r"C:\Users\Administrator\.workbuddy\FreeCDN\dist\src\node"

# 从旧 zip 里提取 edge-node 二进制（在内存中）
print("Extracting edge-node binary from existing zip...")
with zipfile.ZipFile(ZIP_PATH) as old_z:
    node_bin_data = old_z.read("edge-node/bin/edge-node")
print(f"Node binary: {len(node_bin_data)/1024/1024:.1f} MB (from zip)")

def _dir_info(arcname):
    info = zipfile.ZipInfo(arcname + "/")
    info.create_system = 3          # Unix
    info.external_attr = (stat_mod.S_IFDIR | 0o755) << 16
    info.compress_type = zipfile.ZIP_STORED
    return info

def _file_info(arcname, mode=0o755):
    info = zipfile.ZipInfo(arcname)
    info.create_system = 3          # Unix
    info.external_attr = (stat_mod.S_IFREG | mode) << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info

print(f"Node binary: {len(node_bin_data)/1024/1024:.1f} MB (from zip)")
print(f"Output zip:  {ZIP_PATH}")

os.makedirs(DEPLOY_DIR, exist_ok=True)

with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
    # 目录条目（create_system=3 = Unix，确保 Go 正确解析权限）
    for d in ["edge-node", "edge-node/bin", "edge-node/configs"]:
        zf.writestr(_dir_info(d), "")
    
    # 二进制（0755 可执行）
    print("Adding edge-node binary...")
    zf.writestr(_file_info("edge-node/bin/edge-node", mode=0o755), node_bin_data)
    
    # configs
    conf_src = os.path.join(NODE_REPO_DIR, "configs")
    if os.path.isdir(conf_src):
        for root, dirs, files in os.walk(conf_src):
            for fname in files:
                fpath = os.path.join(root, fname)
                rel = "edge-node/configs/" + os.path.relpath(fpath, conf_src).replace("\\", "/")
                with open(fpath, "rb") as f:
                    zf.writestr(_file_info(rel, mode=0o644), f.read())
                print(f"  Added {rel}")
    else:
        zf.writestr(_file_info("edge-node/configs/api_node.yaml", mode=0o644), "")
        print("  Added configs/api_node.yaml (placeholder)")

size_mb = os.path.getsize(ZIP_PATH) / 1024 / 1024
print(f"\nZip created: {size_mb:.1f} MB")

# 验证
print("\n=== 验证 zip 内容 ===")
with zipfile.ZipFile(ZIP_PATH) as z:
    for info in z.infolist():
        mode = (info.external_attr >> 16) & 0xFFFF
        cs = info.create_system
        print(f"  {info.filename:45} create_system={cs} mode=0o{mode:06o}")

print("\nDone. 现在运行 deploy 脚本推到服务器。")
