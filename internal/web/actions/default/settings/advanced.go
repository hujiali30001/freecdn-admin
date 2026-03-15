package settings

import "github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"

type AdvancedAction struct {
	actionutils.ParentAction
}

func (this *AdvancedAction) Init() {
	this.Nav("", "", "")
}

func (this *AdvancedAction) RunGet(params struct{}) {
	// 跳转到高级设置的第一个Tab
	this.RedirectURL("/settings/database")
}
