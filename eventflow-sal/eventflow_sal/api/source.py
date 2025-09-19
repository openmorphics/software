from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any
from .packet import EventPacket

class BaseSource(ABC):
    @abstractmethod
    def metadata(self) -> Dict[str, Any]: ...
    @abstractmethod
    def subscribe(self) -> Iterator[EventPacket]: ...
    def seek(self,t:int): raise NotImplementedError
    def watermark_ns(self)->Optional[int]: return None

class Replayable(BaseSource):
    @abstractmethod
    def set_seed(self, seed: int): ...
