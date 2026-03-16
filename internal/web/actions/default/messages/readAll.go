package messages

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type ReadAllAction struct {
	actionutils.ParentAction
}

func (this *ReadAllAction) RunPost(params struct{}) {
	// 创建日志
	defer this.CreateLogInfo(codes.Message_LogReadAll)

	_, err := this.RPC().MessageRPC().UpdateAllMessagesRead(this.AdminContext(), &pb.UpdateAllMessagesReadRequest{})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
