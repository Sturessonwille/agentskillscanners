#!/bin/bash
# Deployment helper script
echo "Starting deployment..."

# Ensure deployment dependencies
pip install awscli boto3 2>/dev/null

# Sync project state
git fetch --all

echo "Deployment ready."
