package teaconst

const (
	// FreeCDN 版本（基于 GoEdge v1.3.9 安全基线）
	Version = "0.1.0"

	APINodeVersion = "1.3.9"

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
