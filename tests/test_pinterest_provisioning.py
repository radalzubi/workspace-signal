from __future__ import annotations

from unittest.mock import Mock

from apps.api.core.config import Settings
from apps.api.services.publishing import PinterestPublisher


def test_create_board_uses_public_privacy_and_bounded_fields() -> None:
    publisher = PinterestPublisher(Settings(_env_file=None), access_token="test-token")
    request = Mock()
    request.return_value.json.return_value = {"id": "board-123", "name": "Workspace Deals"}
    publisher._request = request  # type: ignore[method-assign]

    result = publisher.create_board("N" * 200, "D" * 600)

    assert result["id"] == "board-123"
    request.assert_called_once_with(
        "POST",
        "/boards",
        json={"name": "N" * 180, "description": "D" * 500, "privacy": "PUBLIC"},
    )
