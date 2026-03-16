// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package transfer

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type StatNodesAction struct {
	actionutils.ParentAction
}

func (this *StatNodesAction) RunPost(params struct{}) {
	countNodesResp, err := this.RPC().NodeRPC().CountAllEnabledNodesMatch(this.AdminContext(), &pb.CountAllEnabledNodesMatchRequest{ActiveState: 1})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	this.Data["countNodes"] = countNodesResp.Count

	this.Success()
}
