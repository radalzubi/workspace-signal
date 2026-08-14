from __future__ import annotations

import base64
import hashlib
import json
from typing import Any

from cryptography.fernet import Fernet


def _fernet(master_secret: str) -> Fernet:
    if len(master_secret) < 16:
        raise ValueError("ADMIN_API_KEY must be at least 16 characters before storing credentials")
    key = base64.urlsafe_b64encode(hashlib.sha256(master_secret.encode()).digest())
    return Fernet(key)


def encrypt_json(value: dict[str, Any], master_secret: str) -> str:
    return _fernet(master_secret).encrypt(json.dumps(value).encode()).decode()


def decrypt_json(value: str, master_secret: str) -> dict[str, Any]:
    decoded: object = json.loads(_fernet(master_secret).decrypt(value.encode()).decode())
    if not isinstance(decoded, dict):
        raise ValueError("Encrypted credential payload is not an object")
    return {str(key): item for key, item in decoded.items()}
