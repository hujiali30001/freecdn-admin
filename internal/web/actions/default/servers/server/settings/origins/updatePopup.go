package origins

import (
	"encoding/json"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs"
	"github.com/iwind/TeaGo/actions"
	"github.com/iwind/TeaGo/maps"
	"github.com/iwind/TeaGo/types"
)

// UpdatePopupAction 修改源站
type UpdatePopupAction struct {
	actionutils.ParentAction
}

func (this *UpdatePopupAction) Init() {
	this.Nav("", "", "")
}

func (this *UpdatePopupAction) RunGet(params struct {
	ServerId       int64
	ServerType     string
	ReverseProxyId int64
	OriginType     string
	OriginId       int64
}) {
	this.Data["originType"] = params.OriginType
	this.Data["reverseProxyId"] = params.ReverseProxyId
	this.Data["originId"] = params.OriginId

	var serverType string
	if params.ServerId > 0 {
		serverTypeResp, err := this.RPC().ServerRPC().FindEnabledServerType(this.AdminContext(), &pb.FindEnabledServerTypeRequest{
			ServerId: params.ServerId,
		})
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

	// 源站信息
	originResp, err := this.RPC().OriginRPC().FindEnabledOriginConfig(this.AdminContext(), &pb.FindEnabledOriginConfigRequest{OriginId: params.OriginId})
	if err != nil {
		this.ErrorPage(err)
		return
	}
	var configData = originResp.OriginJSON
	var config = &serverconfigs.OriginConfig{}
	err = json.Unmarshal(configData, config)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	var connTimeout = 0
	var readTimeout = 0
	var idleTimeout = 0
	if config.ConnTimeout != nil {
		connTimeout = types.Int(config.ConnTimeout.Count)
	}

	if config.ReadTimeout != nil {
		readTimeout = types.Int(config.ReadTimeout.Count)
	}

	if config.IdleTimeout != nil {
		idleTimeout = types.Int(config.IdleTimeout.Count)
	}

	if len(config.Domains) == 0 {
		config.Domains = []string{}
	}

	// 重置数据
	if config.Cert != nil {
		config.Cert.CertData = nil
		config.Cert.KeyData = nil
	}

	var addr = ""
	if len(config.Addr.Host) > 0 && len(config.Addr.PortRange) > 0 {
		addr = config.Addr.Host + ":" + config.Addr.PortRange
	}
	this.Data["origin"] = maps.Map{
		"id":           config.Id,
		"protocol":     config.Addr.Protocol,
		"addr":         addr,
		"weight":       config.Weight,
		"name":         config.Name,
		"description":  config.Description,
		"isOn":         config.IsOn,
		"connTimeout":  connTimeout,
		"readTimeout":  readTimeout,
		"idleTimeout":  idleTimeout,
		"maxConns":     config.MaxConns,
		"maxIdleConns": config.MaxIdleConns,
		"cert":         config.Cert,
		"domains":      config.Domains,
		"host":         config.RequestHost,
		"followPort":   config.FollowPort,
		"http2Enabled": config.HTTP2Enabled,
		"oss":          config.OSS,
	}

	// OSS
	this.getOSSHook()

	this.Show()
}

func (this *UpdatePopupAction) RunPost(params struct {
	OriginType string
	OriginId   int64

	ReverseProxyId int64
	Protocol       string
	Addr           string
	Weight         int32
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

	var ossJSON []byte = nil
	var connTimeoutJSON []byte
	var readTimeoutJSON []byte
	var idleTimeoutJSON []byte
	var certRefJSON []byte
	var ok bool
	var pbAddr = &pb.NetworkAddress{
		Protocol: params.Protocol,
	}

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

	_, err = this.RPC().OriginRPC().UpdateOrigin(this.AdminContext(), &pb.UpdateOriginRequest{
		OriginId:        params.OriginId,
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

	// 日志
	defer this.CreateLogInfo(codes.ServerOrigin_LogUpdateOrigin, params.OriginId)

	this.Success()
}
