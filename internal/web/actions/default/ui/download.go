package ui

import (
	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
)

// DownloadAction 下载指定的文本内容
type DownloadAction struct {
	actionutils.ParentAction
}

func (this *DownloadAction) Init() {
	this.Nav("", "", "")
}

func (this *DownloadAction) RunGet(params struct {
	File string
	Text string
}) {
	this.AddHeader("Content-Disposition", "attachment; filename=\""+params.File+"\";")
	this.WriteString(params.Text)
}
