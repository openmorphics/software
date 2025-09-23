from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any
from .packet import EventPacket

class BaseSource(ABC):
    def __init__(self):
        self._watermark_ns = -1

    @abstractmethod
    def metadata(self) -> Dict[str, Any]: ...
    @abstractmethod
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Yields event packets from the source. Implementers must ensure that
        the watermark is advanced with each yielded packet's timestamp.
        """
        ...

    def seek(self, t: int):
        """
        Optional: Seek the stream to a given timestamp (ns).
        If implemented, subsequent calls to subscribe() should yield events
        at or after the specified time.
        """
        raise NotImplementedError

    def watermark_ns(self) -> Optional[int]:
        """Returns the highest timestamp (ns) emitted by the source, or -1 if none."""
        return self._watermark_ns

class Replayable(BaseSource):
    @abstractmethod
    def set_seed(self, seed: int): ...
