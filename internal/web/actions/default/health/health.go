package health

import (
	"net/http"

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
	_, _ = this.ResponseWriter.Write([]byte(`{"status":"ok"}`))
}
