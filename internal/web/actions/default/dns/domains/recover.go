package domains

import (	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type RecoverAction struct {
	actionutils.ParentAction
}

func (this *RecoverAction) RunPost(params struct {
	DomainId int64
}) {
	// 记录日志
	defer this.CreateLogInfo(codes.DNS_LogRecoverDomain, params.DomainId)

	// 执行恢复
	_, err := this.RPC().DNSDomainRPC().RecoverDNSDomain(this.AdminContext(), &pb.RecoverDNSDomainRequest{DnsDomainId: params.DomainId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
