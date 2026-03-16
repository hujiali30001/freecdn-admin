// Copyright 2024 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .

package security

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/helpers"
)

type DismissXFFPromptAction struct {
	actionutils.ParentAction
}

func (this *DismissXFFPromptAction) RunPost(params struct{}) {
	helpers.DisableXFFPrompt()

	this.Success()
}
