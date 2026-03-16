package health

import "github.com/iwind/TeaGo"

func init() {
	TeaGo.BeforeStart(func(server *TeaGo.Server) {
		server.
			Get("/health", new(HealthAction)).
			EndAll()
	})
}
