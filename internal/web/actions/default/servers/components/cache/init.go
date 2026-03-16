package cache

import (
	"github.com/hujiali30001/freecdn-admin/internal/configloaders"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/iwind/TeaGo"
)

func init() {
	TeaGo.BeforeStart(func(server *TeaGo.Server) {
		server.
			Helper(helpers.NewUserMustAuth(configloaders.AdminModuleCodeServer)).
			Helper(NewHelper()).
			Data("teaMenu", "servers").
			Data("teaSubMenu", "cache").
			Prefix("/servers/components/cache").
			Get("", new(IndexAction)).
			GetPost("/createPopup", new(CreatePopupAction)).
			Get("/policy", new(PolicyAction)).
			GetPost("/update", new(UpdateAction)).
			GetPost("/clean", new(CleanAction)).
			GetPost("/fetch", new(FetchAction)).
			GetPost("/purge", new(PurgeAction)).
			GetPost("/stat", new(StatAction)).
			GetPost("/test", new(TestAction)).
			Post("/delete", new(DeleteAction)).
			Post("/testRead", new(TestReadAction)).
			Post("/testWrite", new(TestWriteAction)).
			Get("/selectPopup", new(SelectPopupAction)).
			Post("/count", new(CountAction)).
			Post("/updateRefs", new(UpdateRefsAction)).
			EndAll()
	})
}
