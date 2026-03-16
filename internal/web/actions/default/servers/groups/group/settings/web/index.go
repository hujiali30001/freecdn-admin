package web

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/default/servers/groups/group/servergrouputils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/dao"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/actions"
)

type IndexAction struct {
	actionutils.ParentAction
}

func (this *IndexAction) Init() {
	this.Nav("", "setting", "index")
	this.SecondMenu("web")
}

func (this *IndexAction) RunGet(params struct {
	GroupId int64
}) {
	_, err := servergrouputils.InitGroup(this.Parent(), params.GroupId, "web")
	if err != nil {
		this.ErrorPage(err)
		return
	}

	webConfig, err := dao.SharedHTTPWebDAO.FindWebConfigWithServerGroupId(this.AdminContext(), params.GroupId)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Data["webId"] = webConfig.Id
	this.Data["rootConfig"] = webConfig.Root

	this.Show()
}

func (this *IndexAction) RunPost(params struct {
	WebId    int64
	RootJSON []byte

	Must *actions.Must
}) {
	defer this.CreateLogInfo(codes.ServerRoot_LogUpdateRoot, params.WebId)

	_, err := this.RPC().HTTPWebRPC().UpdateHTTPWeb(this.AdminContext(), &pb.UpdateHTTPWebRequest{
		HttpWebId: params.WebId,
		RootJSON:  params.RootJSON,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
