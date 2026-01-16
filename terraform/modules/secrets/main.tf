# Secrets Manager Module
# Stores all account credentials in a single secret

resource "aws_secretsmanager_secret" "lotto_credentials" {
  name        = "${var.project_name}/credentials"
  description = "Lotto automation credentials for all accounts"

  tags = {
    Name        = "${var.project_name}-credentials"
    Environment = var.environment
  }
}

# Note: Secret value must be set manually after creation
# Format: {"accounts": [{"username": "id", "password": "pw"}, ...]}
# aws secretsmanager put-secret-value \
#   --secret-id lotto-automation/credentials \
#   --secret-string '{"accounts":[{"username":"id1","password":"pw1"},{"username":"id2","password":"pw2"}]}'
