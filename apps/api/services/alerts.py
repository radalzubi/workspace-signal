from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import structlog

logger = structlog.get_logger()


class AlertProvider(ABC):
    @abstractmethod
    def send(self, event: str, severity: str, context: dict[str, Any]) -> None:
        raise NotImplementedError


class LogAlertProvider(AlertProvider):
    def send(self, event: str, severity: str, context: dict[str, Any]) -> None:
        logger.warning("operational_alert", event=event, severity=severity, **context)


def alert(event: str, severity: str = "warning", **context: Any) -> None:
    LogAlertProvider().send(event, severity, context)
