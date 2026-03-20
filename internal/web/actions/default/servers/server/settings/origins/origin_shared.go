package origins

import (
	"encoding/json"
	"net/url"
	"regexp"
	"strings"

	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/configutils"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/shared"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/sslconfigs"
	"github.com/iwind/TeaGo/actions"
	"github.com/iwind/TeaGo/types"
)

var originAddrRegexp = regexp.MustCompile(`^(http|https)://`)
var originSpaceRegexp = regexp.MustCompile(`\s+`)
var originPortRegexp = regexp.MustCompile(`^\d+$`)

func buildOriginNetworkConfig(action *actionutils.ParentAction, must *actions.Must, protocol string, addr string, connTimeout int, readTimeout int, idleTimeout int, certIdsJSON []byte) (*pb.NetworkAddress, []byte, []byte, []byte, []byte, bool) {
	must.
		Field("addr", addr).
		Require("请输入源站地址")

	if (protocol == "http" || protocol == "https") && originAddrRegexp.MatchString(addr) {
		u, err := url.Parse(addr)
		if err == nil {
			addr = u.Host
		}
	}

	addr = strings.ReplaceAll(addr, "：", ":")
	addr = originSpaceRegexp.ReplaceAllString(addr, "")
	portIndex := strings.LastIndex(addr, ":")
	if portIndex < 0 {
		if protocol == "http" {
			addr += ":80"
		} else if protocol == "https" {
			addr += ":443"
		} else {
			action.FailField("addr", "源站地址中需要带有端口")
			return nil, nil, nil, nil, nil, false
		}
		portIndex = strings.LastIndex(addr, ":")
	}

	host := addr[:portIndex]
	port := addr[portIndex+1:]
	if port == "0" {
		action.FailField("addr", "源站端口号不能为0")
		return nil, nil, nil, nil, nil, false
	}
	if !configutils.HasVariables(port) {
		if !originPortRegexp.MatchString(port) {
			action.FailField("addr", "源站端口号只能为整数")
			return nil, nil, nil, nil, nil, false
		}
		portInt := types.Int(port)
		if portInt == 0 {
			action.FailField("addr", "源站端口号不能为0")
			return nil, nil, nil, nil, nil, false
		}
		if portInt > 65535 {
			action.FailField("addr", "源站端口号不能大于65535")
			return nil, nil, nil, nil, nil, false
		}
	}

	connTimeoutJSON, err := (&shared.TimeDuration{
		Count: int64(connTimeout),
		Unit:  shared.TimeDurationUnitSecond,
	}).AsJSON()
	if err != nil {
		action.ErrorPage(err)
		return nil, nil, nil, nil, nil, false
	}

	readTimeoutJSON, err := (&shared.TimeDuration{
		Count: int64(readTimeout),
		Unit:  shared.TimeDurationUnitSecond,
	}).AsJSON()
	if err != nil {
		action.ErrorPage(err)
		return nil, nil, nil, nil, nil, false
	}

	idleTimeoutJSON, err := (&shared.TimeDuration{
		Count: int64(idleTimeout),
		Unit:  shared.TimeDurationUnitSecond,
	}).AsJSON()
	if err != nil {
		action.ErrorPage(err)
		return nil, nil, nil, nil, nil, false
	}

	certRefJSON, ok := parseOriginCertRefJSON(action, certIdsJSON)
	if !ok {
		return nil, nil, nil, nil, nil, false
	}

	pbAddr := &pb.NetworkAddress{
		Protocol:  protocol,
		Host:      host,
		PortRange: port,
	}

	return pbAddr, connTimeoutJSON, readTimeoutJSON, idleTimeoutJSON, certRefJSON, true
}

func parseOriginCertRefJSON(action *actionutils.ParentAction, certIdsJSON []byte) ([]byte, bool) {
	if len(certIdsJSON) == 0 {
		return nil, true
	}

	certIds := []int64{}
	err := json.Unmarshal(certIdsJSON, &certIds)
	if err != nil {
		action.ErrorPage(err)
		return nil, false
	}

	if len(certIds) == 0 || certIds[0] <= 0 {
		return nil, true
	}

	certRef := &sslconfigs.SSLCertRef{
		IsOn:   true,
		CertId: certIds[0],
	}
	certRefJSON, err := json.Marshal(certRef)
	if err != nil {
		action.ErrorPage(err)
		return nil, false
	}
	return certRefJSON, true
}

func parseOriginDomains(domainsJSON []byte) ([]string, error) {
	domains := []string{}
	if len(domainsJSON) == 0 {
		return domains, nil
	}

	err := json.Unmarshal(domainsJSON, &domains)
	if err != nil {
		return nil, err
	}

	for index, domain := range domains {
		domains[index] = strings.TrimSuffix(domain, "/")
	}
	return domains, nil
}
