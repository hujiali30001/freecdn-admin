// freecdn-init: FreeCDN database initialisation tool.
//
// Replaces the bash+python3 DB init steps in install.sh with a single
// reliable, idempotent Go binary. Safe to re-run.
//
// Usage:
//
//	freecdn-init \
//	  --api-dir  /usr/local/freecdn/edge-admin/edge-api \
//	  --admin-dir /usr/local/freecdn/edge-admin \
//	  --mysql-dsn "freecdn:PASS@tcp(127.0.0.1:3306)/freecdn?charset=utf8mb4&parseTime=true" \
//	  --api-host  1.2.3.4 \
//	  --api-port  8003 \
//	  --admin-user admin \
//	  --admin-pass FreeCDN2026! \
//	  [--reset]
//
// On success: exits 0, prints {"ok":true,...} JSON to stdout.
// On failure: exits 1, prints error to stderr.
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/hujiali30001/freecdn-admin/internal/initdb"
)

func main() {
	cfg := initdb.Config{}

	flag.StringVar(&cfg.APIDir, "api-dir", "/usr/local/freecdn/edge-admin/edge-api",
		"working directory of edge-api (must contain bin/edge-api and configs/)")
	flag.StringVar(&cfg.AdminDir, "admin-dir", "/usr/local/freecdn/edge-admin",
		"working directory of edge-admin (configs/ will be written here)")
	flag.StringVar(&cfg.MySQLDSN, "mysql-dsn", "",
		"MySQL DSN, e.g. user:pass@tcp(127.0.0.1:3306)/db?charset=utf8mb4&parseTime=true")
	flag.StringVar(&cfg.APIHost, "api-host", "127.0.0.1",
		"IP address that edge-api is accessible on (used in accessAddrs)")
	flag.StringVar(&cfg.APIPort, "api-port", "8003",
		"edge-api gRPC/RPC port (default 8003)")
	flag.StringVar(&cfg.AdminUser, "admin-user", "admin",
		"initial admin username")
	flag.StringVar(&cfg.AdminPass, "admin-pass", "",
		"initial admin plain-text password (required)")
	flag.BoolVar(&cfg.Reset, "reset", false,
		"force re-initialisation even if data already exists")

	flag.Usage = func() {
		fmt.Fprintf(os.Stderr, "freecdn-init: FreeCDN one-shot database initialisation\n\n")
		fmt.Fprintf(os.Stderr, "Usage:\n")
		flag.PrintDefaults()
		fmt.Fprintf(os.Stderr, "\nExample:\n")
		fmt.Fprintf(os.Stderr, `  freecdn-init \
  --api-dir  /usr/local/freecdn/edge-admin/edge-api \
  --admin-dir /usr/local/freecdn/edge-admin \
  --mysql-dsn "freecdn:PASS@tcp(127.0.0.1:3306)/freecdn?charset=utf8mb4&parseTime=true" \
  --api-host  1.2.3.4 \
  --api-port  8003 \
  --admin-user admin \
  --admin-pass FreeCDN2026!
`)
	}
	flag.Parse()

	// Validate required flags.
	if cfg.MySQLDSN == "" {
		fmt.Fprintln(os.Stderr, "ERROR: --mysql-dsn is required")
		flag.Usage()
		os.Exit(1)
	}
	if cfg.AdminPass == "" {
		fmt.Fprintln(os.Stderr, "ERROR: --admin-pass is required")
		flag.Usage()
		os.Exit(1)
	}

	// Sanity check paths.
	apiBin := cfg.APIDir + "/bin/edge-api"
	if _, err := os.Stat(apiBin); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: edge-api binary not found at %s\n", apiBin)
		os.Exit(1)
	}

	if err := initdb.Run(cfg); err != nil {
		fmt.Fprintf(os.Stderr, "ERROR: %v\n", err)
		os.Exit(1)
	}
}
