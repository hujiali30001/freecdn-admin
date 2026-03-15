package waf

import "github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"

type TestAction struct {
	actionutils.ParentAction
}

func (this *TestAction) Init() {
	this.Nav("", "", "test")
}

func (this *TestAction) RunGet(params struct{}) {
	this.Show()
}
