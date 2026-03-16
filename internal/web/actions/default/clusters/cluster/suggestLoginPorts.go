// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package cluster

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type SuggestLoginPortsAction struct {
	actionutils.ParentAction
}

func (this *SuggestLoginPortsAction) RunPost(params struct {
	Host string
}) {
	portsResp, err := this.RPC().NodeLoginRPC().FindNodeLoginSuggestPorts(this.AdminContext(), &pb.FindNodeLoginSuggestPortsRequest{Host: params.Host})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	if len(portsResp.Ports) == 0 {
		this.Data["ports"] = []int32{}
	} else {
		this.Data["ports"] = portsResp.Ports
	}

	if len(portsResp.AvailablePorts) == 0 {
		this.Data["availablePorts"] = []int32{}
	} else {
		this.Data["availablePorts"] = portsResp.AvailablePorts
	}

	this.Success()
}
