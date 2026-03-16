#!/bin/bash
find /tmp/freecdn-b/freecdn-api -maxdepth 3 -name "*.go" | grep -E "cmd|main"
