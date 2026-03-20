package helpers

import (
	"net/http"

	"github.com/hujiali30001/freecdn-admin/internal/configloaders"
	teaconst "github.com/hujiali30001/freecdn-admin/internal/const"
	"github.com/hujiali30001/freecdn-admin/internal/utils/numberutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/default/index/loginutils"
	"github.com/iwind/TeaGo/actions"
)

type UserShouldAuth struct {
	action *actions.ActionObject
}

func (this *UserShouldAuth) BeforeAction(actionPtr actions.ActionWrapper, paramName string) (goNext bool) {
	actionutils.ApplySecurityHeaders(actionPtr.Object().ResponseWriter.Header(), "")

	if teaconst.IsRecoverMode {
		actionPtr.Object().RedirectURL("/recover")
		return false
	}

	this.action = actionPtr.Object()

	// 检查请求是否合法
	if isEvilRequest(this.action.Request) {
		this.action.ResponseWriter.WriteHeader(http.StatusForbidden)
		return false
	}

	// 检测注入
	if !safeFilterRequest(this.action.Request) {
		this.action.ResponseWriter.WriteHeader(http.StatusForbidden)
		_, _ = this.action.ResponseWriter.Write([]byte("Denied By WAF"))
		return false
	}

	// 安全相关
	var action = this.action
	securityConfig, _ := configloaders.LoadSecurityConfig()
	if securityConfig != nil && len(securityConfig.Frame) > 0 {
		actionutils.ApplySecurityHeaders(action.ResponseWriter.Header(), securityConfig.Frame)
	}

	// 检查IP
	if !checkIP(securityConfig, loginutils.RemoteIP(action)) {
		action.ResponseWriter.WriteHeader(http.StatusForbidden)
		return false
	}

	// 检查请求
	if !checkRequestSecurity(securityConfig, action.Request) {
		action.ResponseWriter.WriteHeader(http.StatusForbidden)
		return false
	}

	return true
}

// StoreAdmin 存储用户名到SESSION
func (this *UserShouldAuth) StoreAdmin(adminId int64, remember bool, localSid string) {
	loginutils.SetCookie(this.action, remember)
	var session = this.action.Session()
	session.Write("adminId", numberutils.FormatInt64(adminId))
	session.Write("@fingerprint", loginutils.CalculateClientFingerprint(this.action))
	session.Write("@ip", loginutils.RemoteIP(this.action))
	session.Write("@localSid", localSid)
}

func (this *UserShouldAuth) IsUser() bool {
	return this.action.Session().GetInt("adminId") > 0
}

func (this *UserShouldAuth) AdminId() int {
	return this.action.Session().GetInt("adminId")
}

func (this *UserShouldAuth) Logout() {
	loginutils.UnsetCookie(this.action)
	this.action.Session().Delete()
}
