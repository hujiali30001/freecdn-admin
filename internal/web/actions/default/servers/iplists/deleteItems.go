// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package iplists

import (
	"strings"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/types"
)

type DeleteItemsAction struct {
	actionutils.ParentAction
}

func (this *DeleteItemsAction) RunPost(params struct {
	ItemIds []int64
}) {
	if len(params.ItemIds) == 0 {
		this.Success()
	}

	var itemIdStrings = []string{}
	for _, itemId := range params.ItemIds {
		itemIdStrings = append(itemIdStrings, types.String(itemId))
	}

	defer this.CreateLogInfo(codes.IPList_LogDeleteIPBatch, strings.Join(itemIdStrings, ", "))

	_, err := this.RPC().IPItemRPC().DeleteIPItems(this.AdminContext(), &pb.DeleteIPItemsRequest{IpItemIds: params.ItemIds})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	// 通知左侧菜单Badge更新
	helpers.NotifyIPItemsCountChanges()

	this.Success()
}
