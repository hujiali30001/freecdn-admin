// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .
//go:build !plus

package settings

import (
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/maps"
)

func (this *IndexAction) initUserPlan(server *pb.Server) {
	var userPlanMap = maps.Map{"id": server.UserPlanId, "dayTo": "", "plan": maps.Map{}}
	this.Data["userPlan"] = userPlanMap
}
