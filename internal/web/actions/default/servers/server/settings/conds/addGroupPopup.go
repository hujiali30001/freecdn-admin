package conds

import (
	"encoding/json"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/default/servers/server/settings/conds/condutils"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/shared"
	"github.com/iwind/TeaGo/actions"
)

type AddGroupPopupAction struct {
	actionutils.ParentAction
}

func (this *AddGroupPopupAction) Init() {
}

func (this *AddGroupPopupAction) RunGet(params struct{}) {
	this.Data["components"] = condutils.ReadAllAvailableCondTypes()

	this.Show()
}

func (this *AddGroupPopupAction) RunPost(params struct {
	CondGroupJSON []byte

	Must *actions.Must
}) {
	groupConfig := &shared.HTTPRequestCondGroup{}
	err := json.Unmarshal(params.CondGroupJSON, groupConfig)
	if err != nil {
		this.Fail("解析条件时发生错误：" + err.Error())
	}

	err = groupConfig.Init()
	if err != nil {
		this.Fail("校验条件设置时失败：" + err.Error())
	}

	this.Data["group"] = groupConfig
	this.Success()
}
