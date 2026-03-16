package tasks

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteBatchAction struct {
	actionutils.ParentAction
}

func (this *DeleteBatchAction) RunPost(params struct {
	TaskIds []int64
}) {
	defer this.CreateLogInfo(codes.NodeTask_LogDeleteNodeTasksBatch)

	_, err := this.RPC().NodeTaskRPC().DeleteNodeTasks(this.AdminContext(), &pb.DeleteNodeTasksRequest{NodeTaskIds: params.TaskIds})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
