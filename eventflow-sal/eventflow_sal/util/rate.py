from __future__ import annotations
class RateLimiter:
    def __init__(self, keps: int | None = None):
        self.keps = keps
