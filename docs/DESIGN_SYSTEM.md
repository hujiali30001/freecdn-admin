# FreeCDN 设计系统 v0.10.0

> 更新于 2026-03-18 | 版本 v0.10.0（规划中）

---

## 1. 色彩系统

### 1.1 品牌色板

| 名称 | HEX | RGB | 用途 |
|------|-----|-----|------|
| 品牌紫 | `#667eea` | rgb(102, 126, 234) | 主色、链接、活跃状态 |
| 深紫色 | `#764ba2` | rgb(118, 75, 162) | 渐变终点、暗化状态 |
| 浅紫色 | `#e9ecef` | rgb(233, 236, 239) | 背景、悬停效果 |

### 1.2 功能色

| 名称 | HEX | 用途 |
|------|-----|------|
| 成功色 | `#48bb78` | 成功状态、上升趋势 |
| 警告色 | `#ed8936` | 警告信息、需要关注 |
| 危险色 | `#f56565` | 错误、删除操作 |
| 信息色 | `#4299e1` | 信息提示、中性 |

### 1.3 中立色（灰度系列）

| 级别 | HEX | RGB | 用途 |
|-----|-----|-----|------|
| 灰-900 | `#000000` | rgb(0, 0, 0) | 深层文字（不常用） |
| 灰-800 | `#1a202c` | rgb(26, 32, 44) | 主标题 |
| 灰-700 | `#2d3748` | rgb(45, 55, 72) | 正文文字 |
| 灰-600 | `#4a5568` | rgb(74, 85, 104) | 次要文字 |
| 灰-500 | `#718096` | rgb(113, 128, 150) | 占位符、禁用文字 |
| 灰-400 | `#cbd5e0` | rgb(203, 213, 224) | 边框、分割线 |
| 灰-300 | `#e2e8f0` | rgb(226, 232, 240) | 浅边框、悬停背景 |
| 灰-200 | `#edf2f7` | rgb(237, 242, 247) | 轻背景 |
| 灰-100 | `#f7fafc` | rgb(247, 250, 252) | 主背景 |
| 灰-50  | `#ffffff` | rgb(255, 255, 255) | 卡片背景、纯白 |

### 1.4 颜色使用规则

**文字颜色**：
- 主文字：`#2d3748`（灰-700）
- 次要文字：`#718096`（灰-500）
- 禁用文字：`#cbd5e0`（灰-400）
- 白色文字：`#ffffff`（灰-50）

**背景颜色**：
- 页面背景：`#f7fafc`（灰-100）
- 卡片背景：`#ffffff`（灰-50）
- 表格行 hover：`rgba(102, 126, 234, 0.08)`（紫色 8% 透明）
- 输入框焦点背景：`#ffffff`（灰-50）
- 禁用背景：`#f7fafc`（灰-100）

**边框颜色**：
- 标准边框：`#e2e8f0`（灰-300）
- 聚焦边框：`#667eea`（品牌紫）
- 错误边框：`#f56565`（危险红）

---

## 2. 排版系统

### 2.1 字体栈

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 
             'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', 
             Helvetica, Arial, sans-serif;
```

### 2.2 字号和行高

| 用途 | 字号 | 行高 | 字重 | 样例 |
|------|------|------|------|------|
| 超大标题 | 32px | 1.2 | 700 | 页面大标题 |
| 大标题 | 24px | 1.3 | 600 | 模块标题 |
| 中标题 | 18px | 1.4 | 600 | 表格标题、弹窗标题 |
| 小标题 | 16px | 1.5 | 600 | 卡片标题 |
| 正文 | 14px | 1.6 | 400 | 表格行、列表项、描述 |
| 大正文 | 15px | 1.6 | 500 | 表单标签 |
| 小正文 | 12px | 1.5 | 400 | 提示文字、日期、状态 |
| 超小正文 | 11px | 1.4 | 400 | 辅助标签 |

### 2.3 常用文字组合

**页面标题**：
```css
font-size: 24px;
font-weight: 600;
line-height: 1.3;
color: #2d3748;
```

**表格标题**：
```css
font-size: 14px;
font-weight: 600;
line-height: 1.5;
color: #667eea;
text-transform: uppercase;
letter-spacing: 0.5px;
```

**正文**：
```css
font-size: 14px;
font-weight: 400;
line-height: 1.6;
color: #2d3748;
```

**辅助文字**：
```css
font-size: 12px;
font-weight: 400;
line-height: 1.5;
color: #718096;
```

---

## 3. 间距系统

### 3.1 间距单位

基础间距单位：**4px**

| 名称 | 值 | 用途 |
|------|-----|------|
| xs | 4px | 紧凑元素、图标间距 |
| sm | 8px | 小元素间距 |
| md | 12px | 标准间距 |
| lg | 16px | 大间距 |
| xl | 20px | 超大间距 |
| 2xl | 24px | 模块间距 |
| 3xl | 32px | 大模块间距 |

### 3.2 常用间距

**卡片内边距**：
- 小卡片：`12px 16px`
- 标准卡片：`16px 20px`
- 大卡片：`20px 24px`

**表格行高**：
- 紧凑：`36px`
- 标准：`44px`
- 舒适：`52px`

**按钮内边距**：
- 小按钮：`8px 12px`
- 标准按钮：`12px 16px`
- 大按钮：`16px 20px`

**表单控件**：
- 高度：`36px`（小）/ `40px`（标准）/ `44px`（大）
- 内边距：`0 12px`
- 行高：按钮高度的中心对齐

---

## 4. 圆角系统

| 半径 | 用途 |
|------|------|
| 0px | 无圆角 |
| 4px | 小组件（标签、小按钮） |
| 8px | 输入框、小卡片 |
| 12px | 标准卡片 |
| 16px | 大卡片、弹窗 |
| 20px | 超大卡片、登录框 |
| 50% | 圆形（头像、圆形按钮） |

---

## 5. 阴影系统

### 5.1 阴影等级

| 等级 | CSS | 用途 |
|------|-----|------|
| 无 | none | 卡片边框式 |
| 轻 | `0 1px 2px rgba(0, 0, 0, 0.04)` | 表格行、微妙升起感 |
| 中轻 | `0 1px 3px rgba(0, 0, 0, 0.08)` | 卡片、输入框 |
| 中 | `0 4px 12px rgba(0, 0, 0, 0.1)` | 标准卡片、悬停 |
| 中重 | `0 8px 24px rgba(0, 0, 0, 0.12)` | 弹窗、下拉菜单 |
| 重 | `0 12px 32px rgba(0, 0, 0, 0.15)` | 顶层弹窗、模态框 |
| 很重 | `0 20px 60px rgba(0, 0, 0, 0.2)` | 登录框、全屏覆盖 |

---

## 6. 组件规范

### 6.1 按钮

**尺寸变体**：

| 尺寸 | 高度 | 内边距 | 字号 |
|------|------|--------|------|
| 小 | 32px | 8px 12px | 12px |
| 标准 | 40px | 10px 16px | 14px |
| 大 | 48px | 12px 20px | 16px |

**样式变体**：

- **主按钮**（蓝紫渐变）：背景 `linear-gradient(90deg, #667eea, #764ba2)`，文字白色
- **次按钮**（白底紫边）：背景白色，边框 `1px #667eea`，文字 `#667eea`
- **文字按钮**：无背景无边框，文字 `#667eea`，hover 背景淡紫
- **危险按钮**：背景 `#f56565`，文字白色

**状态**：

- 正常：完整色彩
- 悬停：背景加深、阴影增加、上移 2px
- 按下：背景更深、阴影减少、下移 1px
- 禁用：背景淡灰、文字淡灰、无阴影、cursor:not-allowed

### 6.2 输入框

**尺寸**：
- 高度：`40px`（标准）
- 内边距：`0 12px`
- 边框：`1px solid #e2e8f0`
- 圆角：`8px`

**状态**：
- 正常：灰边框、灰文字（占位符）
- 聚焦：紫边框、紫色光晕（box-shadow）、背景白色
- 错误：红边框、红色光晕、错误提示文字
- 禁用：淡灰背景、淡灰文字、无边框、cursor:not-allowed

**聚焦光晕**：
```css
box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
border-color: #667eea;
```

### 6.3 表格

**行高**：
- 表头行：`44px`
- 数据行：`44px`
- 紧凑模式：`36px`

**表头样式**：
- 背景：`#f7fafc`（灰-100）
- 文字：`#667eea`（品牌紫）、加粗（600）
- 边框下：`2px solid #667eea`

**行样式**：
- 背景：`#ffffff`（白）
- 边框下：`1px solid #e2e8f0`（灰）

**行 hover**：
- 背景：`rgba(102, 126, 234, 0.08)`（紫色 8% 透明）
- 过渡：`0.2s ease`

**行 active/selected**：
- 背景：`rgba(102, 126, 234, 0.15)`（紫色 15% 透明）
- 左边框：`3px solid #667eea`

### 6.4 卡片 (Card)

**标准卡片**：
- 背景：`#ffffff`
- 边框：`1px solid #e2e8f0`
- 圆角：`12px`
- 内边距：`20px`
- 阴影：`0 1px 3px rgba(0, 0, 0, 0.08)`

**提升卡片**（悬停）：
- 阴影升级：`0 4px 12px rgba(0, 0, 0, 0.1)`
- 变换：`translateY(-2px)`
- 过渡：`0.3s ease`

**卡片标题**：
- 字号：`16px`
- 字重：`600`
- 颜色：`#2d3748`
- 下边距：`16px`
- 边框下：`2px solid #f7fafc`

### 6.5 表单标签

**标签样式**：
- 字号：`14px`
- 字重：`500`
- 颜色：`#2d3748`
- 下边距：`8px`
- 必填符号：红色 `*`

---

## 7. 动画和过渡

### 7.1 标准过渡

| 持续时间 | 用途 |
|----------|------|
| 150ms | 快速反馈（按钮、颜色变化） |
| 200ms | 标准反馈（背景、阴影） |
| 300ms | 较慢反馈（高度、宽度、不透明度） |
| 500ms | 入场动画（页面过渡、模态框）|

### 7.2 缓动函数

```css
ease: cubic-bezier(0.25, 0.46, 0.45, 0.94);
ease-in: cubic-bezier(0.42, 0, 1, 1);
ease-out: cubic-bezier(0, 0, 0.58, 1);
ease-in-out: cubic-bezier(0.42, 0, 0.58, 1);
```

### 7.3 常用动画

**Fade 淡入淡出**：
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes fadeOut {
  from { opacity: 1; }
  to { opacity: 0; }
}
```

**Slide 滑动**：
```css
@keyframes slideUp {
  from { transform: translateY(16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes slideDown {
  from { transform: translateY(-16px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
```

**Scale 缩放**：
```css
@keyframes scaleIn {
  from { transform: scale(0.9); opacity: 0; }
  to { transform: scale(1); opacity: 1; }
}
```

---

## 8. 响应式断点

| 断点 | 宽度 | 用途 |
|------|------|------|
| xs | 0px - 480px | 手机竖屏 |
| sm | 480px - 768px | 手机横屏 |
| md | 768px - 1024px | 平板 |
| lg | 1024px - 1280px | 小屏桌面 |
| xl | 1280px+ | 大屏桌面 |

### 8.1 媒体查询

```css
/* 手机 */
@media (max-width: 767px) {
  /* 隐藏某些列、调整字号、改为单列布局 */
}

/* 平板 */
@media (min-width: 768px) and (max-width: 1023px) {
  /* 调整网格列数、调整间距 */
}

/* 桌面 */
@media (min-width: 1024px) {
  /* 完整布局 */
}
```

---

## 9. 深色模式

### 9.1 深色模式色彩映射

| 亮色 | HEX | 深色 | HEX |
|------|-----|------|-----|
| 页面背景 | `#f7fafc` | 页面背景 | `#1a202c` |
| 卡片背景 | `#ffffff` | 卡片背景 | `#2d3748` |
| 正文文字 | `#2d3748` | 正文文字 | `#e2e8f0` |
| 次要文字 | `#718096` | 次要文字 | `#cbd5e0` |
| 边框 | `#e2e8f0` | 边框 | `#4a5568` |

### 9.2 深色模式 CSS

```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-bg-primary: #1a202c;
    --color-bg-secondary: #2d3748;
    --color-text-primary: #e2e8f0;
    --color-text-secondary: #cbd5e0;
    --color-border: #4a5568;
  }
}
```

---

## 10. 使用指南

### 10.1 在代码中引用

建议在 CSS 变量中定义所有值：

```css
:root {
  /* 颜色 */
  --color-brand: #667eea;
  --color-brand-dark: #764ba2;
  --color-success: #48bb78;
  --color-warning: #ed8936;
  --color-danger: #f56565;
  
  /* 间距 */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 12px;
  --space-lg: 16px;
  --space-xl: 20px;
  --space-2xl: 24px;
  
  /* 圆角 */
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
  
  /* 阴影 */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.12);
}
```

然后在组件中使用：

```css
.button {
  background: var(--color-brand);
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}
```

### 10.2 常见问题

**Q：什么时候用品牌紫 vs 深紫？**
A：品牌紫（#667eea）用于主交互元素（按钮、链接、聚焦），深紫（#764ba2）用于渐变结束点和暗化状态。

**Q：如何保证文字对比度足够？**
A：所有文字颜色都需要符合 WCAG AA 标准（对比度 ≥ 4.5:1）。使用提供的中立色和颜色进行搭配。

**Q：响应式时如何处理表格？**
A：在小屏幕上（< 768px），将表格转换为卡片视图，每行变为一张卡片，字段名改为标签。

---

## 参考文档

- WCAG 2.1 无障碍标准：https://www.w3.org/WAI/WCAG21/quickref/
- CSS 最佳实践：https://developer.mozilla.org/en-US/docs/Web/CSS/
- 深色模式指南：https://web.dev/prefers-color-scheme/
