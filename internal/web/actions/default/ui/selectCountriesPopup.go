package ui

import (
	"strings"

	"github.com/hujiali30001/freecdn-admin/internal/utils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/actions"
	"github.com/iwind/TeaGo/lists"
	"github.com/iwind/TeaGo/maps"
)

type SelectCountriesPopupAction struct {
	actionutils.ParentAction
}

func (this *SelectCountriesPopupAction) Init() {
	this.Nav("", "", "")
}

func (this *SelectCountriesPopupAction) RunGet(params struct {
	CountryIds string
}) {
	var selectedCountryIds = utils.SplitNumbers(params.CountryIds)

	countriesResp, err := this.RPC().RegionCountryRPC().FindAllRegionCountries(this.AdminContext(), &pb.FindAllRegionCountriesRequest{})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	var countryMaps = []maps.Map{}
	for _, country := range countriesResp.RegionCountries {
		countryMaps = append(countryMaps, maps.Map{
			"id":        country.Id,
			"name":      country.DisplayName,
			"letter":    strings.ToUpper(string(country.Pinyin[0][0])),
			"isChecked": lists.ContainsInt64(selectedCountryIds, country.Id),
		})
	}
	this.Data["countries"] = countryMaps

	this.Show()
}

func (this *SelectCountriesPopupAction) RunPost(params struct {
	CountryIds []int64

	Must *actions.Must
	CSRF *actionutils.CSRF
}) {
	countriesResp, err := this.RPC().RegionCountryRPC().FindAllRegionCountries(this.AdminContext(), &pb.FindAllRegionCountriesRequest{})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	countryNames := map[int64]string{}
	for _, country := range countriesResp.RegionCountries {
		countryNames[country.Id] = country.DisplayName
	}

	var countryMaps = []maps.Map{}
	for _, countryId := range params.CountryIds {
		name, ok := countryNames[countryId]
		if !ok {
			continue
		}
		countryMaps = append(countryMaps, maps.Map{
			"id":   countryId,
			"name": name,
		})
	}
	this.Data["countries"] = countryMaps

	this.Success()
}
