package groups

import (	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type SortAction struct {
	actionutils.ParentAction
}

func (this *SortAction) RunPost(params struct {
	GroupIds []int64
}) {
	// 创建日志
	defer this.CreateLogInfo(codes.ServerGroup_LogSortServerGroups)

	_, err := this.RPC().ServerGroupRPC().UpdateServerGroupOrders(this.AdminContext(), &pb.UpdateServerGroupOrdersRequest{ServerGroupIds: params.GroupIds})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
