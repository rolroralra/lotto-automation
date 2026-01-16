# Lotto Automation - Main Terraform Configuration

locals {
  function_name = "${var.project_name}-${var.environment}"
}

# Secrets Manager Module
module "secrets" {
  source = "./modules/secrets"

  project_name = var.project_name
  environment  = var.environment
}

# Notifications Module (SNS + SQS DLQ)
module "notifications" {
  source = "./modules/notifications"

  project_name       = var.project_name
  environment        = var.environment
  notification_email = var.notification_email
}

# Lambda Module
module "lambda" {
  source = "./modules/lambda"

  project_name  = var.project_name
  environment   = var.environment
  aws_region    = var.aws_region
  function_name = local.function_name
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size
  secret_arn    = module.secrets.secret_arn
  secret_name   = module.secrets.secret_name
  sns_topic_arn = module.notifications.sns_topic_arn
  dlq_arn       = module.notifications.dlq_arn
}

# EventBridge Module
module "eventbridge" {
  source = "./modules/eventbridge"

  project_name         = var.project_name
  environment          = var.environment
  schedule_expression  = var.schedule_expression
  lambda_function_arn  = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
}
