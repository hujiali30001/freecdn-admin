# FreeCDN Phase 3 具体工作清单

> 基于 v0.9.2 完成后的短期任务分解

---

## Phase 3A：其他页面样式统一（v0.9.3）

### 📋 Task 3A-1：设置页面（`/settings/`）

**当前状态**：灰色系传统风格

**需要升级**：
- [ ] 页面背景改为浅紫色 `#f5f7ff`
- [ ] 表单分组卡片：白色 + 4px 圆角 + 阴影
- [ ] 表单标签：品牌色文字（活跃分类）
- [ ] 保存按钮：品牌色渐变
- [ ] 取消/返回按钮：灰色

**文件**：`web/views/@default/settings/index.less`

**预计工作量**：2 小时

---

### 📋 Task 3A-2：用户管理页（`/users/`）

**当前状态**：Semantic UI 默认样式

**需要升级**：
- [ ] 用户列表表头：品牌色 + 加粗
- [ ] 活跃用户行：浅紫色背景高亮
- [ ] 操作按钮：编辑/删除 icon 改品牌色
- [ ] 分页：品牌色高亮当前页
- [ ] 新增按钮：品牌色渐变

**文件**：`web/views/@default/users/index.less`

**预计工作量**：3 小时

---

### 📋 Task 3A-3：弹窗和对话框（`dialog`、`modal`）

**当前状态**：白色背景，黑色边框

**需要升级**：
- [ ] 弹窗标题栏：浅紫色背景 或 品牌色 icon
- [ ] 弹窗边框：品牌色 1px
- [ ] 确认按钮（Primary）：品牌色渐变
- [ ] 取消按钮（Secondary）：灰色
- [ ] 背景遮罩：黑色 + 毛玻璃效果

**文件**：`web/views/@default/@dialog.less`（通用）

**预计工作量**：2-3 小时

---

### 📋 Task 3A-4：按钮组件规范（`button`）

**当前状态**：Semantic UI 默认

**需要升级**：
```less
// Primary 按钮（主操作）
.button.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
  }
}

// Secondary 按钮（次要操作）
.button.secondary {
  background: #f0f0f0;
  color: #666666;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 8px 16px;
  
  &:hover {
    background: #e8e8e8;
  }
}

// Danger 按钮（删除操作）
.button.danger {
  background: #ff6b6b;
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  
  &:hover {
    background: #ff5252;
  }
}
```

**文件**：`web/views/@default/@button.less`（新建或更新）

**预计工作量**：2 小时

---

### 📋 Task 3A-5：表单控件（input、select、textarea）

**当前状态**：原始 HTML 样式

**需要升级**：
- [ ] 输入框边框：2px 灰色，焦点时品牌色
- [ ] 输入框高度：40px 标准高
- [ ] 占位符文字：浅灰色
- [ ] 焦点效果：品牌色光晕
- [ ] 禁用状态：浅灰背景
- [ ] 错误提示：红色 icon + 红色边框

**文件**：`web/views/@default/@form.less`（新建或更新）

**预计工作量**：3 小时

---

## Phase 3B：字体和排版优化（v0.9.4）

### 📋 Task 3B-1：定义全局 CSS 变量

**文件**：`web/views/@default/@variables.less`（新建）

**内容**：
```less
// 字体大小
@font-size-xs: 12px;
@font-size-sm: 13px;
@font-size-base: 14px;
@font-size-lg: 16px;
@font-size-xl: 18px;

// 字重
@font-weight-light: 300;
@font-weight-normal: 400;
@font-weight-medium: 500;
@font-weight-semibold: 600;
@font-weight-bold: 700;

// 行高
@line-height-tight: 1.2;
@line-height-normal: 1.5;
@line-height-loose: 1.8;

// 颜色
@color-brand-primary: #667eea;
@color-brand-secondary: #764ba2;
@color-text-primary: #333333;
@color-text-secondary: #666666;
@color-bg-primary: #f5f7ff;
@color-bg-secondary: #ffffff;
```

**预计工作量**：1 小时

---

### 📋 Task 3B-2：更新所有 LESS 文件导入

**操作**：在每个 .less 文件顶部加入
```less
@import "@variables.less";
```

**受影响文件**：
- [ ] `@layout.less`
- [ ] `@left_menu.less`
- [ ] `@grids.less`
- [ ] `index/index.less`
- [ ] `dashboard/index.less`
- [ ] `@button.less`
- [ ] `@form.less`
- [ ] `@dialog.less`

**预计工作量**：1-2 小时

---

### 📋 Task 3B-3：统一标题和正文字体

**标准**：
- `<h1>`：`@font-size-xl` + `@font-weight-bold` + `@line-height-tight`
- `<h2>`：`@font-size-lg` + `@font-weight-semibold` + `@line-height-tight`
- `<h3>`：`@font-size-base` + `@font-weight-semibold` + `@line-height-normal`
- `<p>`：`@font-size-base` + `@font-weight-normal` + `@line-height-normal`
- `<small>`：`@font-size-sm` + `@font-weight-normal` + `@color-text-secondary`

**预计工作量**：2 小时

---

## 发布计划

### v0.9.3 发布清单

- [ ] 完成 Task 3A-1 至 3A-5
- [ ] 测试所有页面的新样式
- [ ] 更新 PLAN.md 和版本号
- [ ] 生成发布说明
- [ ] 部署到 WSL 测试
- [ ] 创建 GitHub Release

**预计完成日期**：2026-03-25

---

### v0.9.4 发布清单

- [ ] 完成 Task 3B-1 至 3B-3
- [ ] 全量测试响应式
- [ ] 性能优化（LESS 编译体积）
- [ ] 浏览器兼容性测试
- [ ] 创建 GitHub Release

**预计完成日期**：2026-04-01

---

## 注意事项

1. **LESS 编译**：每个 Task 完成后，及时编译为 CSS 并提交
2. **版本号**：修改 `internal/const/const.go` 版本号与 Release tag 保持一致
3. **Git 提交**：按 Task 粒度分别提交，便于追溯
4. **部署验证**：每个 Task 完成后都要部署到 WSL 进行视觉验证
5. **浏览器测试**：至少测试 Chrome、Firefox、Safari 三个浏览器

---

最后更新：2026-03-17
