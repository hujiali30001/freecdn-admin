// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .
//go:build !plus

package nodeutils

import (
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/maps"
)

func filterMenuItems(menuItems []maps.Map, menuItem string, prefix string, query string, info *pb.FindEnabledNodeConfigInfoResponse, langCode string) []maps.Map {
	return menuItems
}
