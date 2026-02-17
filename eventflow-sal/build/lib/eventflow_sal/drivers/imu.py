from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, imu_axis_event

class IMUSource(BaseSource):
    def __init__(self, d: str = "default", **_):
        super().__init__()
        self._d = d
    def metadata(self): return {"kind": "imu.6dof", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live source, so it yields nothing.
        return
        yield

class CSVFileSource(BaseSource):
    def __init__(self, p: str, **_):
        super().__init__()
        self._p = p
    def metadata(self): return {"kind": "imu.6dof", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        import csv
        with open(self._p) as f:
            for r in csv.DictReader(f):
                t = int(r["t_ns"])
                self._watermark_ns = t
                for i, k in enumerate(["ax", "ay", "az", "gx", "gy", "gz"]):
                    yield imu_axis_event(t, i, float(r[k]), u="m/s^2" if i < 3 else "rad/s")
