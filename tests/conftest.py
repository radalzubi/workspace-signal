from __future__ import annotations

import os
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

os.environ.setdefault("DEMO_MODE", "true")
os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("AUTO_PUBLISH", "false")
os.environ.setdefault("ADMIN_API_KEY", "test-admin-token")
os.environ["MEDIA_ROOT"] = "media/test-generated"

from apps.api.db import models  # noqa: E402,F401
from apps.api.db.session import Base  # noqa: E402


@pytest.fixture
def db(tmp_path: Path) -> Session:
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection: object, _: object) -> None:
        cursor = connection.cursor()  # type: ignore[attr-defined]
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    Base.metadata.drop_all(engine)
