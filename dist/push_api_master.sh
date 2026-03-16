#!/bin/bash
# Push freecdn-api health endpoint to GitHub (master branch)
TOKEN=$1
export HTTPS_PROXY=http://172.24.208.1:4780
export HTTP_PROXY=http://172.24.208.1:4780

cd /tmp/freecdn-b/freecdn-api
git remote set-url origin https://${TOKEN}@github.com/hujiali30001/freecdn-api.git
git push origin master
echo "push exit: $?"
