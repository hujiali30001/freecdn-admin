package regions

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/maps"
)

type IndexAction struct {
	actionutils.ParentAction
}

func (this *IndexAction) Init() {
	this.Nav("", "", "index")
}

func (this *IndexAction) RunGet(params struct{}) {
	regionsResp, err := this.RPC().NodeRegionRPC().FindAllEnabledNodeRegions(this.AdminContext(), &pb.FindAllEnabledNodeRegionsRequest{})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	var regionMaps = []maps.Map{}
	for _, region := range regionsResp.NodeRegions {
		countNodesResp, err := this.RPC().NodeRPC().CountAllEnabledNodesWithNodeRegionId(this.AdminContext(), &pb.CountAllEnabledNodesWithNodeRegionIdRequest{NodeRegionId: region.Id})
		if err != nil {
			this.ErrorPage(err)
			return
		}

		regionMaps = append(regionMaps, maps.Map{
			"id":          region.Id,
			"isOn":        region.IsOn,
			"name":        region.Name,
			"description": region.Description,
			"countNodes":  countNodesResp.Count,
		})
	}
	this.Data["regions"] = regionMaps

	this.Show()
}
