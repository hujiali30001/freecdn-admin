#!/usr/bin/env python3
"""
FreeCDN 本地构建 & GitHub Release 上传脚本
用法:
  python scripts/local_build_release.py --token <GITHUB_TOKEN> [--version v0.1.0] [--goedge-version v1.3.9]
"""

import argparse
import hashlib
import os
import shutil
import subprocess
import sys
import urllib.request
import urllib.error
import zipfile
import tarfile
import json
import http.client
import urllib.parse
import pathlib

REPO = "hujiali30001/freecdn-admin"
# 按优先级排列：国内走 ghproxy 加速，最后兜底直连 + 原 goedge 源
GOEDGE_DOWNLOAD_URLS = [
    "https://ghfast.top/https://github.com/TeaOSLab/EdgeAdmin/releases/download/{goedge_ver}/edge-admin-linux-{arch}-plus-{goedge_ver}.zip",
    "https://mirror.ghproxy.com/https://github.com/TeaOSLab/EdgeAdmin/releases/download/{goedge_ver}/edge-admin-linux-{arch}-plus-{goedge_ver}.zip",
    "https://gh.llkk.cc/https://github.com/TeaOSLab/EdgeAdmin/releases/download/{goedge_ver}/edge-admin-linux-{arch}-plus-{goedge_ver}.zip",
    "https://github.com/TeaOSLab/EdgeAdmin/releases/download/{goedge_ver}/edge-admin-linux-{arch}-plus-{goedge_ver}.zip",
    "https://goedge.rip/dl/edge/{goedge_ver}/edge-admin-linux-{arch}-plus-{goedge_ver}.zip",
    "https://dl.goedge.cloud/edge/{goedge_ver}/edge-admin-linux-{arch}-plus-{goedge_ver}.zip",
]
ARCHS = ["amd64", "arm64"]


def log(msg):
    print(f"[build] {msg}", flush=True)


def download_file(url, dest):
    log(f"Downloading {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FreeCDN-Builder/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp, open(dest, "wb") as f:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 65536
            while True:
                data = resp.read(chunk)
                if not data:
                    break
                f.write(data)
                downloaded += len(data)
                if total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}% ({downloaded/1024/1024:.1f} MB)", end="", flush=True)
        print()
        log(f"Saved to {dest} ({os.path.getsize(dest)/1024/1024:.1f} MB)")
        return True
    except Exception as e:
        log(f"Failed: {e}")
        return False


def find_in_zip(zf, name):
    """在 zip 里找文件名匹配的第一个 entry，返回 ZipInfo 或 None"""
    for info in zf.infolist():
        if pathlib.Path(info.filename).name == name:
            return info
    return None


def build_package(work_dir, freecdn_ver, goedge_ver, arch, repo_root):
    log(f"=== Building {arch} ===")
    arch_dir = os.path.join(work_dir, arch)
    os.makedirs(arch_dir, exist_ok=True)

    # 1. 下载 GoEdge zip
    zip_path = os.path.join(arch_dir, f"goedge-{arch}.zip")
    if os.path.exists(zip_path) and os.path.getsize(zip_path) > 10_000_000:
        log(f"Reusing cached {zip_path}")
    else:
        ok = False
        for url_tpl in GOEDGE_DOWNLOAD_URLS:
            url = url_tpl.format(goedge_ver=goedge_ver, arch=arch)
            ok = download_file(url, zip_path)
            if ok:
                break
        if not ok:
            log(f"ERROR: Failed to download GoEdge {goedge_ver} {arch}")
            return None

    # 2. 解压
    extract_dir = os.path.join(arch_dir, "goedge-src")
    if os.path.exists(extract_dir):
        shutil.rmtree(extract_dir)
    os.makedirs(extract_dir)
    log(f"Extracting {zip_path}")
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    # 找 edge-admin 目录（兼容有无顶层目录）
    goedge_dir = extract_dir
    entries = os.listdir(extract_dir)
    if len(entries) == 1 and os.path.isdir(os.path.join(extract_dir, entries[0])):
        goedge_dir = os.path.join(extract_dir, entries[0])
    log(f"GoEdge dir: {goedge_dir}")
    log(f"Contents: {os.listdir(goedge_dir)}")

    # 3. 组装包目录
    pkg_name = f"freecdn-{freecdn_ver}-linux-{arch}"
    pkg_dir = os.path.join(arch_dir, pkg_name)
    if os.path.exists(pkg_dir):
        shutil.rmtree(pkg_dir)
    os.makedirs(pkg_dir)

    def copy_if_exists(src, dst):
        if os.path.exists(src):
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            return True
        log(f"  WARN: {src} not found, skipping")
        return False

    # edge-admin 二进制
    copy_if_exists(os.path.join(goedge_dir, "bin", "edge-admin"), os.path.join(pkg_dir, "edge-admin"))
    # web 资源：先铺 GoEdge 原版，再用仓库里改过的文件覆盖（品牌替换 + 去收费模块）
    copy_if_exists(os.path.join(goedge_dir, "web"), os.path.join(pkg_dir, "web"))
    repo_web = os.path.join(repo_root, "web")
    if os.path.isdir(repo_web):
        log(f"Overlaying repo web/ onto GoEdge web/ ...")
        for root, dirs, files in os.walk(repo_web):
            rel = os.path.relpath(root, repo_web)
            dst_dir = os.path.join(pkg_dir, "web") if rel == "." else os.path.join(pkg_dir, "web", rel)
            os.makedirs(dst_dir, exist_ok=True)
            for fname in files:
                shutil.copy2(os.path.join(root, fname), os.path.join(dst_dir, fname))
        log("Overlay done.")
    else:
        log("WARN: repo web/ not found, using GoEdge original web/ (commercial modules NOT removed!)")
    # edge-api 二进制
    os.makedirs(os.path.join(pkg_dir, "edge-api", "bin"), exist_ok=True)
    edge_api_src = os.path.join(goedge_dir, "edge-api", "bin", "edge-api")
    copy_if_exists(edge_api_src, os.path.join(pkg_dir, "edge-api", "bin", "edge-api"))
    # edge-node 安装包
    os.makedirs(os.path.join(pkg_dir, "edge-api", "deploy"), exist_ok=True)
    deploy_src = os.path.join(goedge_dir, "edge-api", "deploy")
    if os.path.isdir(deploy_src):
        for f in os.listdir(deploy_src):
            if f.startswith(f"edge-node-linux-{arch}-") and f.endswith(".zip"):
                shutil.copy2(os.path.join(deploy_src, f), os.path.join(pkg_dir, "edge-api", "deploy", f))
                log(f"  Copied edge-node package: {f}")

    # FreeCDN 自定义文件
    for fname in ["install.sh", "install-node.sh", "README.md", "NOTICE", "LICENSE"]:
        src = os.path.join(repo_root, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(pkg_dir, fname))
    docs_src = os.path.join(repo_root, "docs")
    if os.path.isdir(docs_src):
        shutil.copytree(docs_src, os.path.join(pkg_dir, "docs"))

    # VERSION 文件
    with open(os.path.join(pkg_dir, "VERSION"), "w") as f:
        import datetime
        f.write(f"FreeCDN {freecdn_ver} (based on GoEdge {goedge_ver})\n")
        f.write(f"Build date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

    # 4. 打 tar.gz
    archive_name = f"{pkg_name}.tar.gz"
    archive_path = os.path.join(work_dir, archive_name)
    log(f"Creating {archive_path}")
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(pkg_dir, arcname=pkg_name)
    size_mb = os.path.getsize(archive_path) / 1024 / 1024
    log(f"Done: {archive_name} ({size_mb:.1f} MB)")
    return archive_path


def sha256sum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            data = f.read(65536)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def github_api(token, method, path, body=None, headers=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-Builder/1.0",
    }
    if headers:
        h.update(headers)
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, json.loads(data) if data else {}


def upload_asset(token, upload_url, file_path):
    """upload_url like https://uploads.github.com/repos/.../releases/123/assets{?name,label}"""
    # 去掉 {?name,label} 模板
    base_url = upload_url.split("{")[0]
    fname = os.path.basename(file_path)
    url = f"{base_url}?name={urllib.parse.quote(fname)}"
    log(f"Uploading {fname} ({os.path.getsize(file_path)/1024/1024:.1f} MB) → {url}")

    parsed = urllib.parse.urlparse(url)
    conn = http.client.HTTPSConnection(parsed.netloc)
    with open(file_path, "rb") as f:
        data = f.read()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/octet-stream",
        "Content-Length": str(len(data)),
        "User-Agent": "FreeCDN-Builder/1.0",
    }
    conn.request("POST", parsed.path + "?" + parsed.query, body=data, headers=headers)
    resp = conn.getresponse()
    resp_data = json.loads(resp.read())
    if resp.status in (200, 201):
        log(f"  Uploaded: {resp_data.get('browser_download_url', 'ok')}")
    else:
        log(f"  ERROR {resp.status}: {resp_data}")
    return resp.status in (200, 201)


def get_or_create_release(token, version):
    """获取已有 Release 或创建新的"""
    # 先查
    status, data = github_api(token, "GET", f"/repos/{REPO}/releases/tags/{version}")
    if status == 200:
        log(f"Found existing release: {data['id']} - {data['name']}")
        return data

    # 创建
    log(f"Creating release {version}")
    body = {
        "tag_name": version,
        "name": f"FreeCDN {version}",
        "body": f"## FreeCDN {version}\n\n基于 **GoEdge v1.3.9**（安全基线版本）打包。\n\n> ⚠️ 注意：FreeCDN 锁定使用 GoEdge v1.3.9，不跟踪 v1.4.x 及以上版本（v1.4.0/v1.4.1 存在恶意代码注入安全事件）。\n\n### 快速安装\n\n```bash\ncurl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash\n```",
        "draft": False,
        "prerelease": False,
    }
    status, data = github_api(token, "POST", f"/repos/{REPO}/releases", body)
    if status == 201:
        log(f"Created release: {data['id']}")
        return data
    log(f"ERROR creating release: {status} {data}")
    return None


def main():
    parser = argparse.ArgumentParser(description="FreeCDN local build & upload to GitHub Release")
    parser.add_argument("--token", required=True, help="GitHub personal access token (contents:write)")
    parser.add_argument("--version", default="v0.1.1", help="FreeCDN version tag")
    parser.add_argument("--goedge-version", default="v1.3.9", help="GoEdge version to package")
    parser.add_argument("--arch", default="all", help="amd64, arm64, or all")
    parser.add_argument("--work-dir", default=None, help="Work directory for downloads/build")
    args = parser.parse_args()

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    work_dir = args.work_dir or os.path.join(repo_root, "dist", "build")
    os.makedirs(work_dir, exist_ok=True)

    archs = ARCHS if args.arch == "all" else [args.arch]

    # 构建各架构包
    archives = []
    for arch in archs:
        path = build_package(work_dir, args.version, args.goedge_version, arch, repo_root)
        if path:
            archives.append(path)
        else:
            log(f"Build failed for {arch}")
            sys.exit(1)

    # 生成 SHA256SUMS
    checksum_path = os.path.join(work_dir, "SHA256SUMS")
    with open(checksum_path, "w") as f:
        for p in archives:
            digest = sha256sum(p)
            f.write(f"{digest}  {os.path.basename(p)}\n")
            log(f"SHA256 {os.path.basename(p)}: {digest}")
    archives.append(checksum_path)

    # 获取/创建 Release
    release = get_or_create_release(args.token, args.version)
    if not release:
        sys.exit(1)

    upload_url = release["upload_url"]

    # 删除同名已有 assets（避免重复上传报错）
    existing_assets = {a["name"]: a["id"] for a in release.get("assets", [])}
    for p in archives:
        fname = os.path.basename(p)
        if fname in existing_assets:
            log(f"Deleting existing asset: {fname}")
            github_api(args.token, "DELETE", f"/repos/{REPO}/releases/assets/{existing_assets[fname]}")

    # 上传
    for p in archives:
        ok = upload_asset(args.token, upload_url, p)
        if not ok:
            log(f"Upload failed for {p}")
            sys.exit(1)

    log("=== All done! ===")
    log(f"Release URL: {release.get('html_url', 'https://github.com/' + REPO + '/releases/tag/' + args.version)}")


if __name__ == "__main__":
    main()
