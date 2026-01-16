# Lambda Module
# Container-based Lambda function for lotto automation with Selenium + Chrome

locals {
  lambda_dir = "${path.root}/../lambda"
  ecr_repo   = "${var.project_name}-${var.environment}"
}

# ECR Repository for Lambda container image
resource "aws_ecr_repository" "lambda" {
  name                 = local.ecr_repo
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Name        = local.ecr_repo
    Environment = var.environment
  }
}

# Build and push Docker image
resource "null_resource" "docker_build" {
  triggers = {
    dockerfile_hash = filemd5("${local.lambda_dir}/Dockerfile")
    handler_hash    = filemd5("${local.lambda_dir}/src/handler.py")
    lotto_hash      = filemd5("${local.lambda_dir}/src/lotto.py")
    secrets_hash    = filemd5("${local.lambda_dir}/src/secrets_manager.py")
    requirements    = filemd5("${local.lambda_dir}/requirements.txt")
  }

  provisioner "local-exec" {
    command = <<-EOT
      cd ${local.lambda_dir}

      # Login to ECR
      aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.lambda.repository_url}

      # Build and push
      docker build --platform linux/amd64 -t ${aws_ecr_repository.lambda.repository_url}:latest .
      docker push ${aws_ecr_repository.lambda.repository_url}:latest
    EOT
  }

  depends_on = [aws_ecr_repository.lambda]
}

# Get the latest image digest
data "aws_ecr_image" "lambda" {
  repository_name = aws_ecr_repository.lambda.name
  image_tag       = "latest"

  depends_on = [null_resource.docker_build]
}

# Lambda function (container image)
resource "aws_lambda_function" "main" {
  function_name = var.function_name
  role          = aws_iam_role.lambda.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}@${data.aws_ecr_image.lambda.image_digest}"
  timeout       = var.timeout
  memory_size   = var.memory_size

  environment {
    variables = {
      SNS_TOPIC_ARN = var.sns_topic_arn
      SECRET_NAME   = var.secret_name
    }
  }

  dead_letter_config {
    target_arn = var.dlq_arn
  }

  tags = {
    Name        = var.function_name
    Environment = var.environment
  }

  depends_on = [null_resource.docker_build]
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 14

  tags = {
    Name        = "${var.function_name}-logs"
    Environment = var.environment
  }
}

# Lambda permission for EventBridge
resource "aws_lambda_permission" "eventbridge" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.main.function_name
  principal     = "events.amazonaws.com"
}
