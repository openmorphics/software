from typing import Iterator
from ..api.source import BaseSource
from ..api.packet import EventPacket, generic_event
from ..sync.clock import ClockSync, ClockModel

class SpectrometerSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.spectrometer", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # Stub for spectrometer data source
        return
        yield

class OscilloscopeSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.oscilloscope", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # Stub for oscilloscope data source
        return
        yield

class SensorSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.sensor", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # Stub for scientific sensor data source
        return
        yield

class DataLoggerSource(BaseSource):
    def __init__(self, d: str = "default", c: "ClockSync|None" = None, **_):
        super().__init__()
        self._d, self._c = d, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.datalogger", "device": self._d}
    def subscribe(self) -> Iterator[EventPacket]:
        # Stub for data logger source
        return
        yield

class SpectrometerFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.spectrometer", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic spectrometer data replay for testing and examples.

        Generates simulated spectral data with wavelength-intensity pairs
        for spectroscopy research demonstrations.
        """
        count = 1000
        t0_ns = 0
        dt_ns = 100_000_000  # 100ms between spectra

        # Simulate spectrometer wavelength range (200-1100 nm)
        wavelengths = list(range(200, 1101, 5))  # 5nm resolution

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            # Simulate spectral peaks (multiple gaussian peaks)
            spectrum = []
            for wl in wavelengths:
                # Add baseline noise (simplified without numpy)
                import random
                intensity = 100 + random.gauss(0, 5)

                # Add spectral peaks
                if 400 <= wl <= 450:  # UV peak
                    intensity += 500 * (2.71828 ** -((wl - 425) / 15) ** 2)  # exp approximation
                if 550 <= wl <= 600:  # Visible peak
                    intensity += 800 * (2.71828 ** -((wl - 575) / 20) ** 2)
                if 700 <= wl <= 750:  # NIR peak
                    intensity += 300 * (2.71828 ** -((wl - 725) / 25) ** 2)

                spectrum.append(intensity)

            # Create spectrum event (wavelength, intensity pairs)
            spectrum_data = {"wavelengths": wavelengths, "intensities": spectrum}
            pkt = generic_event(ts_ns, spectrum_data)
            self._watermark_ns = ts_ns
            yield pkt

class OscilloscopeFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.oscilloscope", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic oscilloscope data replay for testing and examples.

        Generates simulated multi-channel oscilloscope data with various
        signal types for electrical engineering demonstrations.
        """
        import numpy as np

        count = 500
        t0_ns = 0
        dt_ns = 1_000_000  # 1ms between acquisitions

        # Simulate 4-channel oscilloscope
        channels = 4
        sample_rate = 1_000_000  # 1 MS/s
        samples_per_acquisition = 1000

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)
            t_axis = np.linspace(0, samples_per_acquisition / sample_rate, samples_per_acquisition)

            channel_data = {}
            for ch in range(1, channels + 1):
                if ch == 1:
                    # Sine wave
                    signal = 2.0 * np.sin(2 * np.pi * 1000 * t_axis)  # 1kHz sine
                elif ch == 2:
                    # Square wave
                    signal = 3.0 * np.sign(np.sin(2 * np.pi * 500 * t_axis))  # 500Hz square
                elif ch == 3:
                    # Triangle wave
                    signal = 1.5 * (2 * np.abs((t_axis * 2000) % 2 - 1) - 1)  # 2kHz triangle
                else:  # ch == 4
                    # Noise + signal
                    signal = 0.5 * np.sin(2 * np.pi * 2000 * t_axis) + 0.2 * np.random.normal(0, 1, len(t_axis))

                channel_data[f"ch{ch}"] = signal.tolist()

            # Add timing information
            channel_data["time_axis"] = t_axis.tolist()
            channel_data["sample_rate"] = sample_rate

            pkt = generic_event(ts_ns, channel_data)
            self._watermark_ns = ts_ns
            yield pkt

class ScientificSensorFileSource(BaseSource):
    def __init__(self, p: str, c: "ClockSync|None" = None, **_):
        super().__init__()
        self._p, self._c = p, c or ClockSync(ClockModel())
    def metadata(self): return {"kind": "scientific.sensor", "file": self._p}
    def subscribe(self) -> Iterator[EventPacket]:
        """
        Synthetic scientific sensor data replay for testing and examples.

        Generates simulated sensor readings for various scientific measurement
        types including temperature, pressure, flow, and other research parameters.
        """
        import numpy as np

        count = 2000
        t0_ns = 0
        dt_ns = 500_000_000  # 500ms between readings

        sensor_types = ["temperature", "pressure", "flow_rate", "ph", "conductivity"]

        for i in range(count):
            ts_ns = self._c.correct_ns(t0_ns + i * dt_ns)

            sensor_readings = {}
            for sensor_type in sensor_types:
                if sensor_type == "temperature":
                    # Temperature variation around 25°C
                    base_temp = 25.0
                    variation = 2.0 * np.sin(2 * np.pi * i / 100)  # Slow temperature drift
                    noise = np.random.normal(0, 0.1)
                    value = base_temp + variation + noise
                    unit = "celsius"
                elif sensor_type == "pressure":
                    # Pressure around 1 atm with small variations
                    base_pressure = 101325  # Pa
                    variation = 1000 * np.sin(2 * np.pi * i / 50)  # Pressure fluctuations
                    noise = np.random.normal(0, 50)
                    value = base_pressure + variation + noise
                    unit = "pascal"
                elif sensor_type == "flow_rate":
                    # Flow rate around 10 mL/min
                    base_flow = 10.0
                    variation = 2.0 * np.cos(2 * np.pi * i / 75)
                    noise = np.random.normal(0, 0.2)
                    value = base_flow + variation + noise
                    unit = "ml_per_min"
                elif sensor_type == "ph":
                    # pH around 7 with small variations
                    base_ph = 7.0
                    variation = 0.5 * np.sin(2 * np.pi * i / 200)
                    noise = np.random.normal(0, 0.02)
                    value = base_ph + variation + noise
                    unit = "ph"
                else:  # conductivity
                    # Conductivity around 1000 μS/cm
                    base_cond = 1000.0
                    variation = 200 * np.sin(2 * np.pi * i / 150)
                    noise = np.random.normal(0, 10)
                    value = base_cond + variation + noise
                    unit = "microsiemens_per_cm"

                sensor_readings[sensor_type] = {
                    "value": float(value),
                    "unit": unit,
                    "timestamp": ts_ns
                }

            pkt = generic_event(ts_ns, sensor_readings)
            self._watermark_ns = ts_ns
            yield pkt
