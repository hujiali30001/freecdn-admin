package confirm

import (
	"github.com/hujiali30001/freecdn-admin/internal/setup"
	"github.com/iwind/TeaGo/actions"
)

type Helper struct {
}

func (this *Helper) BeforeAction(actionPtr actions.ActionWrapper) (goNext bool) {
	if !setup.IsNewInstalled() {
		actionPtr.Object().RedirectURL("/")
		return false
	}
	return true
}
