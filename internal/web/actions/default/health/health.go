package health

import (
	"encoding/json"
	"net/http"

	teaconst "github.com/hujiali30001/freecdn-admin/internal/const"
	"github.com/iwind/TeaGo/actions"
)

// HealthAction provides a /health endpoint for liveness probes.
// No authentication is required.
type HealthAction struct {
	actions.ActionObject
}

func (this *HealthAction) RunGet(_ struct{}) {
	this.ResponseWriter.Header().Set("Content-Type", "application/json; charset=utf-8")
	this.ResponseWriter.WriteHeader(http.StatusOK)
	data, _ := json.Marshal(map[string]string{
		"status":  "ok",
		"service": "freecdn-admin",
		"version": teaconst.Version,
	})
	_, _ = this.ResponseWriter.Write(data)
}
