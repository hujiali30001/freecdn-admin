package origins

import (
	"encoding/json"
	"errors"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs"
	"github.com/iwind/TeaGo/actions"
)

// AddPopupAction 添加源站
type AddPopupAction struct {
	actionutils.ParentAction
}

func (this *AddPopupAction) RunGet(params struct {
	ServerId       int64
	ServerType     string
	ReverseProxyId int64
	OriginType     string
}) {
	this.Data["reverseProxyId"] = params.ReverseProxyId
	this.Data["originType"] = params.OriginType

	var serverType string
	if params.ServerId > 0 {
		serverTypeResp, err := this.RPC().ServerRPC().FindEnabledServerType(this.AdminContext(), &pb.FindEnabledServerTypeRequest{ServerId: params.ServerId})
		if err != nil {
			this.ErrorPage(err)
			return
		}
		serverType = serverTypeResp.Type
	} else {
		serverType = params.ServerType
	}
	this.Data["serverType"] = serverType

	// 是否为HTTP
	this.Data["isHTTP"] = serverType == "httpProxy" || serverType == "httpWeb"

	// OSS
	this.getOSSHook()

	this.Show()
}

func (this *AddPopupAction) RunPost(params struct {
	OriginType string

	ReverseProxyId int64
	Weight         int32
	Protocol       string
	Addr           string
	Name           string

	ConnTimeout  int
	ReadTimeout  int
	MaxConns     int32
	MaxIdleConns int32
	IdleTimeout  int

	CertIdsJSON []byte

	DomainsJSON  []byte
	Host         string
	FollowPort   bool
	Http2Enabled bool

	Description string
	IsOn        bool

	Must *actions.Must
}) {
	ossConfig, goNext, err := this.postOSSHook(params.Protocol)
	if err != nil {
		this.ErrorPage(err)
		return
	}
	if !goNext {
		return
	}

	// 初始化
	var pbAddr = &pb.NetworkAddress{
		Protocol: params.Protocol,
	}
	var connTimeoutJSON []byte
	var readTimeoutJSON []byte
	var idleTimeoutJSON []byte
	var certRefJSON []byte
	var ok bool

	var ossJSON []byte = nil
	if ossConfig != nil { // OSS
		ossJSON, err = json.Marshal(ossConfig)
		if err != nil {
			this.ErrorPage(err)
			return
		}
		err = ossConfig.Init()
		if err != nil {
			this.Fail("校验OSS配置时出错：" + err.Error())
			return
		}
	} else { // 普通源站
		pbAddr, connTimeoutJSON, readTimeoutJSON, idleTimeoutJSON, certRefJSON, ok = buildOriginNetworkConfig(this.Parent(), params.Must, params.Protocol, params.Addr, params.ConnTimeout, params.ReadTimeout, params.IdleTimeout, params.CertIdsJSON)
		if !ok {
			return
		}
	}

	// 专属域名
	domains, err := parseOriginDomains(params.DomainsJSON)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	createResp, err := this.RPC().OriginRPC().CreateOrigin(this.AdminContext(), &pb.CreateOriginRequest{
		Name:            params.Name,
		Addr:            pbAddr,
		OssJSON:         ossJSON,
		Description:     params.Description,
		Weight:          params.Weight,
		IsOn:            params.IsOn,
		ConnTimeoutJSON: connTimeoutJSON,
		ReadTimeoutJSON: readTimeoutJSON,
		IdleTimeoutJSON: idleTimeoutJSON,
		MaxConns:        params.MaxConns,
		MaxIdleConns:    params.MaxIdleConns,
		CertRefJSON:     certRefJSON,
		Domains:         domains,
		Host:            params.Host,
		FollowPort:      params.FollowPort,
		Http2Enabled:    params.Http2Enabled,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	originId := createResp.OriginId
	originRef := &serverconfigs.OriginRef{
		IsOn:     true,
		OriginId: originId,
	}

	reverseProxyResp, err := this.RPC().ReverseProxyRPC().FindEnabledReverseProxy(this.AdminContext(), &pb.FindEnabledReverseProxyRequest{ReverseProxyId: params.ReverseProxyId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	reverseProxy := reverseProxyResp.ReverseProxy
	if reverseProxy == nil {
		this.ErrorPage(errors.New("reverse proxy should not be nil"))
		return
	}

	origins := []*serverconfigs.OriginRef{}
	switch params.OriginType {
	case "primary":
		if len(reverseProxy.PrimaryOriginsJSON) > 0 {
			err = json.Unmarshal(reverseProxy.PrimaryOriginsJSON, &origins)
			if err != nil {
				this.ErrorPage(err)
				return
			}
		}
	case "backup":
		if len(reverseProxy.BackupOriginsJSON) > 0 {
			err = json.Unmarshal(reverseProxy.BackupOriginsJSON, &origins)
			if err != nil {
				this.ErrorPage(err)
				return
			}
		}
	}
	origins = append(origins, originRef)
	originsData, err := json.Marshal(origins)
	if err != nil {
		this.ErrorPage(err)
		return
	}
	switch params.OriginType {
	case "primary":
		_, err = this.RPC().ReverseProxyRPC().UpdateReverseProxyPrimaryOrigins(this.AdminContext(), &pb.UpdateReverseProxyPrimaryOriginsRequest{
			ReverseProxyId: params.ReverseProxyId,
			OriginsJSON:    originsData,
		})
	case "backup":
		_, err = this.RPC().ReverseProxyRPC().UpdateReverseProxyBackupOrigins(this.AdminContext(), &pb.UpdateReverseProxyBackupOriginsRequest{
			ReverseProxyId: params.ReverseProxyId,
			OriginsJSON:    originsData,
		})
	}
	if err != nil {
		this.ErrorPage(err)
		return
	}

	// 日志
	defer this.CreateLogInfo(codes.ServerOrigin_LogCreateOrigin, originId)

	this.Success()
}
