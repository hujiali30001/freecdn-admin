// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package iplists

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteAction struct {
	actionutils.ParentAction
}

func (this *DeleteAction) RunPost(params struct {
	ListId int64
}) {
	defer this.CreateLogInfo(codes.IPList_LogDeleteIPList, params.ListId)

	// 删除
	_, err := this.RPC().IPListRPC().DeleteIPList(this.AdminContext(), &pb.DeleteIPListRequest{IpListId: params.ListId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	// 通知左侧菜单Badge更新
	helpers.NotifyIPItemsCountChanges()

	this.Success()
}
