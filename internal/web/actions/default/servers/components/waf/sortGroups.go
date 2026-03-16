package waf

import (	"github.com/hujiali30001/freecdn-admin/internal/web/actions/actionutils"
	"github.com/hujiali30001/freecdn-common/pkg/langs/codes"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/dao"
	"github.com/hujiali30001/freecdn-common/pkg/rpc/pb"
	"github.com/hujiali30001/freecdn-common/pkg/serverconfigs/firewallconfigs"
)

type SortGroupsAction struct {
	actionutils.ParentAction
}

func (this *SortGroupsAction) RunPost(params struct {
	FirewallPolicyId int64
	Type             string
	GroupIds         []int64
}) {
	// 日志
	defer this.CreateLogInfo(codes.WAFRuleGroup_LogSortRuleGroups, params.FirewallPolicyId)

	firewallPolicy, err := dao.SharedHTTPFirewallPolicyDAO.FindEnabledHTTPFirewallPolicyConfig(this.AdminContext(), params.FirewallPolicyId)
	if err != nil {
		this.ErrorPage(err)
		return
	}

	if firewallPolicy == nil {
		this.NotFound("firewallPolicy", params.FirewallPolicyId)
		return
	}

	switch params.Type {
	case "inbound":
		refMapping := map[int64]*firewallconfigs.HTTPFirewallRuleGroupRef{}
		for _, ref := range firewallPolicy.Inbound.GroupRefs {
			refMapping[ref.GroupId] = ref
		}
		newRefs := []*firewallconfigs.HTTPFirewallRuleGroupRef{}
		for _, groupId := range params.GroupIds {
			ref, ok := refMapping[groupId]
			if ok {
				newRefs = append(newRefs, ref)
			}
		}
		firewallPolicy.Inbound.GroupRefs = newRefs
	case "outbound":
		refMapping := map[int64]*firewallconfigs.HTTPFirewallRuleGroupRef{}
		for _, ref := range firewallPolicy.Outbound.GroupRefs {
			refMapping[ref.GroupId] = ref
		}
		newRefs := []*firewallconfigs.HTTPFirewallRuleGroupRef{}
		for _, groupId := range params.GroupIds {
			ref, ok := refMapping[groupId]
			if ok {
				newRefs = append(newRefs, ref)
			}
		}
		firewallPolicy.Outbound.GroupRefs = newRefs
	}

	inboundJSON, err := firewallPolicy.InboundJSON()
	if err != nil {
		this.ErrorPage(err)
		return
	}

	outboundJSON, err := firewallPolicy.OutboundJSON()
	if err != nil {
		this.ErrorPage(err)
		return
	}

	_, err = this.RPC().HTTPFirewallPolicyRPC().UpdateHTTPFirewallPolicyGroups(this.AdminContext(), &pb.UpdateHTTPFirewallPolicyGroupsRequest{
		HttpFirewallPolicyId: params.FirewallPolicyId,
		InboundJSON:          inboundJSON,
		OutboundJSON:         outboundJSON,
	})
	if err != nil {
		this.ErrorPage(err)
		return
	}

	this.Success()
}
