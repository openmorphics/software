from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, soil_moisture_event, soil_ph_event, nutrient_event, weather_event, crop_sensor_event
from ..sync.clock import ClockSync, ClockModel

class SoilMoistureSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.soil_moisture", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        return
        yield

class SoilMoistureFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.soil_moisture", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic soil moisture sensor file replay stub.

        For testing and examples, emit synthetic soil moisture events.
        """
        count = 200
        t0_ns = 0
        dt_ns = 10_000_000  # 10ms between events

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            depth_cm = (i % 5) * 10 + 10  # depths: 10, 20, 30, 40, 50 cm
            moisture = 20.0 + (i % 20) * 2.0  # 20-58% moisture

            pkt = soil_moisture_event(ts_ns, depth_cm, moisture)
            self._watermark_ns = ts_ns
            yield pkt

class SoilPhSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.soil_ph", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        return
        yield

class SoilPhFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.soil_ph", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic soil pH sensor file replay stub.
        """
        count = 50
        t0_ns = 0
        dt_ns = 60_000_000_000  # 1 minute between events

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            depth_cm = (i % 3) * 15 + 15  # depths: 15, 30, 45 cm
            ph = 6.0 + (i % 3) * 0.5  # pH range 6.0-7.5

            pkt = soil_ph_event(ts_ns, depth_cm, ph)
            self._watermark_ns = ts_ns
            yield pkt

class NutrientSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.nutrient", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        return
        yield

class NutrientFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.nutrient", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic nutrient sensor file replay stub.
        """
        count = 30
        t0_ns = 0
        dt_ns = 86_400_000_000_000  # 1 day between events

        nutrients = ['N', 'P', 'K']
        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            nutrient_type = nutrients[i % 3]
            concentration = 10.0 + (i % 10) * 5.0  # 10-55 ppm

            pkt = nutrient_event(ts_ns, nutrient_type, concentration)
            self._watermark_ns = ts_ns
            yield pkt

class WeatherSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.weather", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        return
        yield

class WeatherFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.weather", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic weather station file replay stub.
        """
        count = 100
        t0_ns = 0
        dt_ns = 3_600_000_000_000  # 1 hour between events

        sensor_types = ['temperature', 'humidity', 'wind_speed', 'precipitation']
        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            sensor_type = sensor_types[i % 4]
            if sensor_type == 'temperature':
                value = 15.0 + (i % 20) * 2.0  # 15-53°C
            elif sensor_type == 'humidity':
                value = 30.0 + (i % 40)  # 30-69%
            elif sensor_type == 'wind_speed':
                value = (i % 15) * 1.0  # 0-14 m/s
            else:  # precipitation
                value = (i % 10) * 0.5  # 0-4.5 mm

            pkt = weather_event(ts_ns, sensor_type, value)
            self._watermark_ns = ts_ns
            yield pkt

class CropSensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.crop_sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        return
        yield

class CropSensorFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "agriculture.crop_sensor", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic crop sensor file replay stub.
        """
        count = 500
        t0_ns = 0
        dt_ns = 86_400_000_000_000 // 24  # 1 hour between events (24 per day)

        width, height = 10, 10  # 10x10 crop field grid
        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            x = i % width
            y = (i // width) % height
            measurement = 0.5 + (i % 50) * 0.01  # NDVI-like values 0.5-0.99

            pkt = crop_sensor_event(ts_ns, x, y, measurement)
            self._watermark_ns = ts_ns
            yield pkt