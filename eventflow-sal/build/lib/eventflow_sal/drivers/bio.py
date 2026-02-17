from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, bio_signal_event

class ECGSource(BaseSource):
    def __init__(self, d: str = "default", **_):
        super().__init__()
        self._d = d
    def metadata(self): return {"kind": "bio.ecg", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live ECG source, so it yields nothing.
        return
        yield

class EEGSource(BaseSource):
    def __init__(self, d: str = "default", **_):
        super().__init__()
        self._d = d
    def metadata(self): return {"kind": "bio.eeg", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live EEG source, so it yields nothing.
        return
        yield

class EMGSource(BaseSource):
    def __init__(self, d: str = "default", **_):
        super().__init__()
        self._d = d
    def metadata(self): return {"kind": "bio.emg", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # This is a stub for a live EMG source, so it yields nothing.
        return
        yield

class CSVFileSource(BaseSource):
    def __init__(self, p: str, signal_type: str = "ecg", **_):
        super().__init__()
        self._p = p
        self._signal_type = signal_type  # 'ecg', 'eeg', or 'emg'
    def metadata(self): return {"kind": f"bio.{self._signal_type}", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        import csv
        with open(self._p) as f:
            reader = csv.DictReader(f)
            for r in reader:
                t = int(r["t_ns"])
                self._watermark_ns = t
                # Assume CSV has columns: t_ns, ch0, ch1, ch2, ... (channel data)
                for i, k in enumerate([col for col in r.keys() if col.startswith("ch")]):
                    if k in r:
                        value = float(r[k])
                        # Map units based on signal type
                        unit = {"ecg": "mV", "eeg": "uV", "emg": "mV"}.get(self._signal_type, "dimensionless")
                        yield bio_signal_event(t, i, value, u=unit)