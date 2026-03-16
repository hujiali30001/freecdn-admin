package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"github.com/hujiali30001/freecdn-admin/internal/configs"
	"github.com/hujiali30001/freecdn-admin/internal/rpc"
	"github.com/TeaOSLab/EdgeCommon/pkg/rpc/pb"
	"github.com/iwind/TeaGo/Tea"
	stringutil "github.com/iwind/TeaGo/utils/string"
)

func main() {
	// 工作目录优先从环境变量读取，再从命令行参数读取
	workDir := os.Getenv("FREECDN_WORK_DIR")
	if workDir == "" {
		workDir = "/usr/local/freecdn/edge-admin"
	}
	username := "admin"
	password := ""

	if len(os.Args) >= 2 {
		workDir = os.Args[1]
	}
	if len(os.Args) >= 3 {
		username = os.Args[2]
	}
	if len(os.Args) >= 4 {
		password = os.Args[3]
	}

	if password == "" {
		fmt.Println("ERROR: password is required. Usage: create-admin [workDir] [username] <password>")
		os.Exit(1)
	}

	Tea.UpdateRoot(workDir)
	fmt.Printf("[create-admin] workDir=%s\n", workDir)
	fmt.Printf("[create-admin] username=%s\n", username)
	// 不打印密码

	config, err := configs.LoadAPIConfig()
	if err != nil {
		fmt.Println("ERROR: load api config:", err)
		os.Exit(1)
	}

	fmt.Printf("[create-admin] RPC endpoints=%v nodeId=%s\n", config.RPCEndpoints, config.NodeId)

	client, err := rpc.NewRPCClient(config, false)
	if err != nil {
		fmt.Println("ERROR: create rpc client:", err)
		os.Exit(1)
	}
	defer client.Close()

	_, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	// ORA-08：与前端登录保持一致，发送 md5(password)
	// edge-api 存储的是 bcrypt(md5(password))，前端也发 md5(password)
	passwordMd5 := stringutil.Md5(password)

	_, err = client.AdminRPC().CreateOrUpdateAdmin(
		client.APIContext(0),
		&pb.CreateOrUpdateAdminRequest{
			Username: username,
			Password: passwordMd5,
		},
	)
	if err != nil {
		fmt.Println("ERROR: CreateOrUpdateAdmin:", err)
		os.Exit(1)
	}

	fmt.Printf("[create-admin] Admin '%s' created/updated successfully!\n", username)
	fmt.Printf("[create-admin] Login at http://HOST:7788 with username: %s\n", username)
}
