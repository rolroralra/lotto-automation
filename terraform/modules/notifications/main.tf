# Notifications Module
# SNS Topic for alerts and SQS Dead Letter Queue

# SNS Topic for failure notifications
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-alerts-${var.environment}"

  tags = {
    Name        = "${var.project_name}-alerts"
    Environment = var.environment
  }
}

# Email subscription
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.notification_email
}

# SQS Dead Letter Queue for failed Lambda invocations
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-dlq-${var.environment}"
  message_retention_seconds = 1209600 # 14 days

  tags = {
    Name        = "${var.project_name}-dlq"
    Environment = var.environment
  }
}

# CloudWatch Alarm for DLQ messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-dlq-alarm-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when messages appear in the DLQ"

  dimensions = {
    QueueName = aws_sqs_queue.dlq.name
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = {
    Name        = "${var.project_name}-dlq-alarm"
    Environment = var.environment
  }
}
