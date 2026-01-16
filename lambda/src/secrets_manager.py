"""
AWS Secrets Manager Utility
Retrieves credentials from AWS Secrets Manager
"""
import json
import boto3
from botocore.exceptions import ClientError

# Singleton client
_client = None


def get_secrets_client():
    """Get or create Secrets Manager client"""
    global _client
    if _client is None:
        _client = boto3.client('secretsmanager', region_name='ap-northeast-2')
    return _client


def get_all_credentials(secret_name: str) -> list:
    """
    Retrieve all account credentials from Secrets Manager

    Args:
        secret_name: Name of the secret (e.g., 'lotto-automation/credentials')

    Returns:
        list of dicts, each with 'username' and 'password' keys

    Secret format:
        {
          "accounts": [
            {"username": "id1", "password": "pw1"},
            {"username": "id2", "password": "pw2"}
          ]
        }

    Raises:
        ClientError: If secret retrieval fails
        ValueError: If secret format is invalid
    """
    client = get_secrets_client()

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret_string = response['SecretString']
        secret_data = json.loads(secret_string)

        # Validate format
        if not isinstance(secret_data, dict):
            raise ValueError(f"Secret {secret_name} must be a JSON object")

        if 'accounts' not in secret_data:
            raise ValueError(f"Secret {secret_name} must have 'accounts' key")

        accounts = secret_data['accounts']

        if not isinstance(accounts, list):
            raise ValueError(f"'accounts' must be a JSON array")

        # Validate each account
        for i, account in enumerate(accounts):
            if not isinstance(account, dict):
                raise ValueError(f"Account {i+1} must be a JSON object")
            if 'username' not in account or 'password' not in account:
                raise ValueError(f"Account {i+1} missing 'username' or 'password'")

        return accounts

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'ResourceNotFoundException':
            raise ValueError(f"Secret not found: {secret_name}")
        elif error_code == 'AccessDeniedException':
            raise PermissionError(f"Access denied to secret: {secret_name}")
        raise
