"""
Slack request signature verification.

This module implements Slack's request signature verification using HMAC-SHA256.
It protects against replay attacks and timing attacks.

Reference:
    Slack Request Signing: https://api.slack.com/authentication/verifying-requests-from-slack
    AWS Security Best Practices: Use timing-attack-resistant comparison
"""

import hashlib
import hmac
import time


def verify_slack_signature(
    body: str, timestamp: str, signature: str, signing_secret: str
) -> bool:
    """
    Verify Slack request signature using HMAC-SHA256.

    Args:
        body: Raw request body (before JSON parsing)
        timestamp: x-slack-request-timestamp header value
        signature: x-slack-signature header value (format: v0=<hash>)
        signing_secret: Slack app signing secret from SSM

    Returns:
        bool: True if signature is valid and timestamp is fresh

    Security:
        - Uses hmac.compare_digest() to prevent timing attacks
        - Validates timestamp within 5-minute window (replay attack prevention)
        - Operates on raw body (not parsed JSON)

    Example:
        >>> body = '{"type":"url_verification","challenge":"test"}'
        >>> timestamp = str(int(time.time()))
        >>> secret = "8f742231b10e8888abcd99yyyzzz85a5"
        >>> # Generate signature
        >>> basestring = f'v0:{timestamp}:{body}'.encode('utf-8')
        >>> my_sig = 'v0=' + hmac.new(secret.encode('utf-8'),
        ...                           basestring, hashlib.sha256).hexdigest()
        >>> verify_slack_signature(body, timestamp, my_sig, secret)
        True
    """
    # 1. Validate timestamp (prevent replay attacks)
    # Reject requests older than 5 minutes
    current_time = int(time.time())
    request_time = int(timestamp)
    if abs(current_time - request_time) > 60 * 5:  # 5 minutes
        return False

    # 2. Compute expected signature
    # Format: v0:<timestamp>:<body>
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    expected_signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    # 3. Compare using timing-attack-safe function
    # hmac.compare_digest performs constant-time comparison
    # This prevents attackers from deducing the signature through timing analysis
    return hmac.compare_digest(expected_signature, signature)
