from __future__ import annotations

import json
import os
import secrets
import sqlite3
from pathlib import Path

from apps.api.core.crypto import decrypt_json, encrypt_json


def _replace_setting(lines: list[str], name: str, value: str) -> list[str]:
    prefix = f"{name}="
    replaced = False
    output: list[str] = []
    for line in lines:
        if line.startswith(prefix):
            output.append(f"{prefix}{value}")
            replaced = True
        else:
            output.append(line)
    if not replaced:
        output.append(f"{prefix}{value}")
    return output


def rotate(env_path: Path, database_path: Path) -> dict[str, bool]:
    original = env_path.read_text()
    settings = dict(
        line.split("=", 1)
        for line in original.splitlines()
        if line and not line.startswith("#") and "=" in line
    )
    old_admin_key = settings.get("ADMIN_API_KEY", "")
    if not old_admin_key:
        raise ValueError("ADMIN_API_KEY is missing from the environment file")

    new_admin_key = secrets.token_urlsafe(48)
    new_salt = secrets.token_urlsafe(48)
    lines = original.splitlines()
    lines = _replace_setting(lines, "ADMIN_API_KEY", new_admin_key)
    lines = _replace_setting(lines, "ANONYMIZATION_SALT", new_salt)
    replacement = "\n".join(lines) + "\n"
    temporary = env_path.with_name(f".{env_path.name}.rotation-{os.getpid()}")
    temporary.write_text(replacement)
    temporary.chmod(0o600)

    connection: sqlite3.Connection | None = None
    token_reencrypted = False
    try:
        if database_path.exists():
            connection = sqlite3.connect(database_path)
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT value FROM app_settings WHERE key = ?", ("credential:pinterest",)
            ).fetchone()
            if row:
                metadata = json.loads(row[0])
                encrypted = metadata.get("encrypted")
                if not isinstance(encrypted, str):
                    raise ValueError("Stored Pinterest credential is malformed")
                token = decrypt_json(encrypted, old_admin_key)
                metadata["encrypted"] = encrypt_json(token, new_admin_key)
                connection.execute(
                    "UPDATE app_settings SET value = ? WHERE key = ?",
                    (json.dumps(metadata), "credential:pinterest"),
                )
                token_reencrypted = True
        os.replace(temporary, env_path)
        env_path.chmod(0o600)
        if connection:
            connection.commit()
    except Exception:
        if connection:
            connection.rollback()
        env_path.write_text(original)
        env_path.chmod(0o600)
        raise
    finally:
        if connection:
            connection.close()
        temporary.unlink(missing_ok=True)
    return {"secrets_rotated": True, "pinterest_token_reencrypted": token_reencrypted}


if __name__ == "__main__":
    result = rotate(Path(".env"), Path("dealforge-local.db"))
    print(result)
