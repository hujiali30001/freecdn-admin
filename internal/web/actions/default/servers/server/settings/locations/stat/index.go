package stat

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/dao"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/actions"
)

type IndexAction struct {
	actionutils.ParentAction
}

func (this *IndexAction) Init() {
}

func (this *IndexAction) RunGet(params struct {
	LocationId int64
}) {
	webConfig, err := dao.SharedHTTPWebDAO.FindWebConfigWithLocationId(this.AdminContext(), params.LocationId)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Data["webId"] = webConfig.Id
	this.Data["statConfig"] = webConfig.StatRef

	this.Show()
}

func (this *IndexAction) RunPost(params struct {
	WebId    int64
	StatJSON []byte

	Must *actions.Must
}) {
	defer this.CreateLogInfo(codes.ServerStat_LogUpdateStatSettings, params.WebId)

	// TODO 校验配置

	_, err := this.RPC().HTTPWebRPC().UpdateHTTPWebStat(this.AdminContext(), &pb.UpdateHTTPWebStatRequest{
		HttpWebId: params.WebId,
		StatJSON:  params.StatJSON,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	this.Success()
}
