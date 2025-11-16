"""
Unit tests for Slack signature verification.

This module tests the HMAC-SHA256 signature verification logic,
including replay attack prevention and timing attack resistance.

Reference:
    Slack Request Signing: https://api.slack.com/authentication/verifying-requests-from-slack
"""

import hashlib
import hmac
import inspect
import time


from slack_signature import verify_slack_signature


def test_valid_signature_returns_true():
    """Test valid signature verification."""
    timestamp = str(int(time.time()))
    body = '{"type":"event_callback"}'
    signing_secret = "test_secret"

    # Generate valid signature
    basestring = f"v0:{timestamp}:{body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    assert verify_slack_signature(body, timestamp, signature, signing_secret) is True


def test_invalid_signature_returns_false():
    """Test invalid signature returns False."""
    timestamp = str(int(time.time()))
    body = '{"type":"event_callback"}'
    signing_secret = "test_secret"

    # Use invalid signature
    invalid_signature = "v0=invalid_hash_value"

    assert (
        verify_slack_signature(body, timestamp, invalid_signature, signing_secret)
        is False
    )


def test_expired_timestamp_returns_false():
    """Test expired timestamp (>5 minutes) returns False."""
    old_timestamp = str(int(time.time()) - 600)  # 10 minutes ago
    body = '{"type":"event_callback"}'
    signing_secret = "test_secret"

    # Generate signature with old timestamp
    basestring = f"v0:{old_timestamp}:{body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    assert (
        verify_slack_signature(body, old_timestamp, signature, signing_secret) is False
    )


def test_timing_attack_resistance():
    """Test that compare_digest prevents timing attacks."""
    # This test ensures we use hmac.compare_digest()
    # Actual timing attack testing requires specialized tools
    source = inspect.getsource(verify_slack_signature)
    assert "hmac.compare_digest" in source


def test_different_body_invalid_signature():
    """Test that modifying body invalidates signature."""
    timestamp = str(int(time.time()))
    original_body = '{"type":"event_callback","event":{"text":"original"}}'
    tampered_body = '{"type":"event_callback","event":{"text":"tampered"}}'
    signing_secret = "test_secret"

    # Generate signature for original body
    basestring = f"v0:{timestamp}:{original_body}".encode("utf-8")
    signature = (
        "v0="
        + hmac.new(
            signing_secret.encode("utf-8"), basestring, hashlib.sha256
        ).hexdigest()
    )

    # Verify with tampered body should fail
    assert (
        verify_slack_signature(tampered_body, timestamp, signature, signing_secret)
        is False
    )
