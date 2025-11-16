"""
Lambda Function URL handler for Slack Events API.

This module implements the main Lambda handler for processing Slack Events API requests.
It verifies Slack signatures, handles URL verification, and invokes AgentCore Runtime.

Environment Variables:
    AGENTCORE_RUNTIME_ARN: ARN of the AgentCore Runtime to invoke
    LOG_LEVEL: CloudWatch Logs level (default: INFO)

Reference:
    AWS Well-Architected Framework - Security Pillar
    Slack Events API: https://api.slack.com/apis/connections/events-api
"""

import base64
import json
import logging
import os
import re
from typing import Any

from agentcore_client import AgentCoreClient
from slack_signature import verify_slack_signature
from ssm_client import SSMParameterStore

# Configure logger
logger = logging.getLogger()
log_level = os.environ.get("LOG_LEVEL", "INFO")
logger.setLevel(getattr(logging, log_level, logging.INFO))


def mask_sensitive_data(text: str) -> str:
    """
    Mask tokens and signatures in logs.

    Args:
        text: Log text that may contain sensitive data

    Returns:
        str: Text with sensitive data masked

    Security:
        - Masks Slack Bot Tokens (xoxb-*)
        - Masks Slack signatures (v0=<hash>)
        - Prevents credential leakage in CloudWatch Logs
    """
    text = re.sub(r"(xoxb-[a-zA-Z0-9-]+)", "xoxb-***MASKED***", text)
    text = re.sub(r"(v0=[a-f0-9]+)", "v0=***MASKED***", text)
    return text


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda Function URL handler for Slack Events API.

    Args:
        event: Lambda event with keys:
            - body: str (JSON string or Base64 encoded)
            - headers: dict (x-slack-signature, x-slack-request-timestamp)
            - isBase64Encoded: bool
        context: Lambda context object

    Returns:
        dict with keys:
            - statusCode: int (200, 401, 500)
            - body: str (JSON string)

    Raises:
        ValueError: Invalid timestamp or signature
        SlackApiError: Slack API call failed

    Security:
        - Verifies Slack request signatures using HMAC-SHA256
        - Validates timestamp to prevent replay attacks (5-minute window)
        - Masks sensitive data in CloudWatch Logs
    """
    try:
        # 1. Extract headers
        headers = event.get("headers", {})
        signature = headers.get("x-slack-signature")
        timestamp = headers.get("x-slack-request-timestamp")

        if not signature or not timestamp:
            logger.error(
                "Missing required headers (x-slack-signature or x-slack-request-timestamp)"
            )
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required headers"}),
            }

        # 2. Get raw body
        body = event.get("body", "")
        if event.get("isBase64Encoded", False):
            body = base64.b64decode(body).decode("utf-8")

        # 3. Verify signature
        ssm = SSMParameterStore()
        signing_secret = ssm.get_parameter("/slack-issue-agent/slack/signing-secret")

        if not verify_slack_signature(body, timestamp, signature, signing_secret):
            logger.warning(f"Signature verification failed for timestamp: {timestamp}")
            return {
                "statusCode": 401,
                "body": json.dumps({"error": "Invalid signature"}),
            }

        # 4. Parse payload
        payload = json.loads(body)

        # 5. Handle URL verification
        if payload.get("type") == "url_verification":
            logger.info("Handling URL verification")
            return {
                "statusCode": 200,
                "body": json.dumps({"challenge": payload["challenge"]}),
            }

        # 6. Invoke AgentCore
        agent_arn = os.environ["AGENTCORE_RUNTIME_ARN"]
        client = AgentCoreClient(agent_arn)

        event_text = payload["event"]["text"]
        result = client.invoke(prompt=event_text)

        logger.info(f"AgentCore response: {mask_sensitive_data(result['result'])}")

        # 7. Return acknowledgment (Slack requires 200 within 3 seconds)
        return {"statusCode": 200, "body": json.dumps({"ok": True})}

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid JSON payload"}),
        }

    except KeyError as e:
        logger.error(f"Missing required field in payload: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Missing required field: {e}"}),
        }

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Internal server error"}),
        }
