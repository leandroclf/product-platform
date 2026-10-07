from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PortfolioContext:
    content: str
    fingerprint: str
    source: str

    @classmethod
    def from_file(cls, path: Path) -> PortfolioContext:
        data = path.read_bytes()
        if len(data) > 256_000:
            raise ValueError("portfolio context exceeds 256KB")
        text = data.decode("utf-8")
        if not text.strip():
            raise ValueError("portfolio context is empty")
        return cls(text, hashlib.sha256(data).hexdigest(), str(path))

    def prompt_text(self) -> str:
        return f"source={self.source}; sha256={self.fingerprint}\n{self.content}"
