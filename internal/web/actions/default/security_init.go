// Package default 全局安全响应头注入
// 在所有路由注册之前，通过 TeaGo.BeforeStart 挂载 SecurityHeaders helper。
// 由于 Go 的 init() 执行顺序是包导入顺序，此文件需要被 admin_node.go import。
package default_

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/iwind/TeaGo"
)

func init() {
	TeaGo.BeforeStart(func(server *TeaGo.Server) {
		server.
			Prefix("").
			Helper(new(actionutils.SecurityHeaders)).
			EndAll()
	})
}
