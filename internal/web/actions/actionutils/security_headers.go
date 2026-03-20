package actionutils

import (
	"net/http"

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

func ApplySecurityHeaders(header http.Header, frame string) {
	if len(frame) == 0 {
		frame = "SAMEORIGIN"
	}
	header.Set("X-Frame-Options", frame)
	header.Set("X-Content-Type-Options", "nosniff")
	header.Set("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
	header.Set("Referrer-Policy", "same-origin")
	header.Set("X-DNS-Prefetch-Control", "off")
	header.Set("Content-Security-Policy",
		"default-src 'self'; "+
			"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "+
			"style-src 'self' 'unsafe-inline'; "+
			"img-src 'self' data: blob:; "+
			"font-src 'self' data:; "+
			"connect-src 'self'; "+
			"frame-ancestors 'self'",
	)
}

func (this *SecurityHeaders) BeforeAction(actionPtr actions.ActionWrapper, paramName string) (goNext bool) {
	ApplySecurityHeaders(actionPtr.Object().ResponseWriter.Header(), "")
	return true
}
