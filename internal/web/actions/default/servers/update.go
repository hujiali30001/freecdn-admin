package servers

import "github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"

type UpdateAction struct {
	actionutils.ParentAction
}

func (this *UpdateAction) Init() {
	this.Nav("", "", "")
}

func (this *UpdateAction) RunGet(params struct{}) {
	this.Show()
}
