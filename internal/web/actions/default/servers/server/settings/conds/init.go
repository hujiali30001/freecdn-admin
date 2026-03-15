package conds

import (
	"github.com/hujiali30001/freecdn-admin/internal/configloaders"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/iwind/TeaGo"
)

func init() {
	TeaGo.BeforeStart(func(server *TeaGo.Server) {
		server.
			Helper(helpers.NewUserMustAuth(configloaders.AdminModuleCodeServer)).
			Prefix("/servers/server/settings/conds").
			GetPost("/addGroupPopup", new(AddGroupPopupAction)).
			GetPost("/addCondPopup", new(AddCondPopupAction)).
			EndAll()
	})
}
