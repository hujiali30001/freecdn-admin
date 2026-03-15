#!/usr/bin/env node
/**
 * FreeCDN 源码构建 & GitHub Release 上传脚本
 * 完全从源码编译，不依赖 GoEdge 上游 Release
 *
 * 用法:
 *   node scripts/build_from_source.js --token <GITHUB_TOKEN> [--version v0.1.4]
 *
 * 前置要求:
 *   - C:\Go_temp\go\bin\go.exe  (Go 1.22+)
 *   - C:\Users\Administrator\.workbuddy\EdgeCommon  (EdgeCommon 源码)
 *   - 当前目录为 FreeCDN 项目根目录
 */

const fs = require('fs');
const path = require('path');
const { execSync, spawnSync } = require('child_process');
const https = require('https');
const http = require('http');

// ──── 配置 ────────────────────────────────────────────────────────────────────
const REPO = 'hujiali30001/freecdn-admin';
const GO_BIN = 'C:\\Go_temp\\go\\bin\\go.exe';
const ROOT = path.resolve(__dirname, '..');
const DIST_DIR = path.join(ROOT, 'dist', 'build');
const WEB_DIR = path.join(ROOT, 'web');

const ARCHS = [
  { goos: 'linux', goarch: 'amd64', suffix: 'linux-amd64' },
  { goos: 'linux', goarch: 'arm64', suffix: 'linux-arm64' },
];

// ──── 参数解析 ─────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
function getArg(name) {
  const idx = args.indexOf(name);
  return idx >= 0 ? args[idx + 1] : null;
}

const TOKEN = getArg('--token');
const VERSION = getArg('--version') || 'v0.1.4';

if (!TOKEN) {
  console.error('[!] --token is required');
  process.exit(1);
}

// ──── 工具函数 ─────────────────────────────────────────────────────────────────
function log(msg) { console.log(`[build] ${msg}`); }
function run(cmd, opts = {}) {
  log(`> ${cmd}`);
  const result = spawnSync(cmd, { shell: true, stdio: 'inherit', cwd: opts.cwd || ROOT, env: { ...process.env, ...opts.env } });
  if (result.status !== 0) {
    console.error(`[!] Command failed with exit code ${result.status}`);
    process.exit(result.status || 1);
  }
}

// ──── Step 1: 清理并重建输出目录 ──────────────────────────────────────────────
log(`Building FreeCDN ${VERSION} from source`);
if (fs.existsSync(DIST_DIR)) {
  try {
    fs.rmSync(DIST_DIR, { recursive: true, force: true });
  } catch (e) {
    log(`Warning: could not fully clean dist dir (${e.code}), continuing...`);
  }
}
fs.mkdirSync(DIST_DIR, { recursive: true });

// ──── Step 2: 编译各架构 ──────────────────────────────────────────────────────
const builtFiles = [];

for (const { goos, goarch, suffix } of ARCHS) {
  log(`Compiling ${goos}/${goarch}...`);
  const outBin = path.join(DIST_DIR, `edge-admin-${suffix}`);
  run(`${GO_BIN} build -ldflags="-s -w" -o "${outBin}" ./cmd/edge-admin/`, {
    env: {
      GOOS: goos,
      GOARCH: goarch,
      CGO_ENABLED: '0',
      GOPROXY: 'https://goproxy.cn,direct',
      GONOSUMDB: '*',
    }
  });
  log(`  => ${outBin} (${(fs.statSync(outBin).size / 1024 / 1024).toFixed(1)} MB)`);

  // ──── Step 3: 打包 tar.gz ─────────────────────────────────────────────────
  const pkgName = `freecdn-${VERSION}-${suffix}`;
  const pkgDir = path.join(DIST_DIR, pkgName);
  fs.mkdirSync(pkgDir, { recursive: true });
  fs.mkdirSync(path.join(pkgDir, 'bin'), { recursive: true });

  // 复制二进制
  fs.copyFileSync(outBin, path.join(pkgDir, 'bin', 'edge-admin'));

  // 复制 web 目录（品牌修改后的静态资源）
  copyDir(WEB_DIR, path.join(pkgDir, 'web'));

  // 打包
  const tarFile = path.join(DIST_DIR, `${pkgName}.tar.gz`);
  run(`tar -czf "${tarFile}" -C "${DIST_DIR}" "${pkgName}"`);
  log(`  => ${tarFile} (${(fs.statSync(tarFile).size / 1024 / 1024).toFixed(1)} MB)`);
  builtFiles.push({ path: tarFile, name: `${pkgName}.tar.gz` });

  // 清理临时目录
  fs.rmSync(pkgDir, { recursive: true, force: true });
  fs.rmSync(outBin, { force: true });
}

// ──── Step 4: 创建 GitHub Release & 上传 ─────────────────────────────────────
log(`Creating GitHub Release ${VERSION}...`);

async function apiRequest(method, urlPath, body, extraHeaders = {}) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: urlPath,
      method,
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'FreeCDN-Builder/2.0',
        'Content-Type': 'application/json',
        ...extraHeaders,
      },
    };
    if (body) options.headers['Content-Length'] = Buffer.byteLength(body);
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (c) => data += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

async function uploadAsset(uploadUrl, filePath, fileName) {
  const baseUrl = uploadUrl.replace(/{.*}/, '');
  const url = new URL(`${baseUrl}?name=${encodeURIComponent(fileName)}`);
  return new Promise((resolve, reject) => {
    const fileData = fs.readFileSync(filePath);
    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'FreeCDN-Builder/2.0',
        'Content-Type': 'application/octet-stream',
        'Content-Length': fileData.length,
      },
    };
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (c) => data += c);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    req.write(fileData);
    req.end();
  });
}

(async () => {
  // 检查是否已存在同名 release
  const listResp = await apiRequest('GET', `/repos/${REPO}/releases?per_page=10`);
  let releaseId = null;
  let uploadUrl = null;
  if (Array.isArray(listResp.body)) {
    const existing = listResp.body.find(r => r.tag_name === VERSION);
    if (existing) {
      log(`Release ${VERSION} already exists (id=${existing.id}), will upload to it`);
      releaseId = existing.id;
      uploadUrl = existing.upload_url;
    }
  }

  if (!releaseId) {
    const createBody = JSON.stringify({
      tag_name: VERSION,
      name: `FreeCDN ${VERSION}`,
      body: `FreeCDN ${VERSION}\n\n从源码编译，完全独立，不依赖 GoEdge 上游 Release。`,
      draft: false,
      prerelease: false,
    });
    const createResp = await apiRequest('POST', `/repos/${REPO}/releases`, createBody);
    if (createResp.status !== 201) {
      console.error('[!] Failed to create release:', JSON.stringify(createResp.body));
      process.exit(1);
    }
    releaseId = createResp.body.id;
    uploadUrl = createResp.body.upload_url;
    log(`Release created: id=${releaseId}`);
  }

  // 上传文件
  for (const { path: filePath, name: fileName } of builtFiles) {
    log(`Uploading ${fileName} (${(fs.statSync(filePath).size / 1024 / 1024).toFixed(1)} MB)...`);
    const uploadResp = await uploadAsset(uploadUrl, filePath, fileName);
    if (uploadResp.status === 201) {
      log(`  => uploaded: ${uploadResp.body.browser_download_url}`);
    } else {
      console.error(`  [!] Upload failed (${uploadResp.status}):`, JSON.stringify(uploadResp.body).slice(0, 200));
    }
  }

  log(`\nDone! https://github.com/${REPO}/releases/tag/${VERSION}`);
})();

// ──── 工具：递归复制目录 ──────────────────────────────────────────────────────
function copyDir(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const name of fs.readdirSync(src)) {
    const srcPath = path.join(src, name);
    const dstPath = path.join(dst, name);
    if (fs.statSync(srcPath).isDirectory()) {
      copyDir(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}
