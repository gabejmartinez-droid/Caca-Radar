from google_identity import GoogleIdentityError, get_allowed_client_ids, verify_google_credential


def test_get_allowed_client_ids_deduplicates_values():
    assert get_allowed_client_ids("prod-id", "staging-id,prod-id,local-id") == [
        "prod-id",
        "staging-id",
        "local-id",
    ]


def test_verify_google_credential_rejects_audience_mismatch(monkeypatch):
    def fake_verify(*args, **kwargs):
        return {
            "iss": "https://accounts.google.com",
            "aud": "wrong-client",
            "sub": "google-sub-123",
            "email": "person@example.com",
            "email_verified": True,
        }

    monkeypatch.setattr("google_identity.id_token.verify_oauth2_token", fake_verify)

    try:
        verify_google_credential("token", ["expected-client"])
        raise AssertionError("Expected audience mismatch")
    except GoogleIdentityError as exc:
        assert exc.code == "google_audience_mismatch"


def test_verify_google_credential_returns_normalized_claims(monkeypatch):
    def fake_verify(*args, **kwargs):
        return {
            "iss": "accounts.google.com",
            "aud": "expected-client",
            "sub": "google-sub-123",
            "email": "Person@example.com",
            "email_verified": True,
            "name": "Person Example",
            "picture": "https://example.com/avatar.png",
        }

    monkeypatch.setattr("google_identity.id_token.verify_oauth2_token", fake_verify)

    claims = verify_google_credential("token", ["expected-client"])
    assert claims["sub"] == "google-sub-123"
    assert claims["email"] == "person@example.com"
    assert claims["name"] == "Person Example"
