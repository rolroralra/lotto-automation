output "sns_topic_arn" {
  description = "ARN of the SNS topic"
  value       = aws_sns_topic.alerts.arn
}

output "sns_topic_name" {
  description = "Name of the SNS topic"
  value       = aws_sns_topic.alerts.name
}

output "dlq_arn" {
  description = "ARN of the SQS Dead Letter Queue"
  value       = aws_sqs_queue.dlq.arn
}

output "dlq_url" {
  description = "URL of the SQS Dead Letter Queue"
  value       = aws_sqs_queue.dlq.url
}
