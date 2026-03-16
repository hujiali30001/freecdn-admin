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
	defer this.CreateLogInfo(codes.User_LogDeleteUser, params.UserId)

	// TODO 检查用户是否有未完成的业务

	_, err := this.RPC().UserRPC().DeleteUser(this.AdminContext(), &pb.DeleteUserRequest{UserId: params.UserId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
