#!/usr/bin/env python3
"""
FreeCDN 本地构建 & GitHub Release 上传脚本
从自有仓库编译全部三个组件（freecdn-admin / freecdn-api / freecdn-node），不依赖 GoEdge Release 包。

用法:
  python scripts/local_build_release.py --token <GITHUB_TOKEN> [--version v0.1.5] [--arch amd64|arm64|all]

依赖:
  - Go 1.22+  (脚本自动在 PATH 或 C:\\Go_temp\\go\\bin 中查找)
  - Git
  - Python 3.8+
"""

import argparse
import datetime
import hashlib
import http.client
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.parse
import urllib.request

# ── 仓库配置 ──────────────────────────────────────────────────────────────────
RELEASE_REPO   = "hujiali30001/freecdn-admin"   # Release 发布到这里
REPOS = {
    "admin": ("https://github.com/hujiali30001/freecdn-admin.git", "main"),
    "api":   ("https://github.com/hujiali30001/freecdn-api.git",   "master"),
    "node":  ("https://github.com/hujiali30001/freecdn-node.git",  "master"),
}
ARCHS = ["amd64", "arm64"]

# Go 二进制查找路径（Windows 备用）
GO_FALLBACK_PATHS = [
    r"C:\Go_temp\go\bin\go.exe",
    r"C:\Go\bin\go.exe",
    r"C:\Program Files\Go\bin\go.exe",
]

# WSL 配置（用于需要 CGO 的 edge-node 编译）
WSL_GO   = "/usr/local/go/bin/go"
WSL_DISTRO = "Ubuntu-24.04"

def wsl_path(win_path):
    """把 Windows 路径转成 WSL 可访问的 /mnt/... 路径"""
    p = win_path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        drive = p[0].lower()
        p = f"/mnt/{drive}{p[2:]}"
    return p


# ── 工具函数 ──────────────────────────────────────────────────────────────────
def log(msg):
    print(f"[build] {msg}", flush=True)


def find_go():
    """找到可用的 go 可执行文件路径"""
    # 先试 PATH
    go = shutil.which("go")
    if go:
        return go
    for p in GO_FALLBACK_PATHS:
        if os.path.isfile(p):
            return p
    return None


PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://127.0.0.1:4780"

def _base_env():
    """返回带代理的基础环境变量"""
    e = os.environ.copy()
    e.setdefault("HTTP_PROXY",  PROXY)
    e.setdefault("HTTPS_PROXY", PROXY)
    # 让 git 也走代理
    e["GIT_CONFIG_COUNT"] = "1"
    e["GIT_CONFIG_KEY_0"]   = "http.proxy"
    e["GIT_CONFIG_VALUE_0"] = PROXY
    return e


def run(cmd, cwd=None, env=None, check=True, retries=3):
    import time
    log(f"$ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    # 默认继承带代理的环境
    if env is None:
        env = _base_env()
    for attempt in range(1, retries + 1):
        result = subprocess.run(cmd, cwd=cwd, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True)
        if result.stdout:
            for line in result.stdout.splitlines():
                print(f"  {line}")
        if result.returncode == 0:
            return result
        if check:
            if attempt < retries:
                log(f"  command failed (exit {result.returncode}), retrying in 5s... ({attempt}/{retries})")
                time.sleep(5)
            else:
                log(f"ERROR: command failed after {retries} attempts (exit {result.returncode})")
                sys.exit(1)
        else:
            return result
    return result


def sha256sum(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def copy_tree_overlay(src, dst):
    """把 src 目录内容覆盖合并到 dst（已有文件直接覆盖）"""
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        dst_dir = dst if rel == "." else os.path.join(dst, rel)
        os.makedirs(dst_dir, exist_ok=True)
        for fname in files:
            shutil.copy2(os.path.join(root, fname), os.path.join(dst_dir, fname))


# ── clone / 更新仓库 ──────────────────────────────────────────────────────────
def ensure_repo(name, url_branch, src_dir, token):
    """clone 或 pull 仓库，返回本地路径。url_branch 可以是 str 或 (url, branch) 元组"""
    if isinstance(url_branch, tuple):
        url, branch = url_branch
    else:
        url, branch = url_branch, "master"
    repo_dir = os.path.join(src_dir, name)
    auth_url = url.replace("https://", f"https://{token}@")
    if os.path.isdir(os.path.join(repo_dir, ".git")):
        log(f"Updating {name} (branch: {branch}) ...")
        run(["git", "fetch", "origin", branch], cwd=repo_dir)
        run(["git", "reset", "--hard", "FETCH_HEAD"], cwd=repo_dir)
    else:
        log(f"Cloning {name} (branch: {branch}) ...")
        run(["git", "clone", "--branch", branch, auth_url, repo_dir])
    return repo_dir


def _ensure_repo_wsl(name, url_branch, token, arch):
    """
    在 WSL 内部文件系统（/tmp/freecdn-src/<name>）clone 或更新仓库。
    返回 WSL 内的路径字符串（供 WSL 命令使用）。
    """
    if isinstance(url_branch, tuple):
        url, branch = url_branch
    else:
        url, branch = url_branch, "master"
    auth_url  = url.replace("https://", f"https://{token}@")
    repo_path = f"/tmp/freecdn-src/{name}"
    host_ip   = _get_wsl_host_ip()
    proxy     = f"http://{host_ip}:4780"
    # 先检查是否已经 clone
    check = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "-u", "root", "--",
         "bash", "-c", f"test -d '{repo_path}/.git' && echo YES || echo NO"],
        capture_output=True, text=True
    )
    if "YES" in check.stdout:
        log(f"[WSL] Updating {name} in {repo_path} ...")
        script = (
            f"export HTTPS_PROXY={proxy} HTTP_PROXY={proxy}; "
            f"cd '{repo_path}' && git fetch origin {branch} && git reset --hard FETCH_HEAD"
        )
    else:
        log(f"[WSL] Cloning {name} into {repo_path} ...")
        script = (
            f"export HTTPS_PROXY={proxy} HTTP_PROXY={proxy}; "
            f"mkdir -p /tmp/freecdn-src && "
            f"git clone --branch {branch} '{auth_url}' '{repo_path}'"
        )
    result = subprocess.run(
        ["wsl", "-d", WSL_DISTRO, "-u", "root", "--", "bash", "-c", script],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in result.stdout.splitlines():
        print(f"  {line}")
    if result.returncode != 0:
        log(f"ERROR: WSL repo setup failed (exit {result.returncode})")
        sys.exit(1)
    return repo_path  # WSL 内的路径


# ── 编译单个组件 ──────────────────────────────────────────────────────────────
def compile_binary(go_bin, repo_dir, cmd_subdir, output_path, goos, goarch, use_wsl=False):
    """
    在 repo_dir 下编译 cmd/<cmd_subdir>/main.go，输出到 output_path。
    use_wsl=True 时在 WSL Linux 环境编译（支持 CGO，用于 edge-node）。
    """
    cmd_path = f"./cmd/{cmd_subdir}"

    if use_wsl:
        # 路径转换：如果已经是 /xxx 形式就不转，否则从 Windows 路径转 WSL 路径
        repo_dir_wsl    = repo_dir    if repo_dir.startswith("/")    else wsl_path(repo_dir)
        output_path_wsl = output_path if output_path.startswith("/") else wsl_path(output_path)
        host_ip = _get_wsl_host_ip()
        proxy   = f"http://{host_ip}:4780"
        # arm64 交叉编译需要指定 CC
        cc_line = "export CC=aarch64-linux-gnu-gcc;" if goarch == "arm64" else ""
        # 用 env -i 启动干净环境，避免 Windows PATH 里的括号导致 bash syntax error
        script = (
            f"export PATH=/usr/local/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin; "
            f"export HTTPS_PROXY={proxy} HTTP_PROXY={proxy}; "
            f"export GOPROXY=https://proxy.golang.org,direct; "
            f"export GOFLAGS=-mod=mod; "
            f"export GOOS={goos} GOARCH={goarch} CGO_ENABLED=1; "
            f"{cc_line} "
            f"cd '{repo_dir_wsl}' && "
            f"go mod download && "
            f"go build -trimpath -ldflags='-s -w' -o '{output_path_wsl}' {cmd_path}"
        )
        log(f"[WSL] $ {script}")
        result = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "-u", "root", "--", "bash", "-c", script],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        for line in result.stdout.splitlines():
            print(f"  {line}")
        if result.returncode != 0:
            log(f"ERROR: WSL compile failed (exit {result.returncode})")
            sys.exit(1)
    else:
        env = _base_env()
        env["GOOS"]   = goos
        env["GOARCH"] = goarch
        env["CGO_ENABLED"] = "0"
        env["GOFLAGS"] = "-mod=mod"
        env["GOPROXY"] = "https://proxy.golang.org,direct"

        # 先 go mod download
        run([go_bin, "mod", "download"], cwd=repo_dir, env=env)

        run([go_bin, "build", "-trimpath", "-ldflags=-s -w",
             "-o", output_path, cmd_path],
            cwd=repo_dir, env=env)

    size = os.path.getsize(output_path) / 1024 / 1024
    log(f"  -> {output_path} ({size:.1f} MB)")


def _get_wsl_host_ip():
    """获取 WSL 宿主机 IP（用于代理）"""
    try:
        result = subprocess.run(
            ["wsl", "-d", WSL_DISTRO, "--", "ip", "route", "show", "default"],
            capture_output=True, text=True
        )
        import re
        for part in result.stdout.split():
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", part):
                return part
    except Exception:
        pass
    return "172.24.208.1"  # 默认回退


# ── 组装发布包 ────────────────────────────────────────────────────────────────
def build_package(go_bin, src_dir, work_dir, freecdn_ver, arch, repo_root, token):
    log(f"\n{'='*60}")
    log(f"Building {arch} ...")
    log(f"{'='*60}")

    arch_dir = os.path.join(work_dir, arch)
    os.makedirs(arch_dir, exist_ok=True)

    # 1. 确保三个仓库都是最新
    # admin 直接用本地工作目录（就是这个脚本所在的仓库），不重复 clone
    admin_dir = repo_root
    log(f"Using local admin repo: {admin_dir}")
    api_dir   = ensure_repo("api",  REPOS["api"],  src_dir, token)
    node_dir  = ensure_repo("node", REPOS["node"], src_dir, token)

    # 2. 编译三个二进制
    bin_dir = os.path.join(arch_dir, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    log(f"\n-- Compiling edge-admin ({arch}) --")
    compile_binary(go_bin, admin_dir, "edge-admin",
                   os.path.join(bin_dir, "edge-admin"), "linux", arch)

    log(f"\n-- Compiling freecdn-init ({arch}) --")
    compile_binary(go_bin, admin_dir, "freecdn-init",
                   os.path.join(bin_dir, "freecdn-init"), "linux", arch)

    log(f"\n-- Compiling edge-api ({arch}) --")
    compile_binary(go_bin, api_dir, "edge-api",
                   os.path.join(bin_dir, "edge-api"), "linux", arch)

    log(f"\n-- Compiling edge-installer-helper ({arch}) --")
    compile_binary(go_bin, api_dir, "installer-helper",
                   os.path.join(bin_dir, "edge-installer-helper"), "linux", arch)

    log(f"\n-- Compiling edge-node ({arch}) via WSL (CGO) --")
    # edge-node 在 WSL 本地文件系统里编译（避免跨 /mnt/c 的 I/O 性能问题）
    node_dir_wsl = _ensure_repo_wsl("node", REPOS["node"], token, arch)
    compile_binary(go_bin, node_dir_wsl, "edge-node",
                   os.path.join(bin_dir, "edge-node"), "linux", arch, use_wsl=True)

    # 3. 组装包目录
    pkg_name = f"freecdn-{freecdn_ver}-linux-{arch}"
    pkg_dir  = os.path.join(arch_dir, pkg_name)
    if os.path.exists(pkg_dir):
        shutil.rmtree(pkg_dir)
    os.makedirs(pkg_dir)

    log(f"\n-- Assembling package {pkg_name} --")

    # edge-admin 二进制
    shutil.copy2(os.path.join(bin_dir, "edge-admin"), os.path.join(pkg_dir, "edge-admin"))

    # freecdn-init 二进制（数据库初始化工具）
    freecdn_init_src = os.path.join(bin_dir, "freecdn-init")
    if os.path.exists(freecdn_init_src):
        shutil.copy2(freecdn_init_src, os.path.join(pkg_dir, "freecdn-init"))
        log("  Copied freecdn-init")

    # web 资源（直接用 admin 仓库的 web/）
    web_src = os.path.join(admin_dir, "web")
    if os.path.isdir(web_src):
        shutil.copytree(web_src, os.path.join(pkg_dir, "web"))
        log("  Copied web/")
    else:
        log("  WARN: web/ not found in admin repo")

    # edge-api
    api_bin_dir = os.path.join(pkg_dir, "edge-api", "bin")
    os.makedirs(api_bin_dir, exist_ok=True)
    shutil.copy2(os.path.join(bin_dir, "edge-api"),
                 os.path.join(api_bin_dir, "edge-api"))

    # edge-installer-helper（放入 edge-api/installers/，安装脚本将其复制到服务器同目录）
    installers_dir = os.path.join(pkg_dir, "edge-api", "installers")
    os.makedirs(installers_dir, exist_ok=True)
    helper_src = os.path.join(bin_dir, "edge-installer-helper")
    if os.path.exists(helper_src):
        helper_dst_name = f"edge-installer-helper-linux-{arch}"
        shutil.copy2(helper_src, os.path.join(installers_dir, helper_dst_name))
        log(f"  edge-installer-helper -> edge-api/installers/{helper_dst_name}")
    else:
        log("  WARN: edge-installer-helper not found, SSH node install will be broken")

    # edge-node（打包成 zip 放进 edge-api/deploy/，供安装脚本分发到边缘节点）
    deploy_dir = os.path.join(pkg_dir, "edge-api", "deploy")
    os.makedirs(deploy_dir, exist_ok=True)
    node_zip_name = f"edge-node-linux-{arch}-{freecdn_ver}.zip"
    node_zip_path = os.path.join(deploy_dir, node_zip_name)
    _make_node_zip(node_dir, os.path.join(bin_dir, "edge-node"), node_zip_path, arch)
    log(f"  edge-node zip: {node_zip_name}")

    # FreeCDN 附带文件
    for fname in ["install.sh", "install-node.sh", "README.md", "NOTICE", "LICENSE"]:
        src = os.path.join(repo_root, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(pkg_dir, fname))
    docs_src = os.path.join(repo_root, "docs")
    if os.path.isdir(docs_src):
        shutil.copytree(docs_src, os.path.join(pkg_dir, "docs"))

    # VERSION 文件
    with open(os.path.join(pkg_dir, "VERSION"), "w") as f:
        f.write(f"FreeCDN {freecdn_ver}\n")
        f.write(f"Build date: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
        f.write(f"Components: edge-admin / edge-api / edge-node\n")
        f.write(f"Source: https://github.com/hujiali30001\n")

    # 4. 打 tar.gz
    archive_name = f"{pkg_name}.tar.gz"
    archive_path = os.path.join(work_dir, archive_name)
    log(f"\nCreating {archive_path}")
    with tarfile.open(archive_path, "w:gz") as tf:
        tf.add(pkg_dir, arcname=pkg_name)
    size_mb = os.path.getsize(archive_path) / 1024 / 1024
    log(f"Done: {archive_name} ({size_mb:.1f} MB)")
    return archive_path


def _make_node_zip(node_repo_dir, node_bin_path, zip_path, arch):
    """把 edge-node 二进制 + configs/ 模板打成 zip，供 SSH 安装节点时解压到目标目录。

    解压后的目录结构（installer_node.go 期望的路径）：
        edge-node/
            bin/edge-node          ← 可执行文件
            configs/api_node.yaml  ← 安装器写入 RPC 配置的目标文件

    注意：必须显式写入目录条目（以 "/" 结尾的 ZipInfo），否则 unzip.go 的
    目录分支不会触发，仅靠文件条目写文件时父目录可能不存在（即使新版 unzip.go
    已加 MkdirAll，显式目录条目也是 zip 格式的最佳实践）。
    """
    import zipfile
    from zipfile import ZipInfo
    import stat as stat_mod

    def _dir_info(arcname):
        """创建目录条目（必须以 / 结尾，mode 设为目录位）。
        
        关键：必须将 create_system 设为 3（Unix），否则 Go 的 archive/zip 会走
        Windows 分支，忽略 external_attr 里的 Unix 权限位，创建目录时使用默认
        0666（umask 后变为 0664），导致目录缺少执行位（x），stat 报 permission denied。
        """
        info = ZipInfo(arcname + "/")
        info.create_system = 3          # 3 = Unix（告诉 Go 按 Unix 解释 external_attr）
        info.external_attr = (stat_mod.S_IFDIR | 0o755) << 16
        info.compress_type = zipfile.ZIP_STORED  # 目录条目不压缩
        return info

    def _file_info(arcname, mode=0o755):
        """创建文件条目，指定 Unix 权限位。"""
        info = ZipInfo(arcname)
        info.create_system = 3          # 3 = Unix
        info.external_attr = (stat_mod.S_IFREG | mode) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        return info

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # 显式写入目录条目（create_system=3 使 Go 能正确应用 Unix 权限）
        for dir_arc in ["edge-node", "edge-node/bin", "edge-node/configs"]:
            zf.writestr(_dir_info(dir_arc), "")

        # 二进制放到 edge-node/bin/edge-node（设置可执行权限 0755）
        bin_info = _file_info("edge-node/bin/edge-node", mode=0o755)
        with open(node_bin_path, "rb") as f:
            zf.writestr(bin_info, f.read())

        # configs/ 目录：优先从仓库里拿模板；如果没有则创建空占位文件
        # installer_node.go 会覆写 configs/api_node.yaml，但父目录必须存在
        conf_src = os.path.join(node_repo_dir, "configs")
        if os.path.isdir(conf_src):
            has_any = False
            for root, dirs, files in os.walk(conf_src):
                for fname in files:
                    fpath = os.path.join(root, fname)
                    rel = "edge-node/configs/" + os.path.relpath(fpath, conf_src).replace("\\", "/")
                    with open(fpath, "rb") as f:
                        zf.writestr(_file_info(rel, mode=0o644), f.read())
                    has_any = True
            if not has_any:
                zf.writestr(_file_info("edge-node/configs/api_node.yaml", mode=0o644), "")
        else:
            zf.writestr(_file_info("edge-node/configs/api_node.yaml", mode=0o644), "")


# ── GitHub API ────────────────────────────────────────────────────────────────
def github_api(token, method, path, body=None, extra_headers=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-Builder/1.0",
    }
    if extra_headers:
        h.update(extra_headers)
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})


def upload_asset(token, upload_url, file_path):
    base_url = upload_url.split("{")[0]
    fname = os.path.basename(file_path)
    url = f"{base_url}?name={urllib.parse.quote(fname)}"
    log(f"Uploading {fname} ({os.path.getsize(file_path)/1024/1024:.1f} MB)")
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
        log(f"  -> {resp_data.get('browser_download_url', 'ok')}")
    else:
        log(f"  ERROR {resp.status}: {resp_data}")
    return resp.status in (200, 201)


def get_or_create_release(token, version):
    status, data = github_api(token, "GET", f"/repos/{RELEASE_REPO}/releases/tags/{version}")
    if status == 200:
        log(f"Found existing release: {data['id']} - {data['name']}")
        return data
    log(f"Creating release {version} ...")
    body = {
        "tag_name": version,
        "name": f"FreeCDN {version}",
        "body": (
            f"## FreeCDN {version}\n\n"
            "全组件从源码自主构建（edge-admin / edge-api / edge-node），不依赖第三方二进制。\n\n"
            "### 快速安装\n\n"
            "```bash\n"
            "curl -sSL https://raw.githubusercontent.com/hujiali30001/freecdn-admin/main/install.sh | sudo bash\n"
            "```\n"
        ),
        "draft": False,
        "prerelease": False,
    }
    status, data = github_api(token, "POST", f"/repos/{RELEASE_REPO}/releases", body)
    if status == 201:
        log(f"Created release: {data['id']}")
        return data
    log(f"ERROR creating release: {status} {data}")
    return None


def check_version_consistency(version_tag, repo_root, src_dir, token):
    """
    检查三个仓库的 internal/const/const.go 中 Version 字段是否与 version_tag 一致。
    version_tag 形如 "v0.6.0"，const.go 中应为 "0.6.0"。
    失败时打印详情并返回 False。
    """
    expected = version_tag.lstrip("v")  # "v0.6.0" -> "0.6.0"
    log(f"\n{'='*60}")
    log(f"版本号一致性检查（期望: {expected}）")
    log(f"{'='*60}")

    # 确保 api/node 仓库已 clone
    api_dir  = ensure_repo("api",  REPOS["api"],  src_dir, token)
    node_dir = ensure_repo("node", REPOS["node"], src_dir, token)

    repos_to_check = {
        "freecdn-admin": os.path.join(repo_root, "internal", "const", "const.go"),
        "freecdn-api":   os.path.join(api_dir,   "internal", "const", "const.go"),
        "freecdn-node":  os.path.join(node_dir,  "internal", "const", "const.go"),
    }

    import re
    all_ok = True
    for repo_name, const_path in repos_to_check.items():
        if not os.path.isfile(const_path):
            log(f"  [WARN] {repo_name}: const.go 不存在 ({const_path})，跳过检查")
            continue
        content = open(const_path, encoding="utf-8").read()
        m = re.search(r'Version\s*=\s*"([^"]+)"', content)
        if not m:
            log(f"  [WARN] {repo_name}: 未找到 Version 字段，跳过")
            continue
        found = m.group(1)
        if found == expected:
            log(f"  [OK]  {repo_name}: Version = \"{found}\" OK")
        else:
            log(f"  [FAIL] {repo_name}: Version = \"{found}\"，期望 \"{expected}\"")
            all_ok = False

    if not all_ok:
        log("")
        log("ERROR: 版本号不一致！请先更新各仓库 internal/const/const.go 中的 Version 字段")
        log("  freecdn-admin: internal/const/const.go")
        log(f"  freecdn-api:  {os.path.join(api_dir, 'internal', 'const', 'const.go')}")
        log(f"  freecdn-node: {os.path.join(node_dir, 'internal', 'const', 'const.go')}")
        log("  然后 commit + push，再重新运行构建脚本")
    return all_ok


# ── 主入口 ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="FreeCDN full-source build & GitHub Release upload")
    parser.add_argument("--token",   required=True, help="GitHub PAT (contents:write)")
    parser.add_argument("--version", default="v0.2.0", help="FreeCDN release version tag")
    parser.add_argument("--arch",    default="all",    help="amd64, arm64, or all")
    parser.add_argument("--work-dir", default=None,   help="Build output directory")
    parser.add_argument("--src-dir",  default=None,   help="Directory for cloned source repos")
    parser.add_argument("--no-upload", action="store_true", help="Build only, skip GitHub upload")
    parser.add_argument("--skip-version-check", action="store_true",
                        help="跳过版本号一致性检查（不推荐）")
    args = parser.parse_args()

    # 找 go
    go_bin = find_go()
    if not go_bin:
        log("ERROR: go not found. Install Go 1.22+ or set PATH.")
        sys.exit(1)
    result = subprocess.run([go_bin, "version"], capture_output=True, text=True)
    log(f"Using Go: {result.stdout.strip()}")

    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    work_dir  = args.work_dir or os.path.join(repo_root, "dist", "build")
    src_dir   = args.src_dir  or os.path.join(repo_root, "dist", "src")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(src_dir,  exist_ok=True)

    # ── 版本号一致性检查（构建前强制执行）────────────────────────────────────
    if not args.skip_version_check:
        if not check_version_consistency(args.version, repo_root, src_dir, args.token):
            sys.exit(1)
        log("版本号一致性检查通过 [PASS]")
    else:
        log("WARNING: 跳过版本号一致性检查（--skip-version-check）")

    archs = ARCHS if args.arch == "all" else [args.arch]

    # 构建各架构
    archives = []
    for arch in archs:
        path = build_package(go_bin, src_dir, work_dir, args.version, arch, repo_root, args.token)
        if path:
            archives.append(path)
        else:
            log(f"Build failed for {arch}")
            sys.exit(1)

    # SHA256SUMS
    checksum_path = os.path.join(work_dir, "SHA256SUMS")
    with open(checksum_path, "w") as f:
        for p in archives:
            digest = sha256sum(p)
            f.write(f"{digest}  {os.path.basename(p)}\n")
            log(f"SHA256 {os.path.basename(p)}: {digest}")
    archives.append(checksum_path)

    if args.no_upload:
        log("\n=== Build complete (--no-upload, skipping GitHub upload) ===")
        for p in archives:
            log(f"  {p}")
        return

    # 上传到 GitHub Release
    release = get_or_create_release(args.token, args.version)
    if not release:
        sys.exit(1)

    upload_url = release["upload_url"]
    existing_assets = {a["name"]: a["id"] for a in release.get("assets", [])}
    for p in archives:
        fname = os.path.basename(p)
        if fname in existing_assets:
            log(f"Deleting existing asset: {fname}")
            github_api(args.token, "DELETE",
                       f"/repos/{RELEASE_REPO}/releases/assets/{existing_assets[fname]}")

    for p in archives:
        if not upload_asset(args.token, upload_url, p):
            log(f"Upload failed: {p}")
            sys.exit(1)

    # 上传 install.sh（方便用户 curl 一键安装）
    install_sh_path = os.path.join(repo_root, "install.sh")
    if os.path.isfile(install_sh_path):
        fname = "install.sh"
        if fname in existing_assets:
            log(f"Deleting existing asset: {fname}")
            github_api(args.token, "DELETE",
                       f"/repos/{RELEASE_REPO}/releases/assets/{existing_assets[fname]}")
        log("Uploading install.sh ...")
        if not upload_asset(args.token, upload_url, install_sh_path):
            log("WARNING: install.sh upload failed")
        else:
            log("  install.sh uploaded OK")
    else:
        log("WARN: install.sh not found in repo root, skipping")

    log("\n=== All done! ===")
    log(f"Release: {release.get('html_url', 'https://github.com/' + RELEASE_REPO + '/releases/tag/' + args.version)}")


if __name__ == "__main__":
    main()
