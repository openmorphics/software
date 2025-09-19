from __future__ import annotations

class TokenProvider:
    def __init__(self, token: str | None = None):
        self._token = token
    def get(self) -> str | None:
        return self._token
