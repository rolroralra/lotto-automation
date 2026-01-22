"""
AWS Lambda Handler for Lotto Automation
Entry point for Lambda function
"""
import os
import json
import logging
import boto3
from secrets_manager import get_all_credentials
from lotto import buy_lotto_ticket, check_lotto_balance, check_lotto_result

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# SNS client for notifications
sns_client = boto3.client('sns')


def send_notification(topic_arn: str, subject: str, message: str):
    """Send notification via SNS"""
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject,
            Message=message
        )
        logger.info(f"Notification sent: {subject}")
    except Exception as e:
        logger.error(f"Failed to send notification: {e}")


def lambda_handler(event, context):
    """
    Lambda handler function

    Event format:
    {
        "action": "buy_ticket"  # buy_ticket, check_balance, check_result
    }

    Credentials are read from SECRET_NAME environment variable.
    Secret format:
    {
        "accounts": [
            {"username": "id1", "password": "pw1"},
            {"username": "id2", "password": "pw2"}
        ]
    }
    """
    logger.info(f"Event: {json.dumps(event)}")

    # Get configuration from environment
    sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
    secret_name = os.environ.get('SECRET_NAME')

    if not secret_name:
        error_msg = "Missing SECRET_NAME environment variable"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

    action = event.get('action', 'buy_ticket')
    all_results = []
    errors = []

    try:
        # Get all credentials from Secrets Manager
        logger.info(f"Retrieving credentials from: {secret_name}")
        credentials_list = get_all_credentials(secret_name)
        logger.info(f"Found {len(credentials_list)} accounts")

        # Process each account
        for i, creds in enumerate(credentials_list):
            username = creds.get('username')
            password = creds.get('password')

            if not username or not password:
                logger.warning(f"Account {i+1}: Missing username or password, skipping")
                continue

            logger.info(f"Processing account: {username}")
            account_results = []

            try:
                if action == 'buy_ticket':
                    result = buy_lotto_ticket(username, password)
                    account_results.append(result)

                    # Also check balance after purchase
                    balance_result = check_lotto_balance(username, password)
                    account_results.append(balance_result)

                    # Also check result after purchase
                    check_result = check_lotto_result(username, password)
                    account_results.append(check_result)

                elif action == 'check_balance':
                    result = check_lotto_balance(username, password)
                    account_results.append(result)

                elif action == 'check_result':
                    result = check_lotto_result(username, password)
                    account_results.append(result)

                else:
                    logger.error(f"Unknown action: {action}")
                    continue

                # Check for errors
                for result in account_results:
                    if result.get('status') == 'error':
                        errors.append(result.get('message'))

                all_results.extend(account_results)

            except Exception as e:
                error_msg = f"{username}: Error - {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)

        # Send notification
        if sns_topic_arn:
            if errors:
                send_notification(
                    sns_topic_arn,
                    "[Lotto Automation] Error",
                    "\n".join(errors)
                )
            else:
                # Success notification
                success_message = f"Action: {action}\n"
                success_message += f"Accounts processed: {len(credentials_list)}\n\n"
                for result in all_results:
                    success_message += f"- {result.get('username', 'Unknown')}: {result.get('status', 'Unknown')}\n"
                    if result.get('message'):
                        success_message += f"  {result.get('message')}\n"

                send_notification(
                    sns_topic_arn,
                    "[Lotto Automation] Success",
                    success_message
                )

        return {
            'statusCode': 200 if not errors else 500,
            'body': json.dumps({
                'action': action,
                'total_accounts': len(credentials_list),
                'results': all_results,
                'errors': errors
            })
        }

    except Exception as e:
        error_msg = f"Lambda execution failed: {str(e)}"
        logger.error(error_msg)

        if sns_topic_arn:
            send_notification(
                sns_topic_arn,
                "[Lotto Automation] Critical Error",
                error_msg
            )

        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }
