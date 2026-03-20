package ui

import (
	"mime"
	"path/filepath"
	"strconv"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
)

// 公开的图片，不需要检查用户权限
type ImageAction struct {
	actionutils.ParentAction
}

func (this *ImageAction) Init() {
	this.Nav("", "", "")
}

func (this *ImageAction) RunGet(params struct {
	FileId int64
}) {
	ctx := this.AdminContext()
	fileResp, err := this.RPC().FileRPC().FindEnabledFile(ctx, &pb.FindEnabledFileRequest{FileId: params.FileId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	file := fileResp.File
	if file == nil {
		this.NotFound("file", params.FileId)
		return
	}

	if !file.IsPublic {
		this.NotFound("file", params.FileId)
		return
	}

	chunkRPC := this.RPC().FileChunkRPC()
	chunkIdsResp, err := chunkRPC.FindAllFileChunkIds(ctx, &pb.FindAllFileChunkIdsRequest{FileId: file.Id})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	mimeType := ""
	if len(file.Filename) > 0 {
		ext := filepath.Ext(file.Filename)
		mimeType = mime.TypeByExtension(ext)
	}
	if len(mimeType) == 0 {
		mimeType = "image/png"
	}

	this.AddHeader("Last-Modified", "Fri, 06 Sep 2019 08:29:50 GMT")
	this.AddHeader("Content-Type", mimeType)
	this.AddHeader("Content-Length", strconv.FormatInt(file.Size, 10))
	for _, chunkId := range chunkIdsResp.FileChunkIds {
		chunkResp, err := chunkRPC.DownloadFileChunk(ctx, &pb.DownloadFileChunkRequest{FileChunkId: chunkId})
		if err != nil {
			this.ErrorPage(err)
			return
		}
		if chunkResp.FileChunk == nil {
			continue
		}
		_, err = this.Write(chunkResp.FileChunk.Data)
		if err != nil {
			return
		}
	}
}
