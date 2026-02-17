from __future__ import annotations

import csv
from pathlib import Path

import pytest

from eventflow_sal.drivers.agriculture import (
    CropSensorFileSource,
    NutrientFileSource,
    SoilMoistureFileSource,
    SoilPhFileSource,
    WeatherFileSource,
)
from eventflow_sal.drivers.bio import CSVFileSource as BioCSVFileSource
from eventflow_sal.drivers.bio import ECGSource, EEGSource, EMGSource
from eventflow_sal.drivers.city import (
    CitySensorFileSource,
    CrowdSensorSource,
    InfrastructureSensorSource,
    NoiseSensorSource,
    PollutionSensorSource,
    TrafficCameraSource,
)
from eventflow_sal.drivers.dvs import AEDAT4FileSource, DVSSource
from eventflow_sal.drivers.environmental import EnvironmentalFileSource
from eventflow_sal.drivers.fusion import FusionFileSource, FusionSource
from eventflow_sal.drivers.imu import CSVFileSource as IMUCSVFileSource
from eventflow_sal.drivers.imu import IMUSource
from eventflow_sal.drivers.scientific import (
    DataLoggerSource,
    OscilloscopeFileSource,
    OscilloscopeSource,
    ScientificSensorFileSource,
    SensorSource,
    SpectrometerFileSource,
    SpectrometerSource,
)
from eventflow_sal.drivers.security import (
    CameraFileSource,
    MotionDetectorFileSource,
    PerimeterSensorFileSource,
)
from eventflow_sal.drivers.tactile import TactileFileSource


def _first_event(source):
    it = source.subscribe()
    try:
        return next(it)
    except StopIteration:
        return None


def test_stub_sources_return_no_events() -> None:
    stubs = [
        DVSSource(),
        IMUSource(),
        ECGSource(),
        EEGSource(),
        EMGSource(),
        TrafficCameraSource(),
        NoiseSensorSource(),
        PollutionSensorSource(),
        CrowdSensorSource(),
        InfrastructureSensorSource(),
        SpectrometerSource(),
        OscilloscopeSource(),
        SensorSource(),
        DataLoggerSource(),
    ]
    for src in stubs:
        assert _first_event(src) is None


def test_synthetic_file_sources_emit_events() -> None:
    file_sources = [
        AEDAT4FileSource("dummy.aedat4"),
        EnvironmentalFileSource("dummy.json", sensor_type="gas"),
        FusionSource(sources=["vision", "audio"], fusion_type="kalman"),
        FusionFileSource("dummy.json"),
        CitySensorFileSource("traffic.csv"),
        SpectrometerFileSource("dummy.spectrum"),
        OscilloscopeFileSource("dummy.scope"),
        ScientificSensorFileSource("dummy.csv"),
        SoilMoistureFileSource("soil.csv"),
        SoilPhFileSource("soil_ph.csv"),
        NutrientFileSource("npk.csv"),
        WeatherFileSource("weather.csv"),
        CropSensorFileSource("crop.csv"),
        TactileFileSource("tactile.bin"),
        MotionDetectorFileSource("motion.log"),
        CameraFileSource("camera.log"),
        PerimeterSensorFileSource("perimeter.log"),
    ]

    for src in file_sources:
        pkt = _first_event(src)
        assert pkt is not None
        assert isinstance(pkt.t_ns, int)
        assert src.watermark_ns() >= 0


def test_csv_file_sources_emit_events(tmp_path: Path) -> None:
    imu_csv = tmp_path / "imu.csv"
    with imu_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["t_ns", "ax", "ay", "az", "gx", "gy", "gz"])
        writer.writeheader()
        writer.writerow({"t_ns": 1000, "ax": 1.0, "ay": 2.0, "az": 3.0, "gx": 0.1, "gy": 0.2, "gz": 0.3})

    imu_src = IMUCSVFileSource(str(imu_csv))
    imu_pkt = _first_event(imu_src)
    assert imu_pkt is not None
    assert imu_pkt.t_ns == 1000

    bio_csv = tmp_path / "bio.csv"
    with bio_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["t_ns", "ch0", "ch1"])
        writer.writeheader()
        writer.writerow({"t_ns": 2000, "ch0": 0.5, "ch1": 0.9})

    bio_src = BioCSVFileSource(str(bio_csv), signal_type="ecg")
    bio_pkt = _first_event(bio_src)
    assert bio_pkt is not None
    assert bio_pkt.t_ns == 2000
    assert bio_pkt.meta["unit"] in ("mV", "uV", "dimensionless")


def test_audio_driver_optional_dependency_smoke(tmp_path: Path) -> None:
    try:
        import scipy  # noqa: F401
    except Exception:
        pytest.skip("audio driver requires scipy")

    import wave
    import numpy as np
    from eventflow_sal.drivers.audio import WAVFileSource

    wav_path = tmp_path / "audio.wav"
    samples = (np.sin(np.linspace(0, 2 * np.pi, 800)).astype(np.float32) * 32767).astype(np.int16)
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(samples.tobytes())

    src = WAVFileSource(str(wav_path), b=8)
    pkt = _first_event(src)
    assert pkt is not None
