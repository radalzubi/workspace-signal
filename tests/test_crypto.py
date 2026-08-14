from apps.api.core.crypto import decrypt_json, encrypt_json


def test_oauth_credentials_are_encrypted_at_rest() -> None:
    secret = "a-secure-test-master-key"
    payload = {"access_token": "pina_sensitive", "refresh_token": "pinr_sensitive"}
    encrypted = encrypt_json(payload, secret)
    assert "pina_sensitive" not in encrypted
    assert decrypt_json(encrypted, secret) == payload
