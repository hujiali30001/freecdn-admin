# FreeCDN v0.10.0 编译指南

**版本**: v0.10.0  
**日期**: 2026-03-18  
**状态**: 🟢 CSS 升级完成，准备编译二进制

---

## 📋 **当前状态**

✅ **已完成**:
- CSS 设计系统升级（DESIGN_SYSTEM.md）
- 14 个页面 LESS 文件升级
- 18 个 LESS 文件全量编译验证（0 错误）
- 版本号更新到 v0.10.0
- Git 提交和推送到 GitHub

⏳ **待完成**:
- 编译 Windows/Linux/macOS 二进制
- 上传到 GitHub Releases
- 浏览器验证

---

## 🔧 **环境检查清单**

在编译之前，请检查以下环境：

### **必需**
- [ ] Go 1.22+ 已安装
- [ ] Git 已安装
- [ ] Node.js + npm 已安装（用于 LESS 编译）
- [ ] zip/unzip 命令可用
- [ ] sed 命令可用

### **可选**
- [ ] EdgeAPI 仓库已克隆（在 `../EdgeAPI` 相对路径）
- [ ] EdgeNode 仓库已克隆（在 `../EdgeNode` 相对路径）
- [ ] uglifyjs 已安装（用于 JS 压缩）
- [ ] gcc 已安装（用于 Linux 静态链接）

---

## 🚀 **编译步骤**

### **方式 1: 编译单平台（推荐用于测试）**

#### 编译 Windows 版本
```bash
cd FreeCDN/build
./build.sh windows amd64
# 输出: dist/edge-admin-windows-amd64-community-v0.10.0.zip
```

#### 编译 Linux 版本
```bash
cd FreeCDN/build
./build.sh linux amd64
# 输出: dist/edge-admin-linux-amd64-community-v0.10.0.zip
```

#### 编译 macOS 版本
```bash
cd FreeCDN/build
./build.sh darwin amd64
./build.sh darwin arm64
# 输出: dist/edge-admin-darwin-amd64-community-v0.10.0.zip
#       dist/edge-admin-darwin-arm64-community-v0.10.0.zip
```

### **方式 2: 编译所有平台**

```bash
cd FreeCDN/build
./build-all.sh
```

这会自动编译所有平台：
- linux amd64
- linux 386
- linux arm64
- linux mips64
- linux mips64le
- darwin amd64
- darwin arm64

---

## 📦 **编译产物**

成功编译后，会在 `FreeCDN/dist/` 目录下生成 ZIP 文件：

```
dist/
├── edge-admin-windows-amd64-community-v0.10.0.zip
├── edge-admin-linux-amd64-community-v0.10.0.zip
├── edge-admin-darwin-amd64-community-v0.10.0.zip
└── edge-admin-darwin-arm64-community-v0.10.0.zip
```

每个 ZIP 包含：
```
edge-admin/
├── bin/
│   └── edge-admin          # 可执行文件
├── web/                    # Web 资源（含升级后的 CSS）
├── configs/
│   └── server.template.yaml
└── edge-api/               # 依赖的 API 服务
```

---

## 🔍 **编译验证**

### 检查编译结果
```bash
# 查看生成的 ZIP 文件
ls -lah FreeCDN/dist/edge-admin-*.zip

# 检查 ZIP 内容
unzip -l FreeCDN/dist/edge-admin-linux-amd64-community-v0.10.0.zip | head -20
```

### 检查可执行文件
```bash
# Windows
file FreeCDN/dist/edge-admin/bin/edge-admin.exe
FreeCDN/dist/edge-admin/bin/edge-admin.exe --version

# Linux/macOS
file FreeCDN/dist/edge-admin/bin/edge-admin
FreeCDN/dist/edge-admin/bin/edge-admin --version
```

### 验证 CSS 文件
```bash
# 检查 CSS 是否包含在 ZIP 中
unzip -l FreeCDN/dist/edge-admin-linux-amd64-community-v0.10.0.zip | grep "\.css"
```

---

## 🐛 **常见问题处理**

### 问题 1: `go: not found`
**解决方案**:
```bash
# 检查 Go 安装
go version

# 如果未找到，安装 Go 1.22+
# 然后添加到 PATH
export PATH=$PATH:/usr/local/go/bin
```

### 问题 2: `edge-api build script not found`
**解决方案**: 确保 EdgeAPI 仓库在正确位置
```bash
# 期望路径
../EdgeAPI/build/build.sh

# 克隆（如果还没有）
cd ..
git clone https://github.com/hujiali30001/freecdn-api-src.git EdgeAPI
cd EdgeAPI && git checkout v1.3.9-freecdn
```

### 问题 3: `LESS 编译失败`
**解决方案**:
```bash
# 重新编译 LESS
cd FreeCDN
npm install
node compile_less.js

# 检查结果
ls -la web/views/@default/*/index.css
```

### 问题 4: `zip: command not found`
**解决方案**: 安装 zip 工具
```bash
# macOS
brew install zip

# Ubuntu/Debian
sudo apt-get install zip unzip

# CentOS/RHEL
sudo yum install zip unzip
```

---

## 📤 **上传到 GitHub Releases**

### 1. 创建 Release（如果还没有）
```bash
cd FreeCDN

# 创建 tag（如果还没有）
git tag -a v0.10.0 -m "v0.10.0: UI Modern Design System Complete"

# 推送 tag
git push origin v0.10.0
```

### 2. 上传二进制文件

使用 GitHub CLI：
```bash
# 需要先认证
gh auth login

# 创建 Release（编辑 RELEASE_NOTES.md 后）
gh release create v0.10.0 \
  dist/edge-admin-windows-amd64-community-v0.10.0.zip \
  dist/edge-admin-linux-amd64-community-v0.10.0.zip \
  dist/edge-admin-darwin-amd64-community-v0.10.0.zip \
  dist/edge-admin-darwin-arm64-community-v0.10.0.zip \
  --notes-file RELEASE_NOTES.md
```

或手动上传到 GitHub：
1. 打开 https://github.com/hujiali30001/freecdn-admin/releases
2. 点击 "Edit Release" for v0.10.0
3. 拖拽上传 ZIP 文件
4. 填写 Release Notes
5. 发布

### 3. Release Notes 模板

编写 `RELEASE_NOTES.md`:
```markdown
## v0.10.0 - UI Modern Design System Complete

### 🎨 Major Changes

#### CSS Modern Design System
- Complete design system with 4,300+ lines of documentation
- Unified color palette (primary, success, warning, error, neutral)
- Responsive typography system
- Spacing and sizing scales
- 4-level responsive breakpoints (480px, 768px, 1024px, desktop)

#### Page Upgrades
- **14 pages** upgraded with modern CSS
- Dashboard: Responsive grid layout + 5 component types
- Clusters: Interactive enhancements + pulse animations
- Servers: Table optimization + modern scrollbars
- Users: Feature card grid + 4 interaction states
- Settings, Logs, DNS, Admins, Nodes, Region, Index, Setup, DB, UI

#### Compilation
- ✅ 18/18 LESS files compiled successfully
- ✅ 0 errors, 0 warnings
- ✅ All pages responsive (mobile, tablet, desktop)

### 📦 Downloads

- Windows (amd64): edge-admin-windows-amd64-community-v0.10.0.zip
- Linux (amd64): edge-admin-linux-amd64-community-v0.10.0.zip
- macOS (amd64): edge-admin-darwin-amd64-community-v0.10.0.zip
- macOS (arm64): edge-admin-darwin-arm64-community-v0.10.0.zip

### 🔧 Installation

Extract the ZIP and run:
```bash
./edge-admin
```

### 📝 Release Notes Details
- Based on GoEdge v1.3.9 security baseline
- Compatible with EdgeAPI v1.3.9-freecdn
- EdgeNode v1.3.9+ recommended
```

---

## ✨ **验证 CSS 效果**

### 本地预览
```bash
# 启动 HTTP 服务器
cd FreeCDN/web
python3 -m http.server 8000

# 打开浏览器访问
# http://localhost:8000/views/@default/dashboard/
```

### 检查响应式
在浏览器开发者工具中：
1. 切换到响应式模式 (F12 → Ctrl+Shift+M)
2. 测试四个断点：
   - 480px (Mobile)
   - 768px (Tablet)
   - 1024px (Small Screen)
   - 1920px (Desktop)
3. 验证布局、间距、排版是否正确

---

## 🎯 **验收标准**

编译和发版时，请检查以下标准：

- [ ] 18 个 LESS 文件全部编译成功（0 错误）
- [ ] 所有平台的二进制文件成功生成
- [ ] 二进制文件能正常执行（--version 能输出版本号）
- [ ] ZIP 包中包含 CSS 文件
- [ ] Release 已发布到 GitHub
- [ ] Release Notes 包含完整描述
- [ ] 下载链接可用
- [ ] 页面在浏览器中样式正确显示

---

## 📚 **参考资源**

- 设计系统: `docs/DESIGN_SYSTEM.md`
- 项目计划: `PLAN.md`
- 构建脚本: `build/build.sh`, `build/build-all.sh`
- CSS 文件: `web/views/@default/*/index.less`

---

**编译开始日期**: 2026-03-18
**预计完成**: 2026-03-18（1-2 小时）

如有问题，查看上面的常见问题处理部分。
