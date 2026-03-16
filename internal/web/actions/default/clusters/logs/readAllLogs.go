// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package logs

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type ReadAllLogsAction struct {
	actionutils.ParentAction
}

func (this *ReadAllLogsAction) RunPost(params struct {
	LogIds []int64
}) {
	_, err := this.RPC().NodeLogRPC().UpdateAllNodeLogsRead(this.AdminContext(), &pb.UpdateAllNodeLogsReadRequest{})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	// 通知左侧数字Badge更新
	helpers.NotifyNodeLogsCountChange()

	this.Success()
}
