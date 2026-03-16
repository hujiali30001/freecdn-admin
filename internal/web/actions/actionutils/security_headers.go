package actionutils

import (
	"github.com/iwind/TeaGo/actions"
)

// SecurityHeaders 是一个 TeaGo BeforeAction Filter，
// 向所有响应自动注入安全响应头（ORA-13）。
//
// 注册方式（在 admin_node.go 的 TeaGo.NewServer 调用链中添加）：
//
//	TeaGo.NewServer(false).
//	    ...
//	    AddFilter(new(actionutils.SecurityHeaders)).
//	    Start()
type SecurityHeaders struct {
}

func (this *SecurityHeaders) BeforeAction(actionPtr actions.ActionWrapper, paramName string) (goNext bool) {
	w := actionPtr.Object().ResponseWriter

	// 防止页面被嵌入 iframe（点击劫持防护）
	w.Header().Set("X-Frame-Options", "SAMEORIGIN")

	// 禁止 MIME 嗅探
	w.Header().Set("X-Content-Type-Options", "nosniff")

	// 强制 HTTPS（如已启用 HTTPS，浏览器后续 1 年内不降级；HTTP 模式下设置无害）
	w.Header().Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")

	// 限制 Referrer 泄露（只向同域发送完整 referrer）
	w.Header().Set("Referrer-Policy", "same-origin")

	// 禁止浏览器推测性预加载
	w.Header().Set("X-DNS-Prefetch-Control", "off")

	// 内容安全策略（管理后台：只允许同源 + 内联脚本/样式）
	// 注意：GoEdge 原有大量内联脚本/样式，此处宽松策略保持兼容
	w.Header().Set("Content-Security-Policy",
		"default-src 'self'; "+
			"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "+
			"style-src 'self' 'unsafe-inline'; "+
			"img-src 'self' data: blob:; "+
			"font-src 'self' data:; "+
			"connect-src 'self'; "+
			"frame-ancestors 'self'",
	)

	return true
}
