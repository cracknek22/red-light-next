from redlight_next.security.redaction import redact_secrets


def test_redacts_token_assignment():
    text = redact_secrets("token=abc123456789")
    assert "abc123456789" not in text
    assert "***REDACTED***" in text


def test_redacts_bearer_token():
    text = redact_secrets("Authorization: Bearer abcdefghijklmnopqrstuvwxyz")
    assert "abcdefghijklmnopqrstuvwxyz" not in text


def test_redacts_github_token_shape():
    text = redact_secrets("ghp_abcdefghijklmnopqrstuvwxyz1234567890")
    assert "ghp_" not in text
