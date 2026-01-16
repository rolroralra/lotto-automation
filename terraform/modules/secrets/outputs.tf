output "secret_arn" {
  description = "ARN of the credentials secret"
  value       = aws_secretsmanager_secret.lotto_credentials.arn
}

output "secret_name" {
  description = "Name of the credentials secret"
  value       = aws_secretsmanager_secret.lotto_credentials.name
}
