// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

//go:build !plus

package servergrouputils

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/TeaOSLab/EdgeCommon/pkg/rpc/pb"
	"github.com/iwind/TeaGo/maps"
)

func filterMenuItems(leftMenuItems []maps.Map, groupId int64, urlPrefix string, menuItem string, configInfoResp *pb.FindEnabledServerGroupConfigInfoResponse, parent *actionutils.ParentAction) []maps.Map {
	return leftMenuItems
}

func filterMenuItems2(leftMenuItems []maps.Map, groupId int64, urlPrefix string, menuItem string, configInfoResp *pb.FindEnabledServerGroupConfigInfoResponse, parent *actionutils.ParentAction) []maps.Map {
	return leftMenuItems
}
