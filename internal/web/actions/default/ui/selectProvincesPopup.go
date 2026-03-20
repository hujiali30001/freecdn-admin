package ui

import (
	"github.com/hujiali30001/freecdn-admin/internal/utils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/regionconfigs"
	"github.com/iwind/TeaGo/actions"
	"github.com/iwind/TeaGo/lists"
	"github.com/iwind/TeaGo/maps"
)

type SelectProvincesPopupAction struct {
	actionutils.ParentAction
}

func (this *SelectProvincesPopupAction) Init() {
	this.Nav("", "", "")
}

func (this *SelectProvincesPopupAction) RunGet(params struct {
	ProvinceIds string
}) {
	var selectedProvinceIds = utils.SplitNumbers(params.ProvinceIds)

	provincesResp, err := this.RPC().RegionProvinceRPC().FindAllRegionProvincesWithRegionCountryId(this.AdminContext(), &pb.FindAllRegionProvincesWithRegionCountryIdRequest{RegionCountryId: regionconfigs.RegionChinaId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	var provinceMaps = []maps.Map{}
	for _, province := range provincesResp.RegionProvinces {
		provinceMaps = append(provinceMaps, maps.Map{
			"id":        province.Id,
			"name":      province.DisplayName,
			"isChecked": lists.ContainsInt64(selectedProvinceIds, province.Id),
		})
	}
	this.Data["provinces"] = provinceMaps

	this.Show()
}

func (this *SelectProvincesPopupAction) RunPost(params struct {
	ProvinceIds []int64

	Must *actions.Must
	CSRF *actionutils.CSRF
}) {
	provincesResp, err := this.RPC().RegionProvinceRPC().FindAllRegionProvincesWithRegionCountryId(this.AdminContext(), &pb.FindAllRegionProvincesWithRegionCountryIdRequest{RegionCountryId: regionconfigs.RegionChinaId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	provinceNames := map[int64]string{}
	for _, province := range provincesResp.RegionProvinces {
		provinceNames[province.Id] = province.DisplayName
	}

	var provinceMaps = []maps.Map{}
	for _, provinceId := range params.ProvinceIds {
		name, ok := provinceNames[provinceId]
		if !ok {
			continue
		}
		provinceMaps = append(provinceMaps, maps.Map{
			"id":   provinceId,
			"name": name,
		})
	}
	this.Data["provinces"] = provinceMaps

	this.Success()
}
