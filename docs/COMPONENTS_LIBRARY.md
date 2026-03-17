# FreeCDN 组件库规范 v0.10.0

> 更新于 2026-03-18 | 所有组件遵循 DESIGN_SYSTEM.md 中的设计规范

---

## 目录

1. [按钮组件](#1-按钮-button)
2. [输入框组件](#2-输入框-input)
3. [表格组件](#3-表格-table)
4. [卡片组件](#4-卡片-card)
5. [导航组件](#5-导航-navigation)
6. [状态标签](#6-状态标签-badge--tag)
7. [表单组件](#7-表单组件-form)
8. [弹窗组件](#8-弹窗-modal--dialog)

---

## 1. 按钮 (Button)

### HTML 结构

```html
<!-- 主按钮 -->
<button class="btn btn-primary">确定</button>

<!-- 次按钮 -->
<button class="btn btn-secondary">取消</button>

<!-- 文字按钮 -->
<button class="btn btn-text">了解更多</button>

<!-- 危险按钮 -->
<button class="btn btn-danger">删除</button>

<!-- 不同尺寸 -->
<button class="btn btn-primary btn-sm">小按钮</button>
<button class="btn btn-primary btn-md">标准按钮</button>
<button class="btn btn-primary btn-lg">大按钮</button>

<!-- 禁用状态 -->
<button class="btn btn-primary" disabled>禁用</button>

<!-- 带图标 -->
<button class="btn btn-primary">
  <i class="icon-save"></i> 保存
</button>
```

### LESS 代码

```less
// 按钮基础样式
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: inherit;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.15s ease;
  white-space: nowrap;
  
  // 默认标准尺寸
  height: 40px;
  padding: 10px 16px;
  font-size: 14px;
  
  // 小尺寸
  &.btn-sm {
    height: 32px;
    padding: 8px 12px;
    font-size: 12px;
  }
  
  // 大尺寸
  &.btn-lg {
    height: 48px;
    padding: 12px 20px;
    font-size: 16px;
  }
  
  // 主按钮
  &.btn-primary {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    color: white;
    box-shadow: 0 1px 3px rgba(102, 126, 234, 0.2);
    
    &:hover:not(:disabled) {
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    &:active:not(:disabled) {
      transform: translateY(0);
      box-shadow: 0 1px 3px rgba(102, 126, 234, 0.2);
    }
    
    &:disabled {
      background: #cbd5e0;
      color: #718096;
      cursor: not-allowed;
      box-shadow: none;
    }
  }
  
  // 次按钮
  &.btn-secondary {
    background: white;
    color: #667eea;
    border: 1px solid #667eea;
    
    &:hover:not(:disabled) {
      background: rgba(102, 126, 234, 0.08);
      transform: translateY(-2px);
    }
    
    &:active:not(:disabled) {
      background: rgba(102, 126, 234, 0.15);
      transform: translateY(0);
    }
    
    &:disabled {
      background: #f7fafc;
      color: #cbd5e0;
      border-color: #cbd5e0;
      cursor: not-allowed;
    }
  }
  
  // 文字按钮
  &.btn-text {
    background: transparent;
    color: #667eea;
    
    &:hover:not(:disabled) {
      background: rgba(102, 126, 234, 0.08);
    }
    
    &:active:not(:disabled) {
      background: rgba(102, 126, 234, 0.15);
    }
    
    &:disabled {
      color: #cbd5e0;
      cursor: not-allowed;
    }
  }
  
  // 危险按钮
  &.btn-danger {
    background: #f56565;
    color: white;
    
    &:hover:not(:disabled) {
      background: #e53e3e;
      transform: translateY(-2px);
    }
    
    &:active:not(:disabled) {
      background: #c53030;
      transform: translateY(0);
    }
    
    &:disabled {
      background: #cbd5e0;
      color: #718096;
      cursor: not-allowed;
    }
  }
}
```

---

## 2. 输入框 (Input)

### HTML 结构

```html
<!-- 基础输入框 -->
<div class="form-group">
  <label class="form-label">用户名</label>
  <input type="text" class="form-input" placeholder="请输入用户名">
</div>

<!-- 错误状态 -->
<div class="form-group">
  <label class="form-label">邮箱 <span class="required">*</span></label>
  <input type="email" class="form-input is-error" placeholder="请输入邮箱">
  <div class="form-error">邮箱格式不正确</div>
</div>

<!-- 禁用状态 -->
<input type="text" class="form-input" placeholder="禁用输入框" disabled>

<!-- 带图标的输入框 -->
<div class="form-input-group">
  <i class="icon-search"></i>
  <input type="text" class="form-input" placeholder="搜索...">
</div>

<!-- 不同尺寸 -->
<input type="text" class="form-input form-input-sm" placeholder="小输入框">
<input type="text" class="form-input form-input-md" placeholder="标准输入框">
<input type="text" class="form-input form-input-lg" placeholder="大输入框">
```

### LESS 代码

```less
// 表单组
.form-group {
  margin-bottom: 16px;
  
  &:last-child {
    margin-bottom: 0;
  }
}

// 表单标签
.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #2d3748;
  margin-bottom: 8px;
  
  .required {
    color: #f56565;
    margin-left: 2px;
  }
}

// 输入框基础样式
.form-input {
  width: 100%;
  height: 40px;
  padding: 0 12px;
  font-size: 14px;
  font-family: inherit;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  color: #2d3748;
  transition: all 0.2s ease;
  
  &::placeholder {
    color: #cbd5e0;
  }
  
  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    background: white;
  }
  
  &:disabled {
    background: #f7fafc;
    color: #cbd5e0;
    cursor: not-allowed;
    border-color: #e2e8f0;
  }
  
  // 尺寸变体
  &.form-input-sm {
    height: 32px;
    padding: 0 10px;
    font-size: 12px;
  }
  
  &.form-input-lg {
    height: 44px;
    padding: 0 14px;
    font-size: 15px;
  }
  
  // 错误状态
  &.is-error {
    border-color: #f56565;
    
    &:focus {
      box-shadow: 0 0 0 3px rgba(245, 101, 101, 0.1);
      border-color: #f56565;
    }
  }
}

// 错误提示
.form-error {
  font-size: 12px;
  color: #f56565;
  margin-top: 4px;
}

// 带图标的输入框
.form-input-group {
  position: relative;
  display: flex;
  align-items: center;
  
  i {
    position: absolute;
    left: 12px;
    color: #cbd5e0;
    pointer-events: none;
    font-size: 16px;
  }
  
  .form-input {
    padding-left: 36px;
  }
}
```

---

## 3. 表格 (Table)

### HTML 结构

```html
<table class="table">
  <thead>
    <tr>
      <th>姓名</th>
      <th>邮箱</th>
      <th>状态</th>
      <th>操作</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>张三</td>
      <td>zhangsan@example.com</td>
      <td><span class="badge badge-success">活跃</span></td>
      <td>
        <button class="btn btn-text btn-sm">编辑</button>
        <button class="btn btn-text btn-sm">删除</button>
      </td>
    </tr>
    <tr class="is-active">
      <td>李四</td>
      <td>lisi@example.com</td>
      <td><span class="badge badge-warning">待审核</span></td>
      <td>
        <button class="btn btn-text btn-sm">编辑</button>
        <button class="btn btn-text btn-sm">删除</button>
      </td>
    </tr>
  </tbody>
</table>

<!-- 紧凑表格 -->
<table class="table table-compact">
  <!-- ... -->
</table>

<!-- 斑马条纹表格 -->
<table class="table table-striped">
  <!-- ... -->
</table>
```

### LESS 代码

```less
// 表格基础样式
.table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  font-size: 14px;
  
  // 表头
  thead {
    background: #f7fafc;
    border-bottom: 2px solid #667eea;
    
    th {
      padding: 12px 16px;
      text-align: left;
      font-weight: 600;
      color: #667eea;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      font-size: 12px;
      white-space: nowrap;
    }
  }
  
  // 表体
  tbody {
    tr {
      border-bottom: 1px solid #e2e8f0;
      transition: background-color 0.2s ease;
      
      &:hover {
        background-color: rgba(102, 126, 234, 0.08);
      }
      
      &.is-active {
        background-color: rgba(102, 126, 234, 0.15);
        border-left: 3px solid #667eea;
      }
    }
    
    td {
      padding: 12px 16px;
      color: #2d3748;
      vertical-align: middle;
    }
  }
  
  // 紧凑模式
  &.table-compact {
    font-size: 13px;
    
    th, td {
      padding: 8px 12px;
    }
  }
  
  // 斑马条纹
  &.table-striped tbody tr:nth-child(odd) {
    background: #f7fafc;
    
    &:hover {
      background-color: rgba(102, 126, 234, 0.1);
    }
  }
}
```

---

## 4. 卡片 (Card)

### HTML 结构

```html
<!-- 基础卡片 -->
<div class="card">
  <div class="card-header">
    <h3 class="card-title">卡片标题</h3>
  </div>
  <div class="card-body">
    <p>卡片内容</p>
  </div>
  <div class="card-footer">
    <button class="btn btn-primary btn-sm">确定</button>
  </div>
</div>

<!-- 无边框卡片 -->
<div class="card card-flat">
  <div class="card-body">内容</div>
</div>

<!-- 带颜色的卡片 -->
<div class="card card-success">
  <div class="card-body">成功消息</div>
</div>
```

### LESS 代码

```less
// 卡片基础样式
.card {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
}

// 卡片头部
.card-header {
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
  background: #f7fafc;
}

// 卡片标题
.card-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #2d3748;
}

// 卡片内容
.card-body {
  padding: 20px;
  color: #2d3748;
  
  p {
    margin: 0 0 12px 0;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

// 卡片底部
.card-footer {
  padding: 16px 20px;
  border-top: 1px solid #e2e8f0;
  background: #f7fafc;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

// 无边框卡片
.card.card-flat {
  background: #f7fafc;
  border: none;
  box-shadow: none;
  
  &:hover {
    transform: none;
    box-shadow: none;
  }
}

// 颜色变体
.card.card-success {
  border-left: 4px solid #48bb78;
}

.card.card-warning {
  border-left: 4px solid #ed8936;
}

.card.card-danger {
  border-left: 4px solid #f56565;
}

.card.card-info {
  border-left: 4px solid #4299e1;
}
```

---

## 5. 导航 (Navigation)

### 顶栏

```html
<header class="navbar">
  <div class="navbar-container">
    <div class="navbar-brand">
      <a href="/" class="brand-logo">FreeCDN</a>
    </div>
    
    <nav class="navbar-nav">
      <a href="#" class="nav-item active">首页</a>
      <a href="#" class="nav-item">文档</a>
      <a href="#" class="nav-item">关于</a>
    </nav>
    
    <div class="navbar-right">
      <div class="dropdown">
        <button class="btn btn-text">用户</button>
        <div class="dropdown-menu">
          <a href="#" class="dropdown-item">个人设置</a>
          <a href="#" class="dropdown-item">登出</a>
        </div>
      </div>
    </div>
  </div>
</header>
```

### 左侧菜单

```html
<aside class="sidebar">
  <nav class="menu">
    <a href="#" class="menu-item active">
      <i class="icon-dashboard"></i>
      <span>仪表盘</span>
    </a>
    
    <div class="menu-section">
      <div class="menu-section-title">管理</div>
      <a href="#" class="menu-item">
        <i class="icon-cluster"></i>
        <span>集群管理</span>
      </a>
      <a href="#" class="menu-item">
        <i class="icon-server"></i>
        <span>服务管理</span>
      </a>
    </div>
  </nav>
</aside>
```

### LESS 代码

```less
// 顶栏
.navbar {
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  height: 60px;
  display: flex;
  align-items: center;
}

.navbar-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
}

.navbar-brand {
  font-size: 18px;
  font-weight: 700;
  color: white;
  
  .brand-logo {
    color: white;
    text-decoration: none;
  }
}

.navbar-nav {
  display: flex;
  gap: 20px;
  flex: 1;
  margin-left: 40px;
  
  .nav-item {
    color: white;
    text-decoration: none;
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 4px;
    transition: all 0.2s ease;
    
    &:hover {
      background: rgba(255, 255, 255, 0.1);
    }
    
    &.active {
      background: rgba(255, 255, 255, 0.2);
      font-weight: 600;
    }
  }
}

// 左侧菜单
.sidebar {
  width: 240px;
  background: #2d1b69;
  color: white;
  padding: 20px 0;
  position: fixed;
  height: calc(100vh - 60px);
  overflow-y: auto;
}

.menu {
  display: flex;
  flex-direction: column;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  color: white;
  text-decoration: none;
  font-size: 14px;
  border-left: 3px solid transparent;
  transition: all 0.2s ease;
  
  i {
    font-size: 16px;
    width: 20px;
    text-align: center;
  }
  
  &:hover {
    background: rgba(102, 126, 234, 0.1);
  }
  
  &.active {
    background: rgba(102, 126, 234, 0.15);
    border-left-color: #667eea;
    color: #667eea;
    font-weight: 600;
  }
}

.menu-section-title {
  padding: 8px 20px;
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-top: 8px;
  margin-bottom: 8px;
}
```

---

## 6. 状态标签 (Badge / Tag)

### HTML 结构

```html
<!-- 基础标签 -->
<span class="badge badge-info">标签</span>
<span class="badge badge-success">成功</span>
<span class="badge badge-warning">警告</span>
<span class="badge badge-danger">危险</span>

<!-- 大小变体 -->
<span class="badge badge-sm badge-info">小</span>
<span class="badge badge-lg badge-info">大</span>

<!-- 可关闭标签 -->
<span class="badge badge-primary">
  标签
  <button class="badge-close" aria-label="关闭">×</button>
</span>
```

### LESS 代码

```less
.badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  border-radius: 12px;
  white-space: nowrap;
  background: #e2e8f0;
  color: #2d3748;
  
  // 颜色变体
  &.badge-info {
    background: rgba(102, 126, 234, 0.1);
    color: #667eea;
  }
  
  &.badge-success {
    background: rgba(72, 187, 120, 0.1);
    color: #48bb78;
  }
  
  &.badge-warning {
    background: rgba(237, 137, 54, 0.1);
    color: #ed8936;
  }
  
  &.badge-danger {
    background: rgba(245, 101, 101, 0.1);
    color: #f56565;
  }
  
  // 尺寸变体
  &.badge-sm {
    padding: 2px 8px;
    font-size: 11px;
  }
  
  &.badge-lg {
    padding: 6px 12px;
    font-size: 13px;
  }
}

.badge-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  padding: 0 2px;
  line-height: 1;
  color: inherit;
  opacity: 0.7;
  transition: opacity 0.2s ease;
  
  &:hover {
    opacity: 1;
  }
}
```

---

## 参考

- 所有组件遵循 DESIGN_SYSTEM.md 中定义的设计规范
- 颜色使用 DESIGN_SYSTEM.md 中的 10.1 节中定义的 CSS 变量
- 动画和过渡使用 DESIGN_SYSTEM.md 中的 7. 动画和过渡 规范
