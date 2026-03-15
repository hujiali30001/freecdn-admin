package about

import "github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"

type QqAction struct {
	actionutils.ParentAction
}

func (this *QqAction) Init() {
	this.Nav("", "", "")
}

func (this *QqAction) RunGet(params struct{}) {
	this.Show()
}
