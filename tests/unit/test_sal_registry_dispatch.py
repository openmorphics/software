from __future__ import annotations

from urllib.parse import parse_qs

import pytest

from eventflow_sal.api.uri import SensorURI, parse_sensor_uri
from eventflow_sal.registry import resolve_source


def _parse_uri_compat(uri: str) -> SensorURI:
    parsed = parse_sensor_uri(uri)
    # Python's URL parser rejects underscore in scheme; several SAL schemes use underscore.
    # Fall back to a lightweight parser for those legacy-but-supported scheme strings.
    if parsed.scheme != "://":
        return parsed

    if "://" not in uri:
        return parsed
    scheme_raw, rest = uri.split("://", 1)
    path_raw, _, query = rest.partition("?")
    params = {k: v[0] for k, v in parse_qs(query).items()}
    return SensorURI(f"{scheme_raw}://", path_raw, params)


@pytest.mark.parametrize(
    ("uri", "expected_cls"),
    [
        ("vision.dvs://camera0", "DVSSource"),
        ("vision.dvs://file?path=sample.aedat4", "AEDAT4FileSource"),
        ("imu.6dof://imu0", "IMUSource"),
        ("imu.6dof://file?path=imu.csv", "CSVFileSource"),
        ("bio.ecg://sensor0", "ECGSource"),
        ("bio.eeg://sensor0", "EEGSource"),
        ("bio.emg://sensor0", "EMGSource"),
        ("bio.ecg://file?path=bio.csv", "CSVFileSource"),
        ("env.sensor://file?path=env.json&sensor_type=gas", "EnvironmentalFileSource"),
        ("fusion://file?path=fusion.jsonl&fusion_type=kalman", "FusionFileSource"),
        ("city.traffic://cam1", "TrafficCameraSource"),
        ("city.pollution://file?path=pollution.csv", "CitySensorFileSource"),
        ("lab.spectrometer://file?path=trace.spectrum", "SpectrometerFileSource"),
        ("lab.oscilloscope://file?path=trace.scope", "OscilloscopeFileSource"),
        ("lab.sensor://file?path=sci.json", "ScientificSensorFileSource"),
        ("lab.datalogger://usb0", "DataLoggerSource"),
        ("agri.soil_moisture://file?path=soil.csv", "SoilMoistureFileSource"),
        ("agri.soil_ph://file?path=ph.csv", "SoilPhFileSource"),
        ("agri.nutrient://file?path=npk.csv", "NutrientFileSource"),
        ("agri.weather://file?path=weather.csv", "WeatherFileSource"),
        ("agri.crop_sensor://file?path=crop.csv", "CropSensorFileSource"),
        ("tactile.array://file?path=tactile.bin", "TactileFileSource"),
        ("security.motion_detector://file?path=motion.dat", "MotionDetectorFileSource"),
        ("security.camera://file?path=cam.dat", "CameraFileSource"),
        ("security.perimeter_sensor://file?path=perimeter.dat", "PerimeterSensorFileSource"),
        ("file://data/sample.aedat4", "AEDAT4FileSource"),
        ("file://data/sample.csv", "CitySensorFileSource"),
    ],
)
def test_resolve_source_dispatches_supported_schemes(uri: str, expected_cls: str) -> None:
    src = resolve_source(_parse_uri_compat(uri), overrides={})
    assert src.__class__.__name__ == expected_cls


def test_resolve_source_rejects_direct_jsonl_open_for_dvs() -> None:
    with pytest.raises(ValueError, match="JSONL normalization must use SAL stream_to_jsonl"):
        resolve_source(_parse_uri_compat("vision.dvs://file?path=trace.jsonl"), overrides={})


def test_resolve_source_rejects_unsupported_file_scheme_extension() -> None:
    with pytest.raises(ValueError, match="file:// scheme unsupported"):
        resolve_source(_parse_uri_compat("file://data/sample.bin"), overrides={})


def test_resolve_source_rejects_unknown_scheme() -> None:
    with pytest.raises(ValueError, match="sal.unsupported_source"):
        resolve_source(_parse_uri_compat("custom.unknown://source"), overrides={})
