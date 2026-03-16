package reverseProxy

import (
	"encoding/json"
	"errors"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/schedulingconfigs"
)

type SchedulingAction struct {
	actionutils.ParentAction
}

func (this *SchedulingAction) Init() {
	this.FirstMenu("scheduling")
}

func (this *SchedulingAction) RunGet(params struct {
	ServerId   int64
	LocationId int64
}) {
	reverseProxyResp, err := this.RPC().HTTPLocationRPC().FindAndInitHTTPLocationReverseProxyConfig(this.AdminContext(), &pb.FindAndInitHTTPLocationReverseProxyConfigRequest{LocationId: params.LocationId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	var reverseProxy = serverconfigs.NewReverseProxyConfig()
	err = json.Unmarshal(reverseProxyResp.ReverseProxyJSON, reverseProxy)
	if err != nil {
		this.ErrorPage(err)
		return
	}
	this.Data["reverseProxyId"] = reverseProxy.Id

	var schedulingCode = reverseProxy.FindSchedulingConfig().Code
	var schedulingMap = schedulingconfigs.FindSchedulingType(schedulingCode)
	if schedulingMap == nil {
		this.ErrorPage(errors.New("invalid scheduling code '" + schedulingCode + "'"))
		return
	}
	this.Data["scheduling"] = schedulingMap

	this.Show()
}
