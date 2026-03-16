package utils

import (
	"fmt"
	"runtime/debug"

	"github.com/iwind/TeaGo/logs"
)

// Recover 捕获 goroutine panic，记录结构化日志。
// 使用方式：在 goroutine 顶部调用 defer utils.Recover()
func Recover() {
	e := recover()
	if e != nil {
		stack := debug.Stack()
		// 同时写入结构化日志和标准错误，方便容器环境的日志收集
		msg := fmt.Sprintf("[PANIC] %v\n%s", e, string(stack))
		logs.Error("[RECOVER]" + msg)
	}
}
