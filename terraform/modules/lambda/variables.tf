variable "project_name" {
  description = "Project name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-northeast-2"
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "timeout" {
  description = "Lambda timeout in seconds"
  type        = number
  default     = 300
}

variable "memory_size" {
  description = "Lambda memory size in MB"
  type        = number
  default     = 1024
}

variable "secret_arn" {
  description = "ARN of credentials secret"
  type        = string
}

variable "secret_name" {
  description = "Name of credentials secret"
  type        = string
}

variable "sns_topic_arn" {
  description = "ARN of SNS topic for notifications"
  type        = string
}

variable "dlq_arn" {
  description = "ARN of SQS DLQ"
  type        = string
}
