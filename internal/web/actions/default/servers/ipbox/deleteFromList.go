// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package ipbox

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteFromListAction struct {
	actionutils.ParentAction
}

func (this *DeleteFromListAction) RunPost(params struct {
	ListId int64
	ItemId int64
}) {
	defer this.CreateLogInfo(codes.IPItem_LogDeleteIPItem, params.ListId, params.ItemId)

	_, err := this.RPC().IPItemRPC().DeleteIPItem(this.AdminContext(), &pb.DeleteIPItemRequest{IpItemId: params.ItemId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
