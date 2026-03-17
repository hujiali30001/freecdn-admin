# FreeCDN 后续阶段工作规划

> 更新于 2026-03-17 | 当前完成版本：v0.9.2（UI 升级完成）

---

## 📋 短期工作规划（v0.9.3～v0.9.x）

### 🎨 Phase 3A：其他页面样式统一

**目标**：将设置页、表单页、弹窗等所有管理界面升级到统一的紫色系主题。

**涉及页面**：
- [ ] 系统设置页（`/settings/`）
- [ ] 用户管理页（`/users/`）
- [ ] 表单弹窗（`dialog`、`modal`）
- [ ] 按钮组件（Primary、Secondary、Danger）
- [ ] 选择框、输入框等表单控件

**工作量**：约 2-3 天

**技术细节**：
```less
// 按钮样式升级
.button.primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #ffffff;
  border: none;
  border-radius: 4px;
  padding: 10px 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
  }
}

// 表单控件样式升级
.form-control {
  border: 2px solid #e0e0e0;
  border-radius: 4px;
  padding: 10px 12px;
  font-size: 14px;
  
  &:focus {
    border-color: #667eea;
    box-shadow: 0 0 8px rgba(102, 126, 234, 0.2);
    outline: none;
  }
}

// 弹窗背景
.modal-backdrop {
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
}

.modal-content {
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
}
```

---

### 🔤 Phase 3B：字体和排版优化

**目标**：规范化整个系统的字体大小、字重、行高，提升排版一致性。

**工作内容**：
- [ ] 定义 CSS 变量（`--font-size-xs`、`--font-size-sm` 等）
- [ ] 规范化标题（h1～h6）字体大小
- [ ] 调整行高和字母间距（line-height、letter-spacing）
- [ ] 优化代码块和预格式文本
- [ ] 响应式字体大小（小屏幕缩小）

**参考标准**：
```less
// 字体大小级别
--font-size-xs: 12px;      // 辅助文字、label
--font-size-sm: 13px;      // 表格单元格
--font-size-base: 14px;    // 正文
--font-size-lg: 16px;      // 页面标题
--font-size-xl: 18px;      // 卡片标题
--font-size-2xl: 20px;     // 主标题

// 字重
--font-weight-light: 300;
--font-weight-normal: 400;
--font-weight-medium: 500;
--font-weight-semibold: 600;
--font-weight-bold: 700;

// 行高
--line-height-tight: 1.2;
--line-height-normal: 1.5;
--line-height-loose: 1.8;
```

**工作量**：约 1-2 天

---

### 🌙 Phase 3C：暗黑主题支持（可选）

**目标**：为管理后台实现暗黑主题，提高夜间用户体验。

**实现方案**：
```less
// 通过 CSS 变量和媒体查询实现
@media (prefers-color-scheme: dark) {
  :root {
    --bg-primary: #1a1a1a;
    --bg-secondary: #2d2d2d;
    --text-primary: #f0f0f0;
    --text-secondary: #a0a0a0;
    --border-color: #404040;
  }
}

// 或者通过 body class 切换
body.dark-theme {
  --bg-primary: #1a1a1a;
  --bg-secondary: #2d2d2d;
  // ...
}
```

**工作量**：约 3-4 天（评估中）

**优先级**：低（可延后）

---

## 📈 中期工作规划（v1.0.0 前的功能扩展）

### 🔍 Phase 4A：增强型搜索功能

**目标**：改进全系统搜索，支持跨页面快速查找（节点、服务、配置等）。

**功能需求**：
- [ ] 全局搜索框（快捷键 `/` 或 `Ctrl+K`）
- [ ] 搜索结果预览（实时显示匹配项）
- [ ] 搜索历史记录
- [ ] 高级过滤选项

**预期完成**：v0.10.0

---

### 📊 Phase 4B：节点实时监控面板

**目标**：实时展示各边缘节点的资源使用情况（CPU、内存、网络、流量等）。

**功能需求**：
- [ ] 节点在线/离线状态实时更新
- [ ] CPU、内存、磁盘使用率折线图
- [ ] 网络流量实时曲线（in/out）
- [ ] 告警提示（CPU > 80% 等）

**技术栈**：WebSocket + Chart.js / ECharts

**预期完成**：v0.11.0

---

### 📉 Phase 4C：流量分析图表优化

**目标**：升级流量统计和分析功能，提供更直观的数据可视化。

**改进方向**：
- [ ] 多维度流量分析（按地区、按时间、按协议等）
- [ ] 自定义时间范围选择
- [ ] 数据导出功能（CSV、PDF）
- [ ] 同比/环比对比分析

**预期完成**：v0.12.0

---

## 🏗️ 长期工作规划（v1.0.0 及以后）

### Phase 5：完整 Module 命名重构（v1.0.0）

**背景**：当前 go.mod 中还有部分遗留的 GoEdge 命名空间。

**目标**：
- [ ] 完全切断与 GoEdge 上游的依赖
- [ ] 所有内部 module 改为 `github.com/hujiali30001/freecdn-*` 命名

**当前状态**：
- ✅ EdgeCommon 已改为 `freecdn-common`
- ⏳ freecdn-api 和 freecdn-node 的自身 module 名仍未改（留到 v1.0.0）

**预期完成**：v1.0.0（2026 年中）

---

## 📅 发布时间表（估计）

| 版本 | 预计日期 | 关键内容 |
|------|---------|---------|
| v0.9.2 | ✅ 2026-03-17 | 阶段二 UI 升级（完成） |
| v0.9.3 | 2026-03-25 | Phase 3A 其他页面样式统一 |
| v0.9.4 | 2026-04-01 | Phase 3B 字体排版优化 |
| v0.10.0 | 2026-04-15 | Phase 4A 增强型搜索 |
| v0.11.0 | 2026-05-01 | Phase 4B 节点监控面板 |
| v0.12.0 | 2026-05-15 | Phase 4C 流量图表优化 |
| v1.0.0 | 2026-06-30 | Phase 5 完整 module 重构 |

---

## 🔍 立即可做的工作（优先级）

### 高优先级（下周内）
1. **其他页面样式统一** — 选择 3-5 个高频页面先行升级
2. **字体排版规范** — 定义 CSS 变量，整体梳理

### 中优先级（本月内）
1. **浏览器兼容性测试** — 确保 IE11 不崩溃（如支持）
2. **移动端响应式验证** — 小屏幕视觉检查
3. **表单验证和提示** — 改进用户反馈

### 低优先级（备选）
1. **暗黑主题** — 根据用户反馈决定
2. **高级搜索** — v0.10.0 时再做

---

## 技术债清单（已知）

| 项目 | 优先级 | 状态 |
|------|--------|------|
| Vue 2 → Vue 3 升级 | 低 | 评估中（不影响功能） |
| Semantic UI 替换 | 低 | 可选（当前已满足） |
| API 文档自动生成 | 中 | 待实现 |
| 单元测试覆盖 | 中 | 缺失 |
| 性能优化（code splitting） | 低 | 待评估 |

---

## 💡 建议和思路

### 关于 UI 升级的后续思路
1. **渐进式升级**：无需一次性改完所有页面，可分批进行
2. **保持风格统一**：所有新增页面都使用统一的紫色渐变主题
3. **用户反馈**：在 v0.9.3+ 中收集用户对 UI 的反馈
4. **性能考量**：监控 CSS 文件大小，避免过度设计

### 关于功能扩展的策略
1. **用户优先**：先做高频功能（搜索、监控）
2. **数据支撑**：搜集用户行为数据，优化排序
3. **可靠性第一**：确保所有新功能都经过充分测试
4. **向后兼容**：保持与现有部署的兼容性

---

## 📞 反馈收集

请在 GitHub Issues 中报告：
- UI/UX 问题
- 性能瓶颈
- 功能需求

---

*下一步行动*：选择 Phase 3A 作为优先任务，预计本周五前完成初版。

---

最后更新：2026-03-17 | 版本：v0.9.2
