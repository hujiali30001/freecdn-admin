package users

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteAction struct {
	actionutils.ParentAction
}

func (this *DeleteAction) RunPost(params struct {
	UserId int64
}) {
	defer this.CreateLogInfo(codes.ACMEUser_LogDeleteACMEUser, params.UserId)

	countResp, err := this.RPC().ACMETaskRPC().CountAllEnabledACMETasksWithACMEUserId(this.AdminContext(), &pb.CountAllEnabledACMETasksWithACMEUserIdRequest{AcmeUserId: params.UserId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	if countResp.Count > 0 {
		this.Fail("有任务正在和这个用户关联，所以不能删除")
	}

	_, err = this.RPC().ACMEUserRPC().DeleteACMEUser(this.AdminContext(), &pb.DeleteACMEUserRequest{AcmeUserId: params.UserId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
