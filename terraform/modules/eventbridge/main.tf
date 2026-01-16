# EventBridge Module
# Scheduler for periodic Lambda invocation

# EventBridge Rule (Scheduler)
resource "aws_cloudwatch_event_rule" "schedule" {
  name                = "${var.project_name}-schedule-${var.environment}"
  description         = "Schedule for lotto automation - Every Monday at 15:00 KST"
  schedule_expression = var.schedule_expression

  tags = {
    Name        = "${var.project_name}-schedule"
    Environment = var.environment
  }
}

# EventBridge Target
resource "aws_cloudwatch_event_target" "lambda" {
  rule      = aws_cloudwatch_event_rule.schedule.name
  target_id = "${var.project_name}-target"
  arn       = var.lambda_function_arn

  input = jsonencode({
    action = "buy_ticket"
  })
}
