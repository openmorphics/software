from abc import ABC,abstractmethod; from typing import Iterable; from ..api.packet import EventPacket
class CalibrationStage(ABC):
    @abstractmethod
    def apply(self, p:Iterable[EventPacket]): ...
