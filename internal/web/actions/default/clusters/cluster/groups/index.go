package groups

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/maps"
)

type IndexAction struct {
	actionutils.ParentAction
}

func (this *IndexAction) Init() {
	this.Nav("", "node", "group")
	this.SecondMenu("nodes")
}

func (this *IndexAction) RunGet(params struct {
	ClusterId int64
}) {
	groupsResp, err := this.RPC().NodeGroupRPC().FindAllEnabledNodeGroupsWithNodeClusterId(this.AdminContext(), &pb.FindAllEnabledNodeGroupsWithNodeClusterIdRequest{
		NodeClusterId: params.ClusterId,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	groupMaps := []maps.Map{}
	for _, group := range groupsResp.NodeGroups {
		countResp, err := this.RPC().NodeRPC().CountAllEnabledNodesWithNodeGroupId(this.AdminContext(), &pb.CountAllEnabledNodesWithNodeGroupIdRequest{NodeGroupId: group.Id})
		if err != nil {
			this.ErrorPage(err)
			return
		}
		countNodes := countResp.Count

		groupMaps = append(groupMaps, maps.Map{
			"id":         group.Id,
			"name":       group.Name,
			"countNodes": countNodes,
		})
	}
	this.Data["groups"] = groupMaps

	this.Show()
}
