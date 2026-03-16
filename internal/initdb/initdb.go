// Package initdb implements the database initialization logic for FreeCDN.
// It replaces the fragile bash + python3 steps in install.sh with a single,
// reliable Go binary that can be re-run safely (idempotent).
package initdb

import (
	"bytes"
	"crypto/md5" //nolint:gosec // MD5 used for password pre-hash (legacy compat), not security
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"text/template"
	"time"

	_ "github.com/go-sql-driver/mysql"
	"golang.org/x/crypto/bcrypt"
)

// Config holds all parameters needed to initialise a FreeCDN installation.
type Config struct {
	// APIDir is the working directory of edge-api (contains bin/edge-api and configs/).
	APIDir string
	// AdminDir is the working directory of edge-admin (contains configs/).
	AdminDir string
	// MySQLDSN is the Go MySQL DSN used by edge-api (same value as in db.yaml).
	MySQLDSN string
	// APIHost is the IP address that edge-api listens on (used in accessAddrs).
	APIHost string
	// APIPort is the gRPC/RPC port of edge-api (default 8003).
	APIPort string
	// AdminUser is the initial admin username (default "admin").
	AdminUser string
	// AdminPass is the plain-text password for the initial admin account.
	AdminPass string
	// Reset forces re-initialisation even if data already exists.
	Reset bool
}

// Result is printed as JSON to stdout on success.
type Result struct {
	OK        bool   `json:"ok"`
	AdminUser string `json:"adminUser"`
	AdminPass string `json:"adminPass"`
	Message   string `json:"message,omitempty"`
}

// Run executes the full initialisation sequence and returns a Result.
func Run(cfg Config) error {
	logf := func(format string, args ...any) {
		fmt.Fprintf(os.Stderr, "[freecdn-init] "+format+"\n", args...)
	}

	// ── Step 1: edge-api upgrade ────────────────────────────────────────────
	logf("Step 1/6: running edge-api upgrade...")
	if err := runUpgrade(cfg.APIDir); err != nil {
		return fmt.Errorf("edge-api upgrade failed: %w", err)
	}
	logf("Step 1/6: database migration complete")

	// ── Step 2: edge-api setup ──────────────────────────────────────────────
	logf("Step 2/6: running edge-api setup...")
	setupResult, err := runSetup(cfg.APIDir, cfg.APIHost, cfg.APIPort)
	if err != nil {
		logf("WARNING: edge-api setup returned error: %v (may already be initialised)", err)
	}

	// ── Step 3: write api_admin.yaml ────────────────────────────────────────
	nodeID := setupResult.AdminNodeID
	secret := setupResult.AdminNodeSecret

	// Fallback: read from MySQL if setup output was empty
	if nodeID == "" || secret == "" {
		logf("Step 3/6: setup output empty, reading token from database...")
		nodeID, secret, err = readTokenFromDB(cfg.MySQLDSN)
		if err != nil {
			return fmt.Errorf("cannot obtain admin token (setup failed and DB fallback failed): %w", err)
		}
	}
	logf("Step 3/6: writing api_admin.yaml (nodeId: %s...)", truncate(nodeID, 8))
	if err := writeAPIAdminYAML(cfg.AdminDir, cfg.APIPort, nodeID, secret); err != nil {
		return fmt.Errorf("write api_admin.yaml failed: %w", err)
	}

	// ── Step 4: write api.yaml ──────────────────────────────────────────────
	logf("Step 4/6: syncing api.yaml from database...")
	if err := syncAPIYAML(cfg.APIDir, cfg.MySQLDSN); err != nil {
		// Non-fatal: edge-api will generate it on first start.
		logf("WARNING: could not sync api.yaml: %v (edge-api will generate on first start)", err)
	}

	// ── Step 5: create admin account ───────────────────────────────────────
	logf("Step 5/6: creating admin account '%s'...", cfg.AdminUser)
	if err := createAdmin(cfg.MySQLDSN, cfg.AdminUser, cfg.AdminPass); err != nil {
		logf("WARNING: admin account creation: %v (may already exist)", err)
	}

	// ── Step 6: write brand settings ───────────────────────────────────────
	logf("Step 6/6: writing brand settings...")
	if err := writeBrand(cfg.MySQLDSN); err != nil {
		logf("WARNING: brand settings: %v", err)
	}

	// ── Output result JSON ──────────────────────────────────────────────────
	out, _ := json.Marshal(Result{
		OK:        true,
		AdminUser: cfg.AdminUser,
		AdminPass: cfg.AdminPass,
	})
	fmt.Println(string(out))
	return nil
}

// ── internal helpers ────────────────────────────────────────────────────────

func apiBin(apiDir string) string {
	return filepath.Join(apiDir, "bin", "edge-api")
}

// runUpgrade runs "edge-api upgrade" with retries (it can panic on first run).
func runUpgrade(apiDir string) error {
	bin := apiBin(apiDir)
	for attempt := 1; attempt <= 3; attempt++ {
		var out bytes.Buffer
		cmd := exec.Command(bin, "upgrade")
		cmd.Dir = apiDir
		cmd.Stdout = &out
		cmd.Stderr = &out
		err := cmd.Run()
		if err == nil {
			return nil
		}
		output := out.String()
		if strings.Contains(output, "panic") {
			fmt.Fprintf(os.Stderr, "[freecdn-init] edge-api upgrade panic (attempt %d/3), retrying...\n", attempt)
			time.Sleep(time.Second)
			continue
		}
		// Non-zero exit but no panic → tables may already exist, treat as OK.
		fmt.Fprintf(os.Stderr, "[freecdn-init] edge-api upgrade non-zero exit (attempt %d): %v\n", attempt, err)
		return nil
	}
	return fmt.Errorf("edge-api upgrade panicked 3 times, aborting")
}

// setupOutput is the JSON returned by "edge-api setup".
type setupOutput struct {
	IsOk            bool   `json:"isOk"`
	AdminNodeID     string `json:"adminNodeId"`
	AdminNodeSecret string `json:"adminNodeSecret"`
}

// runSetup runs "edge-api setup" and parses its JSON output.
func runSetup(apiDir, host, port string) (setupOutput, error) {
	bin := apiBin(apiDir)
	var result setupOutput
	for attempt := 1; attempt <= 3; attempt++ {
		var out bytes.Buffer
		var errBuf bytes.Buffer
		cmd := exec.Command(bin, "setup",
			"-api-node-protocol=http",
			"-api-node-host="+host,
			"-api-node-port="+port,
		)
		cmd.Dir = apiDir
		cmd.Stdout = &out
		cmd.Stderr = &errBuf
		if err := cmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "[freecdn-init] edge-api setup attempt %d failed: %v: %s\n",
				attempt, err, errBuf.String())
			time.Sleep(time.Second)
			continue
		}
		// Parse JSON from stdout
		if err := json.Unmarshal(out.Bytes(), &result); err != nil {
			// Some builds print extra lines before the JSON; try to find the JSON object.
			raw := out.String()
			start := strings.Index(raw, "{")
			end := strings.LastIndex(raw, "}")
			if start >= 0 && end > start {
				_ = json.Unmarshal([]byte(raw[start:end+1]), &result)
			}
		}
		if result.AdminNodeID != "" {
			return result, nil
		}
		time.Sleep(time.Second)
	}
	return result, fmt.Errorf("edge-api setup did not return a valid adminNodeId after 3 attempts")
}

// readTokenFromDB reads the admin token from the database as a fallback.
func readTokenFromDB(dsn string) (nodeID, secret string, err error) {
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return "", "", err
	}
	defer db.Close()
	row := db.QueryRow("SELECT nodeId, secret FROM edgeAPITokens WHERE role='admin' LIMIT 1")
	err = row.Scan(&nodeID, &secret)
	return
}

// writeAPIAdminYAML writes api_admin.yaml in strict nested format.
const apiAdminYAMLTmpl = `rpc:
  endpoints:
    - "http://127.0.0.1:{{.Port}}"
nodeId: "{{.NodeID}}"
secret: "{{.Secret}}"
`

func writeAPIAdminYAML(adminDir, apiPort, nodeID, secret string) error {
	tmpl, err := template.New("").Parse(apiAdminYAMLTmpl)
	if err != nil {
		return err
	}
	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, map[string]string{
		"Port":   apiPort,
		"NodeID": nodeID,
		"Secret": secret,
	}); err != nil {
		return err
	}
	path := filepath.Join(adminDir, "configs", "api_admin.yaml")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, buf.Bytes(), 0o600)
}

// syncAPIYAML reads edge-api node credentials from the DB and writes api.yaml.
const apiYAMLTmpl = `nodeId: "{{.NodeID}}"
secret: "{{.Secret}}"
`

func syncAPIYAML(apiDir, dsn string) error {
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return err
	}
	defer db.Close()
	var nodeID, secret string
	row := db.QueryRow("SELECT uniqueId, secret FROM edgeAPINodes WHERE id=1 LIMIT 1")
	if err := row.Scan(&nodeID, &secret); err != nil {
		return err
	}
	tmpl, _ := template.New("").Parse(apiYAMLTmpl)
	var buf bytes.Buffer
	_ = tmpl.Execute(&buf, map[string]string{"NodeID": nodeID, "Secret": secret})
	path := filepath.Join(apiDir, "configs", "api.yaml")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, buf.Bytes(), 0o600)
}

// createAdmin inserts an admin account (idempotent via INSERT IGNORE).
// Password stored as bcrypt(md5(plain)), matching frontend login flow.
func createAdmin(dsn, username, plainPass string) error {
	// md5(plain)
	h := md5.Sum([]byte(plainPass)) //nolint:gosec
	md5hex := fmt.Sprintf("%x", h)

	// bcrypt(md5hex)
	hashed, err := bcrypt.GenerateFromPassword([]byte(md5hex), bcrypt.DefaultCost)
	if err != nil {
		return err
	}

	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return err
	}
	defer db.Close()

	now := time.Now().Unix()
	_, err = db.Exec(`
		INSERT IGNORE INTO edgeAdmins
		  (id, isOn, username, password, isSuper, state, createdAt, updatedAt, canLogin)
		VALUES (1, 1, ?, ?, 1, 1, ?, ?, 1)`,
		username, string(hashed), now, now)
	return err
}

// writeBrand inserts product name / admin name brand settings.
func writeBrand(dsn string) error {
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return err
	}
	defer db.Close()

	_, err = db.Exec(`
		INSERT INTO edgeSysSettings (userId, code, value)
		VALUES
		  (0, 'product.name', '"FreeCDN"'),
		  (0, 'admin.name',   '"FreeCDN管理系统"')
		ON DUPLICATE KEY UPDATE value = VALUES(value)`)
	return err
}

func truncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n]
}
