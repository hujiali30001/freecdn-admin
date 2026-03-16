package tasks

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteAction struct {
	actionutils.ParentAction
}

func (this *DeleteAction) RunPost(params struct {
	TaskId int64
}) {
	defer this.CreateLogInfo(codes.DNSTask_LogDeleteDNSTask, params.TaskId)

	_, err := this.RPC().DNSTaskRPC().DeleteDNSTask(this.AdminContext(), &pb.DeleteDNSTaskRequest{DnsTaskId: params.TaskId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
