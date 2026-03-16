// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .

package cache

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteTaskAction struct {
	actionutils.ParentAction
}

func (this *DeleteTaskAction) RunPost(params struct {
	TaskId int64
}) {
	defer this.CreateLogInfo(codes.HTTPCacheTask_LogDeleteHTTPCacheTask, params.TaskId)

	_, err := this.RPC().HTTPCacheTaskRPC().DeleteHTTPCacheTask(this.AdminContext(), &pb.DeleteHTTPCacheTaskRequest{
		HttpCacheTaskId: params.TaskId,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
