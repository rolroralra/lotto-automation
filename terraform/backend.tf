# Terraform Backend Configuration
# S3 bucket and DynamoDB table must be created before using this backend
# Run scripts/setup-aws.sh to create these resources

terraform {
  backend "s3" {
    bucket         = "lotto-automation-tfstate-182043863214"
    key            = "terraform.tfstate"
    region         = "ap-northeast-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
