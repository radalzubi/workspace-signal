from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class TextToSpeechProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, cache_key: str) -> tuple[Path | None, float]:
        raise NotImplementedError


class DisabledTextToSpeechProvider(TextToSpeechProvider):
    def synthesize(self, text: str, cache_key: str) -> tuple[Path | None, float]:
        return None, 0.0
