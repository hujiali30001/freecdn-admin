// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package ipbox

import (
	"github.com/hujiali30001/freecdn-admin/internal/configloaders"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/iwind/TeaGo"
)

func init() {
	TeaGo.BeforeStart(func(server *TeaGo.Server) {
		server.
			Helper(helpers.NewUserMustAuth(configloaders.AdminModuleCodeServer)).
			Prefix("/servers/ipbox").
			Get("", new(IndexAction)).
			Post("/addIP", new(AddIPAction)).
			Post("/deleteFromList", new(DeleteFromListAction)).
			EndAll()
	})
}
