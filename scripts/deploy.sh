#!/bin/bash
# Deployment Script for Lotto Automation
# Builds Lambda package and deploys via Terraform

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "${SCRIPT_DIR}")"
TERRAFORM_DIR="${PROJECT_DIR}/terraform"

echo "=== Lotto Automation Deployment ==="
echo "Project Directory: ${PROJECT_DIR}"
echo ""

# Note: Docker build is handled by Terraform's null_resource.docker_build
# No need to run build.sh (legacy ZIP packaging)

# Terraform deployment
echo "Step 1: Running Terraform..."
cd "${TERRAFORM_DIR}"

# Initialize if needed
if [ ! -d ".terraform" ]; then
    echo "  Initializing Terraform..."
    tofu init
fi

# Plan
echo "  Creating execution plan..."
tofu plan -out=tfplan

# Prompt for confirmation
echo ""
read -p "Do you want to apply this plan? (y/N) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  Applying changes..."
    tofu apply tfplan
    rm -f tfplan

    echo ""
    echo "=== Deployment Complete ==="
    echo ""
    tofu output
else
    echo "  Deployment cancelled."
    rm -f tfplan
fi
