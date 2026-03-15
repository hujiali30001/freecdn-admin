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
)

func main() {
	workDir := "/home/huhuhu/freecdn/goedge/edge-admin"
	username := "admin"
	password := "Admin2026"

	if len(os.Args) >= 2 {
		workDir = os.Args[1]
	}
	if len(os.Args) >= 3 {
		username = os.Args[2]
	}
	if len(os.Args) >= 4 {
		password = os.Args[3]
	}

	Tea.UpdateRoot(workDir)
	fmt.Printf("[create-admin] workDir=%s\n", workDir)
	fmt.Printf("[create-admin] username=%s\n", username)

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

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	_, err = client.AdminRPC().CreateOrUpdateAdmin(
		client.APIContext(0),
		&pb.CreateOrUpdateAdminRequest{
			Username: username,
			Password: password,
		},
	)
	if err != nil {
		fmt.Println("ERROR: CreateOrUpdateAdmin:", err)
		_ = ctx
		os.Exit(1)
	}

	fmt.Printf("[create-admin] Admin '%s' created/updated successfully!\n", username)
	fmt.Printf("[create-admin] Login at http://WSL_IP:7788 with %s / %s\n", username, password)
}
