package node

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

// 手动上线
type UpAction struct {
	actionutils.ParentAction
}

func (this *UpAction) RunPost(params struct {
	NodeId int64
}) {
	defer this.CreateLogInfo(codes.Node_LogUpNode, params.NodeId)

	_, err := this.RPC().NodeRPC().UpdateNodeUp(this.AdminContext(), &pb.UpdateNodeUpRequest{
		NodeId: params.NodeId,
		IsUp:   true,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
