from __future__ import annotations
from typing import Dict
from .api.uri import SensorURI
from .api.source import BaseSource


def _effective_path(u: SensorURI) -> str:
    """
    Use query param ?path= if provided (compat with URIs like audio.mic://file?path=...),
    otherwise fall back to netloc+path parsed into SensorURI.path.
    """
    params = getattr(u, "params", {}) or {}
    return params.get("path") or u.path


def resolve_source(u: SensorURI, overrides: dict) -> BaseSource:
    """
    Registry dispatcher that supports both device URIs and file-based URIs
    with ?path= compatibility across schemes.
    """
    kind = u.scheme
    path = _effective_path(u) or ""
    params = getattr(u, "params", {}) or {}

    if kind == "vision.dvs://":
        from .drivers.dvs import DVSSource, AEDAT4FileSource

        # File-based DVS recording
        if path.lower().endswith(".aedat4"):
            return AEDAT4FileSource(path, **overrides)
        # JSONL is handled by SAL stream normalization path (api.stream_to_jsonl passthrough),
        # but if someone calls open() directly with a JSONL we fail fast:
        if path.lower().endswith(".jsonl"):
            raise ValueError("sal.unsupported_source: JSONL normalization must use SAL stream_to_jsonl(), not open()")
        # Device-based DVS (live camera or stub)
        return DVSSource(device=path or "default", **overrides)

    if kind == "audio.mic://":
        from .drivers.audio import MicSource, WAVFileSource

        # WAV file → band stream
        if path.lower().endswith(".wav"):
            # Map overrides: b=bands, hop=ns (already provided by caller)
            b = int(overrides.get("b", 32))
            hop = int(overrides.get("hop", 10_000_000))  # default 10 ms in ns
            return WAVFileSource(path, b=b, hop=hop)
        # Device microphone (stub)
        return MicSource(device=path or "default", **overrides)

    if kind == "imu.6dof://":
        from .drivers.imu import IMUSource, CSVFileSource

        if path.lower().endswith(".csv"):
            return CSVFileSource(path, **overrides)
        return IMUSource(device=path or "default", **overrides)

    if kind == "bio.ecg://":
        from .drivers.bio import ECGSource, CSVFileSource as BioCSVFileSource

        if path.lower().endswith(".csv"):
            return BioCSVFileSource(path, signal_type="ecg", **overrides)
        return ECGSource(device=path or "default", **overrides)

    if kind == "bio.eeg://":
        from .drivers.bio import EEGSource, CSVFileSource as BioCSVFileSource

        if path.lower().endswith(".csv"):
            return BioCSVFileSource(path, signal_type="eeg", **overrides)
        return EEGSource(device=path or "default", **overrides)

    if kind == "bio.emg://":
        from .drivers.bio import EMGSource, CSVFileSource as BioCSVFileSource

        if path.lower().endswith(".csv"):
            return BioCSVFileSource(path, signal_type="emg", **overrides)
        return EMGSource(device=path or "default", **overrides)

    if kind == "env.sensor://":
        from .drivers.environmental import EnvironmentalSource, EnvironmentalFileSource

        # Parse sensor type from query params, e.g. env.sensor://file?path=data.csv&sensor_type=gas
        sensor_type = params.get("sensor_type", "gas")
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return EnvironmentalFileSource(path, sensor_type=sensor_type, **overrides)
        return EnvironmentalSource(sensor_type=sensor_type, device=path or "default", **overrides)

    if kind == "fusion://":
        from .drivers.fusion import FusionSource, FusionFileSource

        # Multi-modal fusion processing
        fusion_type = params.get("fusion_type", "kalman")
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return FusionFileSource(path, fusion_type=fusion_type, **overrides)
        return FusionSource(sources=[], fusion_type=fusion_type, **overrides)

    if kind == "city.traffic://":
        from .drivers.city import TrafficCameraSource, CitySensorFileSource

        # Traffic camera sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return TrafficCameraSource(device=path or "default", **overrides)

    if kind == "city.noise://":
        from .drivers.city import NoiseSensorSource, CitySensorFileSource

        # Noise pollution sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return NoiseSensorSource(device=path or "default", **overrides)

    if kind == "city.pollution://":
        from .drivers.city import PollutionSensorSource, CitySensorFileSource

        # Air pollution sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return PollutionSensorSource(device=path or "default", **overrides)

    if kind == "city.crowd://":
        from .drivers.city import CrowdSensorSource, CitySensorFileSource

        # Crowd density sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return CrowdSensorSource(device=path or "default", **overrides)

    if kind == "city.infrastructure://":
        from .drivers.city import InfrastructureSensorSource, CitySensorFileSource

        # Infrastructure health sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return InfrastructureSensorSource(device=path or "default", **overrides)

    if kind == "lab.spectrometer://":
        from .drivers.scientific import SpectrometerSource, SpectrometerFileSource

        # Spectrometer instrument
        if path.lower().endswith((".csv", ".jsonl", ".json", ".spectrum")):
            return SpectrometerFileSource(path, **overrides)
        return SpectrometerSource(device=path or "default", **overrides)

    if kind == "lab.oscilloscope://":
        from .drivers.scientific import OscilloscopeSource, OscilloscopeFileSource

        # Oscilloscope instrument
        if path.lower().endswith((".csv", ".jsonl", ".json", ".scope")):
            return OscilloscopeFileSource(path, **overrides)
        return OscilloscopeSource(device=path or "default", **overrides)

    if kind == "lab.sensor://":
        from .drivers.scientific import SensorSource, ScientificSensorFileSource

        # Scientific sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return ScientificSensorFileSource(path, **overrides)
        return SensorSource(device=path or "default", **overrides)

    if kind == "lab.datalogger://":
        from .drivers.scientific import DataLoggerSource

        # Data logger instrument
        return DataLoggerSource(device=path or "default", **overrides)

    if kind == "agri.soil_moisture://":
        from .drivers.agriculture import SoilMoistureSource, SoilMoistureFileSource

        # Soil moisture sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return SoilMoistureFileSource(path, **overrides)
        return SoilMoistureSource(device=path or "default", **overrides)

    if kind == "agri.soil_ph://":
        from .drivers.agriculture import SoilPhSource, SoilPhFileSource

        # Soil pH sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return SoilPhFileSource(path, **overrides)
        return SoilPhSource(device=path or "default", **overrides)

    if kind == "agri.nutrient://":
        from .drivers.agriculture import NutrientSource, NutrientFileSource

        # Soil nutrient sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return NutrientFileSource(path, **overrides)
        return NutrientSource(device=path or "default", **overrides)

    if kind == "agri.weather://":
        from .drivers.agriculture import WeatherSource, WeatherFileSource

        # Weather station sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return WeatherFileSource(path, **overrides)
        return WeatherSource(device=path or "default", **overrides)

    if kind == "agri.crop_sensor://":
        from .drivers.agriculture import CropSensorSource, CropSensorFileSource

        # Crop monitoring sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CropSensorFileSource(path, **overrides)
        return CropSensorSource(device=path or "default", **overrides)

    if kind == "tactile.array://":
        from .drivers.tactile import TactileFileSource

        # Tactile sensor array
        return TactileFileSource(path, **overrides)

    if kind == "security.motion_detector://":
        from .drivers.security import MotionDetectorFileSource

        # Motion detector sensor
        return MotionDetectorFileSource(path, **overrides)

    if kind == "security.camera://":
        from .drivers.security import CameraFileSource

        # Security camera
        return CameraFileSource(path, **overrides)

    if kind == "security.perimeter_sensor://":
        from .drivers.security import PerimeterSensorFileSource

        # Perimeter security sensor
        return PerimeterSensorFileSource(path, **overrides)

    if kind == "file://":
        from .drivers.dvs import AEDAT4FileSource
        from .drivers.city import CitySensorFileSource

        # Generic file scheme: route by extension (AEDAT4 for DVS, city files)
        if path.lower().endswith(".aedat4"):
            return AEDAT4FileSource(path, **overrides)
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        raise ValueError(f"file:// scheme unsupported for path: {path!r}")

    raise ValueError(f"sal.unsupported_source: no driver for scheme {kind!r}")
