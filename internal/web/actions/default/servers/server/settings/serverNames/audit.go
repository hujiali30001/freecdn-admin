package serverNames

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

// 审核域名
type AuditAction struct {
	actionutils.ParentAction
}

func (this *AuditAction) RunPost(params struct {
	ServerId       int64
	AuditingOK     bool
	AuditingReason string

	CSRF *actionutils.CSRF
}) {
	defer this.CreateLogInfo(codes.Server_LogSubmitAuditingServer, params.ServerId)

	if !params.AuditingOK && len(params.AuditingReason) == 0 {
		this.FailField("auditingReason", "请输入审核不通过原因")
	}

	_, err := this.RPC().ServerRPC().UpdateServerNamesAuditing(this.AdminContext(), &pb.UpdateServerNamesAuditingRequest{
		ServerId: params.ServerId,
		AuditingResult: &pb.ServerNameAuditingResult{
			IsOk:   params.AuditingOK,
			Reason: params.AuditingReason,
		},
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
