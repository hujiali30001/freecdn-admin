package cluster

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

type DeleteAction struct {
	actionutils.ParentAction
}

func (this *DeleteAction) Init() {
	this.Nav("", "delete", "index")
	this.SecondMenu("nodes")
}

func (this *DeleteAction) RunGet(params struct{}) {
	this.Show()
}

func (this *DeleteAction) RunPost(params struct {
	ClusterId int64
}) {
	// 检查有无服务正在使用
	countResp, err := this.RPC().ServerRPC().CountAllEnabledServersWithNodeClusterId(this.AdminContext(), &pb.CountAllEnabledServersWithNodeClusterIdRequest{NodeClusterId: params.ClusterId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	if countResp.Count > 0 {
		this.Fail("有代理服务正在使用此集群，请修改这些代理服务后再删除")
	}

	// 删除
	_, err = this.RPC().NodeClusterRPC().DeleteNodeCluster(this.AdminContext(), &pb.DeleteNodeClusterRequest{NodeClusterId: params.ClusterId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	// 创建日志
	defer this.CreateLogInfo(codes.NodeCluster_LogDeleteCluster, params.ClusterId)

	this.Success()
}
