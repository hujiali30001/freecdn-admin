# FreeCDN 现代化设计系统指南

## 目录
1. [设计理念](#设计理念)
2. [颜色系统](#颜色系统)
3. [组件库](#组件库)
4. [响应式设计](#响应式设计)
5. [实施步骤](#实施步骤)
6. [常见问题](#常见问题)

---

## 设计理念

### 核心特性
- **现代化美学**：使用柔和的蓝紫渐变色调
- **一致性**：统一的卡片、阴影、圆角、间距
- **可访问性**：清晰的文字对比度和层级
- **响应式**：完美适配桌面、平板、移动设备

### 品牌配色

| 用途 | 颜色 | HEX值 |
|------|------|--------|
| 主背景 | 蓝紫渐变 | #f5f7ff → #f0f5ff |
| 侧边栏 | 紫色渐变 | #c5d0f5 → #d8c8f0 |
| 集群卡片 | 蓝色渐变 | #d4e5f9 → #c5d8f5 |
| 节点卡片 | 紫色渐变 | #e5d8f9 → #d8c8f5 |
| 用户卡片 | 粉色渐变 | #f9e5ec → #f5d8e3 |
| 服务器卡片 | 薰衣草渐变 | #f0e5f9 → #e5d8f5 |

---

## 颜色系统

### 文字颜色

| 级别 | 颜色 | HEX值 | 用途 |
|------|------|--------|------|
| 主标题 | 深灰蓝 | #1a202c | 页面标题、卡片标题 |
| 正文 | 中灰蓝 | #2d3748 | 常规文本内容 |
| 次级 | 浅灰蓝 | #4a5568 | 描述文本、小标题 |
| 辅助 | 更浅灰蓝 | #718096 | 提示文字、子信息 |

### 功能颜色
- **成功**：#21ba45（绿色）
- **警告**：#ff851b（橙色）
- **错误**：#db2828（红色）
- **信息**：#4183c4（蓝色）

---

## 组件库

### 1. 统计卡片（Stat Card）

**用途**：显示关键指标数据

**结构**：
```html
<div class="stat-card cluster">
    <div>
        <div class="stat-title">集群</div>
        <div class="stat-value">12</div>
    </div>
    <div class="stat-desc">全球分布式集群</div>
</div>
```

**样式规范**：
- 背景：渐变色（根据类型）
- 圆角：20px
- 内边距：24px（桌面端）/ 16px（移动端）
- 最小高度：140px（桌面端）
- 阴影：0 8px 24px rgba(0, 0, 0, 0.05)
- Hover 效果：translateY(-4px) + 阴影加强

**类型**：
- `.cluster`：蓝色（集群）
- `.node`：紫色（节点）
- `.user`：粉色（用户）
- `.server`：薰衣草色（服务器）

### 2. 卡片容器（Chart Card）

**用途**：包含图表、表格或内容的容器

**结构**：
```html
<div class="chart-card">
    <div class="chart-header">
        <span class="chart-title">实时流量趋势</span>
        <span class="chart-subtitle">（24小时）</span>
    </div>
    <div id="chart-container" class="chart-container"></div>
</div>
```

**样式规范**：
- 背景：白色（#ffffff）
- 圆角：20px
- 内边距：24px
- 阴影：0 8px 24px rgba(0, 0, 0, 0.05)
- 边框：1px solid rgba(226, 232, 240, 0.6)
- Hover 效果：translateY(-4px) + 阴影加强

### 3. 网格布局

**统计卡片网格**：
```css
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}
```

**图表区域网格**：
```css
.charts-grid {
    display: grid;
    grid-template-columns: 1fr 380px;
    gap: 20px;
}
```

### 4. 进度条

**用途**：显示任务进度或负载

**结构**：
```html
<div class="progress-item">
    <div class="progress-header">
        <span>集群A</span>
        <span>78%</span>
    </div>
    <div class="progress-bar">
        <div class="progress-fill" style="width: 78%"></div>
    </div>
</div>
```

**样式规范**：
- 背景条高度：12px（桌面端）/ 10px（移动端）
- 圆角：6px
- 渐变色：#8b9ff0 → #a88be8

---

## 响应式设计

### 断点规划

| 设备类型 | 宽度范围 | 特点 |
|---------|---------|------|
| 桌面端 | > 1400px | 4列统计卡片 + 双列图表 |
| 平板端 | 768px - 1400px | 2列统计卡片 + 单列图表 |
| 移动端 | < 768px | 1列卡片 + 全屏图表 |
| 超小屏 | < 480px | 优化字号和间距 |

### 响应式变化

**统计卡片**：
```css
/* 桌面端 */
.stats-grid { grid-template-columns: repeat(4, 1fr); }

/* 平板端 */
@media (max-width: 1400px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* 移动端 */
@media (max-width: 768px) {
    .stats-grid { grid-template-columns: 1fr; }
}
```

**图表区域**：
```css
/* 桌面端 */
.charts-grid { grid-template-columns: 1fr 380px; }

/* 平板端 */
@media (max-width: 1400px) {
    .charts-grid { grid-template-columns: 1fr; }
    .right-panel { grid-template-columns: 1fr 1fr; }
}

/* 移动端 */
@media (max-width: 768px) {
    .right-panel { grid-template-columns: 1fr; }
}
```

**字号和间距缩放**：
```css
/* 移动端调整 */
.stat-card {
    padding: 16px;        /* 从24px → 16px */
    min-height: 120px;    /* 从140px → 120px */
}

.stat-value {
    font-size: 28px;      /* 从36px → 28px */
}

.chart-container {
    height: 280px;        /* 从350px → 280px */
}
```

---

## 实施步骤

### 步骤 1：导入主题文件

在 `@layout.html` 中添加：
```html
<link rel="stylesheet" type="text/css" href="/_/@default/@modern_theme.css" media="all"/>
```

### 步骤 2：更新现有页面

针对各个子模块（clusters、servers、users 等），应用统一的卡片样式：

```html
<!-- 集群列表页 -->
<div class="cluster-grid">
    <div class="chart-card" v-for="cluster in clusters">
        <div class="chart-header">
            <span class="chart-title">{{cluster.name}}</span>
        </div>
        <div class="cluster-stats">
            <!-- 集群信息 -->
        </div>
    </div>
</div>
```

### 步骤 3：优化模块页面

对每个主要模块进行优化：

**集群管理** (`clusters/`)
- 集群列表卡片化
- 统计信息现代化
- 响应式表格

**服务器管理** (`servers/`)
- 服务器卡片布局
- 流量统计图表
- 性能监控仪表板

**用户管理** (`users/`)
- 用户统计卡片
- 用户排行榜
- 活跃度图表

**节点管理** (`nodes/`)
- 节点状态卡片
- 负载均衡可视化
- 实时监控面板

### 步骤 4：测试响应式

在各种设备/浏览器宽度上测试：
- 桌面（1920px、1400px）
- 平板（1024px、768px）
- 手机（480px、375px）

---

## 常见问题

### Q1：如何自定义卡片颜色？

A：使用 CSS 变量：
```html
<div class="stat-card custom" style="--card-start: #e8f4ff; --card-end: #d4e8ff;">
    ...
</div>
```

### Q2：图表高度如何调整？

A：修改 `.chart-container` 或各设备的媒体查询：
```css
.chart-container { height: 400px; }  /* 更高 */
@media (max-width: 768px) {
    .chart-container { height: 300px; }
}
```

### Q3：如何添加新的统计卡片类型？

A：在 LESS 中添加新类：
```less
.stat-card.custom {
    --card-start: #your-color-1;
    --card-end: #your-color-2;
}
```

### Q4：响应式设计可以自定义断点吗？

A：可以，修改媒体查询值：
```css
@media (max-width: 1600px) { ... }  /* 更大的平板 */
```

### Q5：如何禁用卡片悬停效果？

A：添加 `.no-hover` 类：
```html
<div class="stat-card no-hover">
    ...
</div>
```

```css
.stat-card.no-hover:hover {
    transform: none;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
}
```

---

## 升级清单

- [ ] 导入 `@modern_theme.less` 文件
- [ ] 编译 LESS 为 CSS
- [ ] 更新 dashboard 页面
- [ ] 优化 clusters 模块
- [ ] 优化 servers 模块
- [ ] 优化 users 模块
- [ ] 优化 nodes 模块
- [ ] 优化 settings 模块
- [ ] 测试桌面端布局
- [ ] 测试平板端布局
- [ ] 测试移动端布局
- [ ] 验证所有链接和功能
- [ ] 性能测试

---

## 文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| @modern_theme.less | @default/ | 现代主题样式 |
| @modern_theme.css | @default/ | 编译后的 CSS |
| index_modern.html | @default/dashboard/ | 现代化 dashboard |
| design_guide.md | 项目根目录 | 本设计指南 |

---

**版本**: 1.0  
**更新日期**: 2026-03-18  
**维护者**: FreeCDN Team
