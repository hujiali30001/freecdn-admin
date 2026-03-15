package reverseProxy

import (
	"github.com/hujiali30001/freecdn-admin/internal/configloaders"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/default/servers/server/settings/locations/locationutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/default/servers/serverutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/iwind/TeaGo"
)

func init() {
	TeaGo.BeforeStart(func(server *TeaGo.Server) {
		server.
			Helper(helpers.NewUserMustAuth(configloaders.AdminModuleCodeServer)).
			Helper(locationutils.NewLocationHelper()).
			Helper(serverutils.NewServerHelper()).
			Data("mainTab", "setting").
			Data("tinyMenuItem", "reverseProxy").
			Prefix("/servers/server/settings/locations/reverseProxy").
			Get("", new(IndexAction)).
			GetPost("/scheduling", new(SchedulingAction)).
			GetPost("/setting", new(SettingAction)).
			EndAll()
	})
}
