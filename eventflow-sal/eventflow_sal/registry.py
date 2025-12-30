from __future__ import annotations
from typing import Dict
from .api.uri import SensorURI
from .api.source import BaseSource
from .drivers.dvs import DVSSource, AEDAT4FileSource
from .drivers.audio import MicSource, WAVFileSource
from .drivers.imu import IMUSource, CSVFileSource
from .drivers.bio import ECGSource, EEGSource, EMGSource, CSVFileSource as BioCSVFileSource
from .drivers.environmental import EnvironmentalSource, EnvironmentalFileSource
from .drivers.fusion import FusionSource, FusionFileSource
from .drivers.city import TrafficCameraSource, NoiseSensorSource, PollutionSensorSource, CrowdSensorSource, InfrastructureSensorSource, CitySensorFileSource
from .drivers.scientific import SpectrometerSource, OscilloscopeSource, SensorSource, DataLoggerSource, SpectrometerFileSource, OscilloscopeFileSource, ScientificSensorFileSource
from .drivers.agriculture import SoilMoistureSource, SoilMoistureFileSource, SoilPhSource, SoilPhFileSource, NutrientSource, NutrientFileSource, WeatherSource, WeatherFileSource, CropSensorSource, CropSensorFileSource
from .drivers.tactile import TactileSource, TactileFileSource
from .drivers.security import MotionDetectorSource, MotionDetectorFileSource, CameraSource, CameraFileSource, PerimeterSensorSource, PerimeterSensorFileSource


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
        # WAV file → band stream
        if path.lower().endswith(".wav"):
            # Map overrides: b=bands, hop=ns (already provided by caller)
            b = int(overrides.get("b", 32))
            hop = int(overrides.get("hop", 10_000_000))  # default 10 ms in ns
            return WAVFileSource(path, b=b, hop=hop)
        # Device microphone (stub)
        return MicSource(device=path or "default", **overrides)

    if kind == "imu.6dof://":
        if path.lower().endswith(".csv"):
            return CSVFileSource(path, **overrides)
        return IMUSource(device=path or "default", **overrides)

    if kind == "bio.ecg://":
        if path.lower().endswith(".csv"):
            return BioCSVFileSource(path, signal_type="ecg", **overrides)
        return ECGSource(device=path or "default", **overrides)

    if kind == "bio.eeg://":
        if path.lower().endswith(".csv"):
            return BioCSVFileSource(path, signal_type="eeg", **overrides)
        return EEGSource(device=path or "default", **overrides)

    if kind == "bio.emg://":
        if path.lower().endswith(".csv"):
            return BioCSVFileSource(path, signal_type="emg", **overrides)
        return EMGSource(device=path or "default", **overrides)

    if kind == "env.sensor://":
        # Parse sensor type from query params, e.g. env.sensor://file?path=data.csv&sensor_type=gas
        sensor_type = params.get("sensor_type", "gas")
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return EnvironmentalFileSource(path, sensor_type=sensor_type, **overrides)
        return EnvironmentalSource(sensor_type=sensor_type, device=path or "default", **overrides)

    if kind == "fusion://":
        # Multi-modal fusion processing
        fusion_type = params.get("fusion_type", "kalman")
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return FusionFileSource(path, fusion_type=fusion_type, **overrides)
        return FusionSource(sources=[], fusion_type=fusion_type, **overrides)

    if kind == "city.traffic://":
        # Traffic camera sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return TrafficCameraSource(device=path or "default", **overrides)

    if kind == "city.noise://":
        # Noise pollution sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return NoiseSensorSource(device=path or "default", **overrides)

    if kind == "city.pollution://":
        # Air pollution sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return PollutionSensorSource(device=path or "default", **overrides)

    if kind == "city.crowd://":
        # Crowd density sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return CrowdSensorSource(device=path or "default", **overrides)

    if kind == "city.infrastructure://":
        # Infrastructure health sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        return InfrastructureSensorSource(device=path or "default", **overrides)

    if kind == "lab.spectrometer://":
        # Spectrometer instrument
        if path.lower().endswith((".csv", ".jsonl", ".json", ".spectrum")):
            return SpectrometerFileSource(path, **overrides)
        return SpectrometerSource(device=path or "default", **overrides)

    if kind == "lab.oscilloscope://":
        # Oscilloscope instrument
        if path.lower().endswith((".csv", ".jsonl", ".json", ".scope")):
            return OscilloscopeFileSource(path, **overrides)
        return OscilloscopeSource(device=path or "default", **overrides)

    if kind == "lab.sensor://":
        # Scientific sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return ScientificSensorFileSource(path, **overrides)
        return SensorSource(device=path or "default", **overrides)

    if kind == "lab.datalogger://":
        # Data logger instrument
        return DataLoggerSource(device=path or "default", **overrides)

    if kind == "agri.soil_moisture://":
        # Soil moisture sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return SoilMoistureFileSource(path, **overrides)
        return SoilMoistureSource(device=path or "default", **overrides)

    if kind == "agri.soil_ph://":
        # Soil pH sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return SoilPhFileSource(path, **overrides)
        return SoilPhSource(device=path or "default", **overrides)

    if kind == "agri.nutrient://":
        # Soil nutrient sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return NutrientFileSource(path, **overrides)
        return NutrientSource(device=path or "default", **overrides)

    if kind == "agri.weather://":
        # Weather station sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return WeatherFileSource(path, **overrides)
        return WeatherSource(device=path or "default", **overrides)

    if kind == "agri.crop_sensor://":
        # Crop monitoring sensor
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CropSensorFileSource(path, **overrides)
        return CropSensorSource(device=path or "default", **overrides)

    if kind == "tactile.array://":
        # Tactile sensor array
        return TactileFileSource(path, **overrides)

    if kind == "security.motion_detector://":
        # Motion detector sensor
        return MotionDetectorFileSource(path, **overrides)

    if kind == "security.camera://":
        # Security camera
        return CameraFileSource(path, **overrides)

    if kind == "security.perimeter_sensor://":
        # Perimeter security sensor
        return PerimeterSensorFileSource(path, **overrides)

    if kind == "file://":
        # Generic file scheme: route by extension (AEDAT4 for DVS, city files)
        if path.lower().endswith(".aedat4"):
            return AEDAT4FileSource(path, **overrides)
        if path.lower().endswith((".csv", ".jsonl", ".json")):
            return CitySensorFileSource(path, **overrides)
        raise ValueError(f"file:// scheme unsupported for path: {path!r}")

    raise ValueError(f"sal.unsupported_source: no driver for scheme {kind!r}")
