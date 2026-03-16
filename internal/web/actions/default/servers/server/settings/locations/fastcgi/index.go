package fastcgi

import (
	"encoding/json"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/dao"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs"
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
	this.Data["fastcgiRef"] = webConfig.FastcgiRef
	this.Data["fastcgiConfigs"] = webConfig.FastcgiList

	this.Show()
}

func (this *IndexAction) RunPost(params struct {
	WebId          int64
	FastcgiRefJSON []byte
	FastcgiJSON    []byte

	Must *actions.Must
}) {
	defer this.CreateLogInfo(codes.ServerFastcgi_LogUpdateHTTPFastcgi, params.WebId)

	// TODO 检查配置

	fastcgiRef := &serverconfigs.HTTPFastcgiRef{}
	err := json.Unmarshal(params.FastcgiRefJSON, fastcgiRef)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	fastcgiRefJSON, err := json.Marshal(fastcgiRef)
	if err != nil {
		this.ErrorPage(err)
		return
	}
	_, err = this.RPC().HTTPWebRPC().UpdateHTTPWebFastcgi(this.AdminContext(), &pb.UpdateHTTPWebFastcgiRequest{
		HttpWebId:   params.WebId,
		FastcgiJSON: fastcgiRefJSON,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
