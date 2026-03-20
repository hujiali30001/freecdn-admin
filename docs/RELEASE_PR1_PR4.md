# FreeCDN 控制面发布说明（PR-1 ~ PR-4）

## 1. 发布目标

本次发布聚焦四类问题：

- 安全止血：默认弱口令、未授权访问、信息暴露。
- 稳定性治理：关键路径吞错、外部请求阻塞。
- 性能优化：地区选择类 N+1 RPC、下载链路无效调用。
- 可维护性重构：源站新增/更新重复逻辑、安全头注入策略分叉。

---

## 2. 变更摘要

### PR-1 安全止血

- `deploy/run-wsl.sh`：移除默认管理员密码，禁止明文回显密码。
- `install.sh`：初始管理员密码改为随机生成，写入 `600` 权限文件。
- `internal/web/actions/default/files/init.go`：`/files/file` 补齐登录鉴权。
- `internal/web/actions/default/health/health.go`：`/health` 收敛为最小响应，仅返回 `{"status":"ok"}`。

### PR-2 稳定性与错误治理

- `internal/web/actions/default/settings/updates/index.go`：
  - 外部更新请求增加超时与状态码校验。
  - 响应读取增加大小上限。
- `internal/tasks/task_check_updates.go`：同上，后台自动检查链路同步治理。
- `internal/utils/upgrade_manager.go`：版本元数据读取增加上限，降低内存放大风险。
- `internal/web/actions/default/settings/updates/upgrade.go`：
  - 升级数据库失败、重启失败显式返回错误。
  - 修复 ticker 生命周期管理。
- `internal/nodes/admin_node.go`：会话初始化失败不再进程级致命退出。

### PR-3 性能与 N+1 优化

- `internal/web/actions/default/ui/selectCountriesPopup.go`：
  - 提交回显从逐条查询改为单次列表查询+本地映射。
- `internal/web/actions/default/ui/selectProvincesPopup.go`：
  - 提交回显从逐条查询改为单次列表查询+本地映射。
- `internal/web/actions/default/settings/security/index.go`：
  - 国家/省份回显改为单次列表查询+本地映射。
- `internal/web/actions/default/files/file.go`、`internal/web/actions/default/ui/image.go`：
  - 复用上下文/RPC对象，写出失败快速终止后续调用。

### PR-4 可维护性重构

- `internal/web/actions/default/servers/server/settings/origins/origin_shared.go`：
  - 新增共享逻辑，统一处理地址校验、超时序列化、证书引用、域名规范化。
- `internal/web/actions/default/servers/server/settings/origins/addPopup.go`
- `internal/web/actions/default/servers/server/settings/origins/updatePopup.go`
  - 新增/更新流程复用共享逻辑，减少重复与行为漂移。
- `internal/web/actions/actionutils/security_headers.go`：
  - 提供统一 `ApplySecurityHeaders` 入口。
- `internal/web/actions/actionutils/parent_action.go`
- `internal/web/helpers/user_must_auth.go`
- `internal/web/helpers/user_should_auth.go`
  - 安全头策略统一调用同一函数，避免多处实现不一致。

---

## 3. 风险与兼容性说明

### 安全行为变化

- WSL 启动脚本不再接受空密码；需要显式传入 `ADMIN_PASSWORD`。
- `/files/file` 现在需要登录会话，未登录将被拦截。
- `/health` 不再返回服务名与版本字段。

### 运行行为变化

- 更新检查对外部源增加请求超时，弱网络下会更快失败返回。
- 升级流程中的数据库升级与重启失败会前端可见，不再静默吞错。

### 重构风险点

- 源站新增/更新使用共享函数后，地址与端口校验逻辑一致化。
- 安全头统一入口后，若后续新增头策略需在一个函数内统一调整。

---

## 4. 回滚方案

建议按“文件集”回滚，保持 PR 粒度：

- 回滚 PR-4：恢复 `origins` 共享抽取与安全头统一入口相关文件。
- 回滚 PR-3：恢复地区选择与安全设置页面的映射优化。
- 回滚 PR-2：恢复更新检查与升级流程的超时/错误处理策略。
- 回滚 PR-1：恢复脚本与鉴权/健康检查行为。

建议保留回滚顺序：**PR-4 -> PR-3 -> PR-2 -> PR-1**，每次回滚后执行“上线后检查清单”中的关键项复验。

---

## 5. 上线前检查清单

- [ ] 确认部署环境已设置 `ADMIN_PASSWORD`（WSL/脚本场景）。
- [ ] 确认 `/files/file` 访问路径依赖的前端流程已在登录态执行。
- [ ] 确认外部更新源可访问，或接受超时快速失败行为。
- [ ] 确认运维值班知晓：升级失败与重启失败会直接可见。
- [ ] 确认无自定义逻辑依赖 `/health` 的旧字段（service/version）。

---

## 6. 上线后检查清单

- [ ] 检查健康探针：`/health` 返回 `200` 且响应体为 `{"status":"ok"}`。
- [ ] 未登录访问 `/files/file` 返回未授权（预期被拦截）。
- [ ] 登录后文件下载与图片加载正常，无异常中断。
- [ ] 进入“安全设置”页面，国家/省份回显正常且加载更快。
- [ ] 源站新增/更新（HTTP/HTTPS/OSS）流程可正常保存并回显。
- [ ] 手动触发更新检查，网络异常时可在超时后快速返回失败信息。

---

## 7. 验证命令记录

建议在发布分支执行以下命令并保留日志：

- `go test ./internal/web/actions/default/files ./internal/web/actions/default/health`
- `go test ./internal/web/actions/default/settings/updates ./internal/tasks`
- `go test ./internal/utils ./internal/nodes`
- `go test ./internal/web/actions/default/ui ./internal/web/actions/default/settings/security ./internal/web/actions/default/files`
- `go test ./internal/web/actions/default/servers/server/settings/origins ./internal/web/actions/actionutils ./internal/web/helpers`
- `go test ./cmd/...`

