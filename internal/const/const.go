package teaconst

const (
	// FreeCDN 版本（基于 GoEdge v1.3.9 安全基线）
	Version = "0.10.0"

	// APINodeVersion 期望的 API 节点版本，与 Version 保持一致，只检测自己 Release 的版本
	APINodeVersion = Version

	ProductName = "FreeCDN Admin"
	ProcessName = "edge-admin"

	Role = "admin"

	EncryptMethod = "aes-256-cfb"

	CookieSID      = "geadsid"
	SessionAdminId = "adminId"

	SystemdServiceName = "edge-admin"
	// UpdatesURL 留空：FreeCDN 不使用上游 GoEdge 的更新服务器
	// 版本更新通过 GitHub Releases 发布，由管理员手动决策是否升级
	UpdatesURL = ""
)
