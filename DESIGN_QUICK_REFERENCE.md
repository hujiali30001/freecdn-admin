<!-- 快速参考：FreeCDN 现代化设计系统 -->

# 🎨 设计系统快速参考

## 颜色速查表

### 主要颜色
```
主背景渐变：#f5f7ff → #f0f5ff
侧边栏渐变：#c5d0f5 → #d8c8f0
```

### 文字颜色
```
主标题（h1, h2）：#1a202c (font-weight: 700)
正文（p, div）：#2d3748 (font-weight: 600)
次级（small, label）：#4a5568 (font-weight: 600)
辅助（hint, disabled）：#718096 (font-weight: 500)
```

### 卡片颜色
```css
集群卡片：linear-gradient(135deg, #d4e5f9 0%, #c5d8f5 100%)
节点卡片：linear-gradient(135deg, #e5d8f9 0%, #d8c8f5 100%)
用户卡片：linear-gradient(135deg, #f9e5ec 0%, #f5d8e3 100%)
服务器卡片：linear-gradient(135deg, #f0e5f9 0%, #e5d8f5 100%)
```

### 功能颜色
```
成功（在线）：#21ba45
错误（离线）：#db2828
警告：#ff851b
信息：#4183c4
```

---

## 组件样式速查

### 统计卡片
```html
<div class="stat-card cluster">
    <div>
        <div class="stat-title">集群</div>
        <div class="stat-value">12</div>
    </div>
    <div class="stat-desc">全球分布式集群</div>
</div>
```

**CSS 属性**：
- 背景：linear-gradient(135deg, ...)
- 圆角：20px
- 内边距：24px
- 最小高度：140px
- 阴影：0 8px 24px rgba(0, 0, 0, 0.05)
- Hover：transform: translateY(-4px)

**类型变量**：
- `.cluster` - 蓝色
- `.node` - 紫色
- `.user` - 粉色
- `.server` - 薰衣草色

---

### 卡片容器
```html
<div class="chart-card">
    <div class="chart-header">
        <span class="chart-title">标题</span>
        <span class="chart-subtitle">副标题</span>
    </div>
    <div id="chart" class="chart-container"></div>
</div>
```

**CSS 属性**：
- 背景：white
- 圆角：20px
- 内边距：24px
- 阴影：0 8px 24px rgba(0, 0, 0, 0.05)
- 边框：1px solid rgba(226, 232, 240, 0.6)

---

### 网格布局

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

**右侧面板**（平板端）：
```css
.right-panel {
    grid-template-columns: 1fr 1fr;
}
```

---

## 响应式断点

| 设备 | 宽度 | 统计卡片 | 图表 | 说明 |
|------|------|---------|------|------|
| 桌面 | >1400px | 4列 | 1fr 380px | 完整显示 |
| 平板 | 768-1400px | 2列 | 1fr | 图表单列 |
| 手机 | <768px | 1列 | 1fr | 全屏显示 |
| 超小 | <480px | 1列 | 1fr | 字号缩小 |

### 媒体查询代码片段

```css
/* 平板端 */
@media (max-width: 1400px) {
    .stats-grid { grid-template-columns: repeat(2, 1fr); }
    .charts-grid { grid-template-columns: 1fr; }
    .right-panel { grid-template-columns: 1fr 1fr; }
}

/* 移动端 */
@media (max-width: 768px) {
    .stats-grid { 
        grid-template-columns: 1fr; 
        gap: 15px;
    }
    .stat-card { 
        padding: 16px; 
        min-height: 120px;
    }
    .chart-card { padding: 16px; }
    .chart-container { height: 280px; }
    .right-panel { grid-template-columns: 1fr; }
}

/* 超小屏 */
@media (max-width: 480px) {
    .chart-container { height: 240px; }
}
```

---

## 字号系统

| 用途 | 大小 | 字重 | 用例 |
|------|------|------|------|
| 页面标题 | 28px | 700 | 主标题 |
| 卡片标题 | 18px | 700 | 图表、卡片头部 |
| 组件标题 | 16px | 700 | 小标题、数据 |
| 正文 | 14px | 600 | 常规文本 |
| 标签 | 13px | 600 | 表单标签、说明 |
| 描述 | 12px | 500 | 辅助文字 |
| 提示 | 11px | 500 | 很小的文字 |

---

## 间距系统

```
超大：24px    (卡片间距)
大：20px      (卡片内间距、网格间距)
中：16px      (组件间距、移动端卡片间距)
小：12px      (小组件间距)
微小：8px     (表单间距、按钮间距)
```

---

## 圆角系统

```
圆角大：20px   (卡片)
圆角中：12px   (输入框、按钮)
圆角小：8px    (标签、小按钮)
圆角微小：4px  (边框、细节)
```

---

## 阴影系统

```
软阴影：0 8px 24px rgba(0, 0, 0, 0.05)      (卡片默认)
中等阴影：0 12px 32px rgba(0, 0, 0, 0.08)   (卡片 Hover)
轻阴影：0 4px 12px rgba(139, 159, 240, 0.3) (按钮 Hover)
无阴影：none                                (某些情况)
```

---

## 常用 CSS 类

```css
/* 卡片 */
.stat-card         /* 统计卡片 */
.chart-card        /* 图表卡片 */
.stat-card.cluster /* 集群卡片 */
.stat-card.node    /* 节点卡片 */
.stat-card.user    /* 用户卡片 */
.stat-card.server  /* 服务器卡片 */

/* 网格 */
.stats-grid        /* 统计卡片网格 */
.charts-grid       /* 图表网格 */
.right-panel       /* 右侧面板 */

/* 文字 */
.stat-title        /* 卡片标题 */
.stat-value        /* 卡片数值 */
.stat-desc         /* 卡片描述 */
.chart-title       /* 图表标题 */
.chart-subtitle    /* 图表副标题 */

/* 进度 */
.progress-bar      /* 进度条容器 */
.progress-fill     /* 进度条填充 */
.progress-item     /* 单个进度项 */
.progress-header   /* 进度标题 */
```

---

## 常用 CSS 属性组合

### 默认卡片
```css
background: white;
border-radius: 20px;
padding: 24px;
box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
border: 1px solid rgba(226, 232, 240, 0.6);
transition: all 0.3s ease;
```

### Hover 效果（卡片）
```css
transform: translateY(-4px);
box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
```

### 输入框焦点
```css
border-color: #8b9ff0;
box-shadow: 0 0 0 3px rgba(139, 159, 240, 0.1);
outline: none;
```

### 按钮基础
```css
padding: 10px 20px;
border-radius: 8px;
font-weight: 600;
cursor: pointer;
transition: all 0.3s ease;
border: none;
```

### 按钮主色 Hover
```css
background: linear-gradient(135deg, #8b9ff0 0%, #a88be8 100%);
transform: translateY(-2px);
box-shadow: 0 4px 12px rgba(139, 159, 240, 0.3);
```

---

## 快速复制代码

### 统计卡片示例
```html
<div class="stats-grid">
    <div class="stat-card cluster">
        <div>
            <div class="stat-title">集群</div>
            <div class="stat-value">12</div>
        </div>
        <div class="stat-desc">全球分布式集群</div>
    </div>
</div>

<style>
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 20px;
}

.stat-card {
    background: linear-gradient(135deg, var(--card-start) 0%, var(--card-end) 100%);
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
    transition: all 0.3s ease;
    min-height: 140px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}

.stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.stat-card.cluster {
    --card-start: #d4e5f9;
    --card-end: #c5d8f5;
}
</style>
```

### 图表卡片示例
```html
<div class="chart-card">
    <div class="chart-header">
        <span class="chart-title">实时流量趋势</span>
        <span class="chart-subtitle">（24小时）</span>
    </div>
    <div id="chart" class="chart-container"></div>
</div>

<style>
.chart-card {
    background: white;
    border-radius: 20px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(226, 232, 240, 0.6);
    display: flex;
    flex-direction: column;
}

.chart-container {
    width: 100%;
    height: 350px;
    flex: 1;
}
</style>
```

---

## 开发工作流

1. **导入样式**
   ```html
   <link rel="stylesheet" href="/_/@default/@modern_theme.css">
   ```

2. **使用组件**
   ```html
   <div class="stat-card cluster">...</div>
   <div class="chart-card">...</div>
   ```

3. **自定义颜色**
   ```html
   <div class="stat-card custom" style="
       --card-start: #your-color-1;
       --card-end: #your-color-2;">
   </div>
   ```

4. **响应式测试**
   - 桌面：1920px、1400px
   - 平板：1024px、768px
   - 手机：480px、375px

5. **性能检查**
   - 使用开发工具检查重排
   - 监控 CSS 文件大小
   - 测试动画流畅度

---

## 常见问题速解

**Q: 卡片 Hover 动画不工作？**
```css
确保有 transition: all 0.3s ease;
```

**Q: 响应式在某设备显示错乱？**
```css
检查媒体查询顺序，应从小到大（Mobile First）
```

**Q: 字号在移动端太小？**
```css
在 @media (max-width: 768px) 中增大字号
```

**Q: 卡片间距太挤？**
```css
增加 gap 值：gap: 24px; (从 20px)
```

**Q: 渐变颜色不对？**
```css
检查 linear-gradient 方向和颜色值
```

---

**快速参考版本**: 1.0  
**更新日期**: 2026-03-18  
**维护者**: FreeCDN Team
