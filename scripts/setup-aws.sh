#!/bin/bash
# AWS Initial Setup Script for Lotto Automation
# This script creates the S3 bucket and DynamoDB table for Terraform state

set -e

# Configuration
AWS_REGION="${AWS_REGION:-ap-northeast-2}"
PROJECT_NAME="lotto-automation"

# Get AWS Account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="${PROJECT_NAME}-tfstate-${ACCOUNT_ID}"
DYNAMODB_TABLE="terraform-locks"

echo "=== Lotto Automation AWS Setup ==="
echo "Region: ${AWS_REGION}"
echo "Account ID: ${ACCOUNT_ID}"
echo "S3 Bucket: ${BUCKET_NAME}"
echo "DynamoDB Table: ${DYNAMODB_TABLE}"
echo ""

# Create S3 bucket for Terraform state
echo "Creating S3 bucket for Terraform state..."
if aws s3api head-bucket --bucket "${BUCKET_NAME}" 2>/dev/null; then
    echo "  Bucket already exists: ${BUCKET_NAME}"
else
    aws s3api create-bucket \
        --bucket "${BUCKET_NAME}" \
        --region "${AWS_REGION}" \
        --create-bucket-configuration LocationConstraint="${AWS_REGION}"

    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "${BUCKET_NAME}" \
        --versioning-configuration Status=Enabled

    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "${BUCKET_NAME}" \
        --server-side-encryption-configuration '{
            "Rules": [
                {
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }
            ]
        }'

    echo "  Created bucket: ${BUCKET_NAME}"
fi

# Create DynamoDB table for state locking
echo "Creating DynamoDB table for state locking..."
if aws dynamodb describe-table --table-name "${DYNAMODB_TABLE}" --region "${AWS_REGION}" 2>/dev/null; then
    echo "  Table already exists: ${DYNAMODB_TABLE}"
else
    aws dynamodb create-table \
        --table-name "${DYNAMODB_TABLE}" \
        --attribute-definitions AttributeName=LockID,AttributeType=S \
        --key-schema AttributeName=LockID,KeyType=HASH \
        --billing-mode PAY_PER_REQUEST \
        --region "${AWS_REGION}"

    echo "  Created table: ${DYNAMODB_TABLE}"
    echo "  Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name "${DYNAMODB_TABLE}" --region "${AWS_REGION}"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Update terraform/backend.tf with the following:"
echo ""
echo "terraform {"
echo "  backend \"s3\" {"
echo "    bucket         = \"${BUCKET_NAME}\""
echo "    key            = \"terraform.tfstate\""
echo "    region         = \"${AWS_REGION}\""
echo "    encrypt        = true"
echo "    dynamodb_table = \"${DYNAMODB_TABLE}\""
echo "  }"
echo "}"
echo ""
echo "Next steps:"
echo "  1. cd terraform"
echo "  2. terraform init"
echo "  3. terraform plan"
echo "  4. terraform apply"
