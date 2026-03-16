#!/usr/bin/env python3
"""
更新三主仓库 go.mod 中的 EdgeCommon replace 版本 hash，
以及更新版本号到 0.7.0
"""
import subprocess, sys, json, base64, http.client, urllib.parse, time, re, os

TOKEN  = os.environ.get("GITHUB_TOKEN", "")  # set via env: GITHUB_TOKEN=ghp_...
DISTRO = "Ubuntu-24.04"
WORKDIR = "/tmp/freecdn-b"

# 新的 EdgeCommon pseudo-version（commit 45be148915e8，UTC 2026-03-16 19:34:26）
NEW_PSEUDO = "v1.3.10-0.20260316193426-45be148915e8"
OLD_PSEUDO = "v1.3.10-0.20260315182923-7ed7574dde08"

NEW_VERSION = "0.7.0"


def wsl_run(cmd_list):
    r = subprocess.run(
        ["wsl", "-d", DISTRO, "-u", "root", "--"] + cmd_list,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in r.stdout.splitlines():
        print(f"  {line}")
    return r


def wsl_script(script, check=True):
    host_ip = "172.24.208.1"
    # 获取宿主机 IP
    r2 = subprocess.run(
        ["wsl", "-d", DISTRO, "--", "ip", "route", "show", "default"],
        capture_output=True, text=True
    )
    for part in r2.stdout.split():
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", part):
            host_ip = part
            break
    full = f"export HTTPS_PROXY=http://{host_ip}:4780 HTTP_PROXY=http://{host_ip}:4780; " + script
    r = subprocess.run(
        ["wsl", "-d", DISTRO, "-u", "root", "--", "bash", "-c", full],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    for line in r.stdout.splitlines():
        print(f"  {line}")
    if check and r.returncode != 0:
        print(f"ERROR: {r.returncode}")
        sys.exit(1)
    return r


def github_api(method, path, body=None):
    conn = http.client.HTTPSConnection("api.github.com")
    h = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FreeCDN-StageB/1.0",
    }
    payload = json.dumps(body).encode() if body else None
    if payload:
        h["Content-Type"] = "application/json"
    conn.request(method, path, body=payload, headers=h)
    resp = conn.getresponse()
    data = resp.read()
    return resp.status, (json.loads(data) if data else {})


def get_file_sha(repo, path):
    status, data = github_api("GET", f"/repos/{repo}/contents/{path}")
    if status == 200:
        return data.get("sha", "")
    return ""


def update_file_via_api(repo, path, new_content, message, branch="master"):
    sha = get_file_sha(repo, path)
    body = {
        "message": message,
        "content": base64.b64encode(new_content.encode()).decode(),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    status, data = github_api("PUT", f"/repos/{repo}/contents/{path}", body)
    if status in (200, 201):
        print(f"  [OK] {repo}/{path} updated")
        return True
    print(f"  [ERROR] {status}: {data}")
    return False


def get_file_content(repo, path):
    status, data = github_api("GET", f"/repos/{repo}/contents/{path}")
    if status == 200:
        return base64.b64decode(data["content"]).decode()
    return None


# ── 1. 更新 freecdn-api go.mod ────────────────────────────────────────────────
def update_api_gomod():
    print("\n=== Updating freecdn-api go.mod ===")
    content = get_file_content("hujiali30001/freecdn-api", "go.mod")
    if not content:
        print("ERROR: cannot fetch go.mod")
        return False
    new = content.replace(OLD_PSEUDO, NEW_PSEUDO)
    if new == content:
        print("  [WARN] OLD_PSEUDO not found, checking current content...")
        for line in content.splitlines():
            if "EdgeCommon" in line or "freecdn-common" in line:
                print(f"  {line}")
    else:
        return update_file_via_api(
            "hujiali30001/freecdn-api", "go.mod", new,
            f"chore: update freecdn-common replace hash to {NEW_PSEUDO}"
        )
    return True


# ── 2. 更新 freecdn-node go.mod ───────────────────────────────────────────────
def update_node_gomod():
    print("\n=== Updating freecdn-node go.mod ===")
    content = get_file_content("hujiali30001/freecdn-node", "go.mod")
    if not content:
        print("ERROR: cannot fetch go.mod")
        return False
    new = content.replace(OLD_PSEUDO, NEW_PSEUDO)
    if new == content:
        print("  [WARN] OLD_PSEUDO not found")
        for line in content.splitlines():
            if "EdgeCommon" in line or "freecdn-common" in line:
                print(f"  {line}")
    else:
        return update_file_via_api(
            "hujiali30001/freecdn-node", "go.mod", new,
            f"chore: update freecdn-common replace hash to {NEW_PSEUDO}"
        )
    return True


# ── 3. 更新 freecdn-admin go.mod（本地） ──────────────────────────────────────
def update_admin_gomod():
    print("\n=== Updating freecdn-admin go.mod (local) ===")
    gomod_path = r"C:\Users\Administrator\.workbuddy\FreeCDN\go.mod"
    with open(gomod_path, "r", encoding="utf-8") as f:
        content = f.read()
    new = content.replace(OLD_PSEUDO, NEW_PSEUDO)
    if new == content:
        print("  [INFO] OLD_PSEUDO not found in admin go.mod, checking...")
        for line in content.splitlines():
            if "EdgeCommon" in line or "freecdn-common" in line:
                print(f"  {line}")
    else:
        with open(gomod_path, "w", encoding="utf-8") as f:
            f.write(new)
        print("  [OK] admin go.mod updated")
    return True


# ── 4. 更新版本号到 0.7.0 ─────────────────────────────────────────────────────
def update_versions():
    print("\n=== Updating version to 0.7.0 ===")

    def update_const(repo, branch="master"):
        content = get_file_content(repo, "internal/const/const.go")
        if not content:
            print(f"  ERROR: cannot fetch {repo}/internal/const/const.go")
            return False
        new = re.sub(r'Version\s*=\s*"[^"]+"', f'Version = "{NEW_VERSION}"', content, count=1)
        # NodeVersion（freecdn-api 里有）
        new = re.sub(r'NodeVersion\s*=\s*"[^"]+"', f'NodeVersion = "{NEW_VERSION}"', new, count=1)
        if new == content:
            print(f"  [SKIP] {repo}: version already {NEW_VERSION}")
            return True
        return update_file_via_api(
            repo, "internal/const/const.go", new,
            f"chore: bump version to {NEW_VERSION}",
            branch=branch
        )

    update_const("hujiali30001/freecdn-api",  "master")
    update_const("hujiali30001/freecdn-node", "master")

    # freecdn-admin const.go（本地）
    const_path = r"C:\Users\Administrator\.workbuddy\FreeCDN\internal\const\const.go"
    with open(const_path, "r", encoding="utf-8") as f:
        content = f.read()
    new = re.sub(r'Version\s*=\s*"[^"]+"', f'Version = "{NEW_VERSION}"', content, count=1)
    if new != content:
        with open(const_path, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"  [OK] freecdn-admin const.go: Version = {NEW_VERSION}")
    else:
        print(f"  [SKIP] freecdn-admin already {NEW_VERSION}")


# ── 5. 更新 install.sh / Dockerfile / docker-compose.yml ─────────────────────
def update_deploy_files():
    print("\n=== Updating deploy files to v0.7.0 ===")

    # install.sh
    ipath = r"C:\Users\Administrator\.workbuddy\FreeCDN\install.sh"
    with open(ipath, "r", encoding="utf-8") as f:
        content = f.read()
    new = re.sub(r'FREECDN_VERSION="v[^"]+"', 'FREECDN_VERSION="v0.7.0"', content, count=1)
    if new != content:
        with open(ipath, "w", encoding="utf-8") as f:
            f.write(new)
        print("  [OK] install.sh updated to v0.7.0")
    else:
        print("  [SKIP] install.sh")

    # deploy/Dockerfile
    dpath = r"C:\Users\Administrator\.workbuddy\FreeCDN\deploy\Dockerfile"
    with open(dpath, "r", encoding="utf-8") as f:
        content = f.read()
    new = re.sub(r'ARG FREECDN_VERSION=v[\d.]+', 'ARG FREECDN_VERSION=v0.7.0', content)
    if new != content:
        with open(dpath, "w", encoding="utf-8") as f:
            f.write(new)
        print("  [OK] deploy/Dockerfile updated to v0.7.0")
    else:
        print("  [SKIP] deploy/Dockerfile")

    # deploy/docker-compose.yml
    dcpath = r"C:\Users\Administrator\.workbuddy\FreeCDN\deploy\docker-compose.yml"
    with open(dcpath, "r", encoding="utf-8") as f:
        content = f.read()
    new = re.sub(r'FREECDN_VERSION:-v[\d.]+', 'FREECDN_VERSION:-v0.7.0', content)
    if new != content:
        with open(dcpath, "w", encoding="utf-8") as f:
            f.write(new)
        print("  [OK] deploy/docker-compose.yml updated to v0.7.0")
    else:
        print("  [SKIP] deploy/docker-compose.yml")


def main():
    update_api_gomod()
    update_node_gomod()
    update_admin_gomod()
    update_versions()
    update_deploy_files()
    print("\n=== All updates done! ===")
    print("Next: commit freecdn-admin local changes and build v0.7.0")


if __name__ == "__main__":
    main()
