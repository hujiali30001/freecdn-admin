// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .

package ui

import (
	"strings"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/regionconfigs"
	"github.com/iwind/TeaGo/lists"
	"github.com/iwind/TeaGo/maps"
)

type CountryOptionsAction struct {
	actionutils.ParentAction
}

func (this *CountryOptionsAction) RunPost(params struct{}) {
	countriesResp, err := this.RPC().RegionCountryRPC().FindAllRegionCountries(this.AdminContext(), &pb.FindAllRegionCountriesRequest{})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	var countryMaps = []maps.Map{}
	for _, country := range countriesResp.RegionCountries {
		if lists.ContainsInt64(regionconfigs.FindAllGreaterChinaSubRegionIds(), country.Id) {
			continue
		}

		if country.Codes == nil {
			country.Codes = []string{}
		}

		var letter = ""
		if len(country.Pinyin) > 0 && len(country.Pinyin[0]) > 0 {
			letter = strings.ToUpper(country.Pinyin[0][:1])
		}

		countryMaps = append(countryMaps, maps.Map{
			"id":       country.Id,
			"name":     country.Name,
			"fullname": letter + " " + country.Name,
			"codes":    country.Codes,
		})
	}
	this.Data["countries"] = countryMaps

	this.Success()
}
