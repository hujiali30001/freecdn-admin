package node

import (
	"fmt"
	"strconv"

	teaconst "github.com/hujiali30001/freecdn-admin/internal/const"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/default/clusters/cluster/node/nodeutils"
)

type IndexAction struct {
	actionutils.ParentAction
}

func (this *IndexAction) Init() {
	this.Nav("", "node", "node")
	this.SecondMenu("nodes")
}

func (this *IndexAction) RunGet(params struct {
	NodeId int64
}) {
	_, err := nodeutils.InitNodeInfo(this.Parent(), params.NodeId)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	if teaconst.IsPlus {
		this.RedirectURL("/clusters/cluster/node/boards?clusterId=" + fmt.Sprintf("%d", this.Data["clusterId"]) + "&nodeId=" + strconv.FormatInt(params.NodeId, 10))
	} else {
		this.RedirectURL("/clusters/cluster/node/detail?clusterId=" + fmt.Sprintf("%d", this.Data["clusterId"]) + "&nodeId=" + strconv.FormatInt(params.NodeId, 10))
	}
}
