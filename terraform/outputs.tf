output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.lambda.function_arn
}

output "sns_topic_arn" {
  description = "ARN of the SNS topic for notifications"
  value       = module.notifications.sns_topic_arn
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule"
  value       = module.eventbridge.rule_arn
}

output "secret_arn" {
  description = "ARN of the credentials secret"
  value       = module.secrets.secret_arn
}

output "secret_name" {
  description = "Name of the credentials secret"
  value       = module.secrets.secret_name
}
