from __future__ import annotations
class RingBuffer:
    def __init__(self, capacity: int):
        self._buf = [None] * capacity
        self._cap = capacity
        self._r = 0
        self._w = 0
