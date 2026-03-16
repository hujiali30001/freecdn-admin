// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .

package cache

import (
	"github.com/hujiali30001/freecdn-admin/internal/rpc"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

func InitMenu(parent *actionutils.ParentAction) error {
	rpcClient, err := rpc.SharedRPC()
	if err != nil {
		return err
	}

	countTasksResp, err := rpcClient.HTTPCacheTaskRPC().CountDoingHTTPCacheTasks(parent.AdminContext(), &pb.CountDoingHTTPCacheTasksRequest{})
	if err != nil {
		return err
	}

	parent.Data["countDoingTasks"] = countTasksResp.Count
	return nil
}
