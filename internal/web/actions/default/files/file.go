// Copyright 2022 GoEdge CDN goedge.cdn@gmail.com. All rights reserved. Official site: https://goedge.cloud .

package files

import (
	"mime"
	"path/filepath"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/iwind/TeaGo/types"
)

type FileAction struct {
	actionutils.ParentAction
}

func (this *FileAction) Init() {
	this.Nav("", "", "")
}

func (this *FileAction) RunGet(params struct {
	FileId int64
}) {
	ctx := this.AdminContext()
	fileResp, err := this.RPC().FileRPC().FindEnabledFile(ctx, &pb.FindEnabledFileRequest{FileId: params.FileId})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	var file = fileResp.File
	if file == nil {
		this.NotFound("File", params.FileId)
		return
	}

	chunkRPC := this.RPC().FileChunkRPC()
	chunkIdsResp, err := chunkRPC.FindAllFileChunkIds(ctx, &pb.FindAllFileChunkIdsRequest{FileId: file.Id})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.AddHeader("Content-Length", types.String(file.Size))
	if len(file.MimeType) > 0 {
		this.AddHeader("Content-Type", file.MimeType)
	} else if len(file.Filename) > 0 {
		var ext = filepath.Ext(file.Filename)
		var mimeType = mime.TypeByExtension(ext)
		this.AddHeader("Content-Type", mimeType)
	}

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
