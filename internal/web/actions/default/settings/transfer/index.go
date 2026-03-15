// Copyright 2021 GoEdge CDN goedge.cdn@gmail.com. All rights reserved.

package transfer

import "github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"

type IndexAction struct {
	actionutils.ParentAction
}

func (this *IndexAction) Init() {
	this.Nav("", "transfer", "")
}

func (this *IndexAction) RunGet(params struct{}) {
	this.Show()
}
